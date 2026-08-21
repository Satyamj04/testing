"""
Repeater API - modify and replay HTTP requests with scope enforcement.
"""
import time
from uuid import UUID
from typing import Optional

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.storage import storage_client
from app.core.config import settings
from app.core.security import mask_sensitive_headers
from app.models.http_traffic import HTTPRequest, Replay
from app.models.project import Target, Project
from app.models.user import User
from app.schemas.schemas import ReplayCreate, ReplayResponse
from app.api.v1.deps import get_current_user
from app.services.scope_validator import ScopeValidator, ScopeViolationError

router = APIRouter(prefix="/repeater", tags=["Repeater"])
logger = structlog.get_logger(__name__)


@router.post("", response_model=ReplayResponse, status_code=201)
async def create_and_execute_replay(
    payload: ReplayCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a replay with modifications and execute it.
    The request MUST pass ScopeValidator before sending.
    """
    # Load original request
    result = await db.execute(
        select(HTTPRequest)
        .join(Target, HTTPRequest.target_id == Target.id)
        .join(Project, Target.project_id == Project.id)
        .where(HTTPRequest.id == payload.original_request_id, Project.owner_id == current_user.id)
    )
    original = result.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=404, detail="Original request not found")

    effective_url = payload.modified_url or original.url
    effective_method = payload.modified_method or original.method
    effective_headers = payload.modified_headers or original.request_headers or {}

    # ── Scope enforcement ────────────────────────────────────────────────────
    validator = ScopeValidator(db)
    try:
        await validator.enforce(
            url=effective_url,
            method=effective_method,
            target_id=str(original.target_id),
            user_id=str(current_user.id),
            action="repeater_replay",
        )
    except ScopeViolationError as e:
        raise HTTPException(status_code=403, detail=f"Scope violation: {e.reason}")

    # Build body
    body_bytes: Optional[bytes] = None
    if payload.modified_body:
        body_bytes = payload.modified_body.encode()
    elif original.request_body_storage_key:
        bucket, obj = original.request_body_storage_key.split("/", 1)
        body_bytes = storage_client.get_object(bucket, obj)

    # Clean headers (remove host/content-length)
    send_headers = {k: v for k, v in effective_headers.items()
                    if k.lower() not in ("host", "content-length", "transfer-encoding")}

    # ── Execute ───────────────────────────────────────────────────────────────
    start = time.monotonic()
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        try:
            resp = await client.request(
                method=effective_method,
                url=effective_url,
                headers=send_headers,
                content=body_bytes,
            )
            duration_ms = (time.monotonic() - start) * 1000
            resp_body = resp.content
            resp_status = resp.status_code
            resp_headers = dict(resp.headers)
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Request failed: {str(e)}")

    # Store response body if large
    storage_key = None
    if resp_body and len(resp_body) > 0:
        import uuid
        obj_name = f"replays/{uuid.uuid4()}/response.bin"
        storage_key = storage_client.put_object(
            settings.MINIO_BUCKET_EVIDENCE,
            obj_name,
            resp_body,
            content_type=resp_headers.get("content-type", "application/octet-stream"),
        )

    # Store replay record
    replay = Replay(
        original_request_id=original.id,
        modified_url=payload.modified_url,
        modified_method=payload.modified_method,
        modified_headers=mask_sensitive_headers(payload.modified_headers or {}),
        modification_notes=payload.modification_notes,
        response_status=resp_status,
        response_headers=mask_sensitive_headers(resp_headers),
        response_body_storage_key=storage_key,
        duration_ms=duration_ms,
    )
    db.add(replay)
    await db.commit()
    await db.refresh(replay)

    logger.info(
        "replay_executed",
        replay_id=str(replay.id),
        url=effective_url,
        method=effective_method,
        status=resp_status,
        duration_ms=round(duration_ms, 2),
    )
    return replay


@router.get("/{replay_id}/body")
async def get_replay_response_body(
    replay_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve replay response body from object storage."""
    result = await db.execute(select(Replay).where(Replay.id == replay_id))
    replay = result.scalar_one_or_none()
    if not replay:
        raise HTTPException(status_code=404, detail="Replay not found")

    if not replay.response_body_storage_key:
        return {"body": None, "size": 0}

    bucket, obj = replay.response_body_storage_key.split("/", 1)
    data = storage_client.get_object(bucket, obj)
    return {
        "body": data.decode("utf-8", errors="replace") if data else None,
        "size": len(data) if data else 0,
    }
