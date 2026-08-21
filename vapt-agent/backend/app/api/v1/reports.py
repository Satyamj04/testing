"""
Reports API - generate and download VAPT reports.
"""
from typing import List
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.storage import storage_client
from app.models.audit import Report
from app.models.project import Project
from app.models.user import User
from app.schemas.schemas import ReportCreate, ReportResponse
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])
logger = structlog.get_logger(__name__)


@router.post("", response_model=ReportResponse, status_code=201)
async def generate_report(
    payload: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.scan import Scan
    result = await db.execute(
        select(Scan)
        .join(Project, Scan.project_id == Project.id)
        .where(Scan.id == payload.scan_id, Project.owner_id == current_user.id)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    title = payload.title or f"VAPT Report - {scan.id}"
    report = Report(
        project_id=scan.project_id,
        scan_id=scan.id,
        title=title,
        format=payload.format,
        status="generating",
    )
    db.add(report)
    await db.flush()

    # Queue report generation
    try:
        from app.workers.scan_worker import generate_report_task
        generate_report_task.apply_async(
            args=[str(report.id), str(scan.id), payload.format],
            queue="default",
        )
    except Exception as e:
        logger.warning("report_queue_failed", error=str(e))

    await db.commit()
    await db.refresh(report)
    return report


@router.get("", response_model=List[ReportResponse])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Report)
        .join(Project, Report.project_id == Project.id)
        .where(Project.owner_id == current_user.id)
        .order_by(Report.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Report)
        .join(Project, Report.project_id == Project.id)
        .where(Report.id == report_id, Project.owner_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream report file from MinIO storage."""
    result = await db.execute(
        select(Report)
        .join(Project, Report.project_id == Project.id)
        .where(Report.id == report_id, Project.owner_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.status != "completed" or not report.storage_key:
        raise HTTPException(status_code=400, detail="Report is not ready yet")

    bucket, obj = report.storage_key.split("/", 1)
    data = storage_client.get_object(bucket, obj)
    if not data:
        raise HTTPException(status_code=404, detail="Report file not found in storage")

    content_types = {"html": "text/html", "pdf": "application/pdf", "json": "application/json"}
    ct = content_types.get(report.format, "application/octet-stream")
    filename = f"vapt-report-{report.id}.{report.format}"

    return Response(
        content=data,
        media_type=ct,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
