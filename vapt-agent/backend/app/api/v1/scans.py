"""
Scans API - create, monitor, cancel scans.
"""
from typing import List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.scan import Scan, ScanStatus
from app.models.project import Target, Project
from app.models.user import User
from app.schemas.schemas import ScanCreate, ScanResponse
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/scans", tags=["Scans"])
logger = structlog.get_logger(__name__)


@router.post("", response_model=ScanResponse, status_code=201)
async def create_scan(
    payload: ScanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify target ownership and authorization
    result = await db.execute(
        select(Target)
        .join(Project, Target.project_id == Project.id)
        .where(Target.id == payload.target_id, Project.owner_id == current_user.id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    if not target.is_authorized:
        raise HTTPException(status_code=403, detail="Target is not marked as authorized for testing")

    scan = Scan(
        project_id=target.project_id,
        target_id=target.id,
        scan_type=payload.scan_type,
        config=payload.config or {},
    )
    db.add(scan)
    await db.flush()

    # Queue Celery task
    try:
        from app.workers.scan_worker import run_full_scan
        task = run_full_scan.apply_async(
            args=[str(scan.id)],
            queue="scans",
        )
        scan.celery_task_id = task.id
    except Exception as e:
        logger.warning("celery_unavailable", error=str(e))
        scan.status = ScanStatus.QUEUED

    await db.commit()
    await db.refresh(scan)
    logger.info("scan_created", scan_id=str(scan.id), target=str(target.url))
    return scan


@router.get("", response_model=List[ScanResponse])
async def list_scans(
    target_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Scan)
        .join(Project, Scan.project_id == Project.id)
        .where(Project.owner_id == current_user.id)
        .order_by(Scan.created_at.desc())
    )
    if target_id:
        query = query.where(Scan.target_id == target_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Scan)
        .join(Project, Scan.project_id == Project.id)
        .where(Scan.id == scan_id, Project.owner_id == current_user.id)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.post("/{scan_id}/cancel", response_model=ScanResponse)
async def cancel_scan(
    scan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Scan)
        .join(Project, Scan.project_id == Project.id)
        .where(Scan.id == scan_id, Project.owner_id == current_user.id)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.status in (ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED):
        raise HTTPException(status_code=400, detail=f"Scan is already {scan.status}")

    if scan.celery_task_id:
        try:
            from app.workers.celery_app import celery_app
            celery_app.control.revoke(scan.celery_task_id, terminate=True)
        except Exception as e:
            logger.warning("celery_revoke_failed", error=str(e))

    scan.status = ScanStatus.CANCELLED
    await db.commit()
    await db.refresh(scan)
    return scan
