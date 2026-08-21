"""
HTTP History API - view captured proxy traffic.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.storage import storage_client
from app.core.config import settings
from app.models.http_traffic import HTTPRequest
from app.models.project import Target, Project
from app.models.user import User
from app.schemas.schemas import HTTPRequestResponse
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/http-history", tags=["HTTP History"])


@router.get("", response_model=List[HTTPRequestResponse])
async def list_http_history(
    target_id: Optional[UUID] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    host: Optional[str] = None,
    path_contains: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Burp-like HTTP history with multi-field filtering."""
    filters = []
    if target_id:
        filters.append(HTTPRequest.target_id == target_id)
    if method:
        filters.append(HTTPRequest.method == method.upper())
    if status_code:
        filters.append(HTTPRequest.response_status == status_code)
    if host:
        filters.append(HTTPRequest.host.ilike(f"%{host}%"))
    if path_contains:
        filters.append(HTTPRequest.path.ilike(f"%{path_contains}%"))
    if source:
        filters.append(HTTPRequest.source == source)

    query = (
        select(HTTPRequest)
        .join(Target, HTTPRequest.target_id == Target.id)
        .join(Project, Target.project_id == Project.id)
        .where(Project.owner_id == current_user.id)
    )
    if filters:
        query = query.where(and_(*filters))
    query = query.order_by(HTTPRequest.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{request_id}", response_model=HTTPRequestResponse)
async def get_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(HTTPRequest)
        .join(Target, HTTPRequest.target_id == Target.id)
        .join(Project, Target.project_id == Project.id)
        .where(HTTPRequest.id == request_id, Project.owner_id == current_user.id)
    )
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


@router.get("/{request_id}/body")
async def get_request_body(
    request_id: UUID,
    part: str = Query("request", pattern="^(request|response)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve request or response body from MinIO."""
    result = await db.execute(
        select(HTTPRequest)
        .join(Target, HTTPRequest.target_id == Target.id)
        .join(Project, Target.project_id == Project.id)
        .where(HTTPRequest.id == request_id, Project.owner_id == current_user.id)
    )
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    storage_key = req.request_body_storage_key if part == "request" else req.response_body_storage_key
    if not storage_key:
        return {"body": None, "size": 0}

    bucket, obj_name = storage_key.split("/", 1)
    data = storage_client.get_object(bucket, obj_name)
    return {
        "body": data.decode("utf-8", errors="replace") if data else None,
        "size": len(data) if data else 0,
    }
