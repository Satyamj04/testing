"""
Findings API - list, view, validate findings.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.finding import Finding, FindingEvidence, ValidationRun, ValidationMethod
from app.models.project import Target, Project
from app.models.user import User
from app.schemas.schemas import FindingResponse
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/findings", tags=["Findings"])


@router.get("", response_model=List[FindingResponse])
async def list_findings(
    target_id: Optional[UUID] = None,
    scan_id: Optional[UUID] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Finding)
        .join(Target, Finding.target_id == Target.id)
        .join(Project, Target.project_id == Project.id)
        .where(Project.owner_id == current_user.id)
        .order_by(Finding.created_at.desc())
    )
    if target_id:
        query = query.where(Finding.target_id == target_id)
    if scan_id:
        query = query.where(Finding.scan_id == scan_id)
    if severity:
        query = query.where(Finding.severity == severity)
    if status:
        query = query.where(Finding.status == status)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Finding)
        .join(Target, Finding.target_id == Target.id)
        .join(Project, Target.project_id == Project.id)
        .where(Finding.id == finding_id, Project.owner_id == current_user.id)
    )
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.get("/{finding_id}/evidence")
async def get_finding_evidence(
    finding_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FindingEvidence).where(FindingEvidence.finding_id == finding_id)
    )
    evidence_list = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "evidence_type": e.evidence_type,
            "title": e.title,
            "description": e.description,
            "data": e.data,
            "storage_key": e.storage_key,
            "created_at": e.created_at.isoformat(),
        }
        for e in evidence_list
    ]


@router.post("/{finding_id}/validate")
async def validate_finding(
    finding_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger re-validation of a finding."""
    result = await db.execute(
        select(Finding)
        .join(Target, Finding.target_id == Target.id)
        .join(Project, Target.project_id == Project.id)
        .where(Finding.id == finding_id, Project.owner_id == current_user.id)
    )
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    from app.models.finding import FindingStatus
    finding.status = FindingStatus.VALIDATING
    await db.commit()

    # Queue validation task
    try:
        from app.workers.validation_worker import validate_finding_task
        validate_finding_task.apply_async(args=[str(finding_id)], queue="validation")
    except Exception:
        pass

    return {"message": "Validation queued", "finding_id": str(finding_id)}
