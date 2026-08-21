"""
Proxy capture endpoint - receives traffic from mitmproxy addon.
"""
import uuid as uuid_mod
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.storage import storage_client
from app.core.config import settings
from app.models.http_traffic import HTTPRequest
from app.core.security import mask_sensitive_headers

router = APIRouter(prefix="/proxy", tags=["Proxy"])


@router.post("/capture")
async def capture_request(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive captured traffic from mitmproxy addon."""
    data = await request.json()

    # Store large bodies in MinIO
    req_body_key = None
    if data.get("request_body") and data.get("request_body_size", 0) > 500:
        key = f"proxy/{uuid_mod.uuid4()}/request.bin"
        req_body_key = storage_client.put_object(
            settings.MINIO_BUCKET_EVIDENCE,
            key,
            data["request_body"].encode(),
        )

    resp_body_key = None
    if data.get("response_body") and data.get("response_body_size", 0) > 500:
        key = f"proxy/{uuid_mod.uuid4()}/response.bin"
        resp_body_key = storage_client.put_object(
            settings.MINIO_BUCKET_EVIDENCE,
            key,
            data["response_body"].encode(),
        )

    req_record = HTTPRequest(
        target_id=data["target_id"],
        scan_id=data.get("scan_id"),
        method=data.get("method", "GET"),
        url=data.get("url", ""),
        host=data.get("host", ""),
        path=data.get("path", "/"),
        query_string=data.get("query_string"),
        scheme=data.get("scheme", "https"),
        port=data.get("port"),
        http_version=data.get("http_version", "HTTP/1.1"),
        request_headers=mask_sensitive_headers(data.get("request_headers") or {}),
        request_body_size=data.get("request_body_size", 0),
        request_body_storage_key=req_body_key,
        response_status=data.get("response_status"),
        response_headers=mask_sensitive_headers(data.get("response_headers") or {}),
        response_body_size=data.get("response_body_size", 0),
        response_body_storage_key=resp_body_key,
        response_content_type=data.get("response_content_type"),
        source="proxy",
        duration_ms=data.get("duration_ms"),
    )
    db.add(req_record)
    await db.commit()

    return {"status": "captured", "request_id": str(req_record.id)}
