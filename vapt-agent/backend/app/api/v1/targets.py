"""
Targets and Scopes API routes.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.project import Project, Target
from app.models.scope import Scope
from app.models.user import User
from app.schemas.schemas import (
    TargetCreate, TargetUpdate, TargetResponse,
    ScopeCreate, ScopeUpdate, ScopeResponse,
    ScopeCheckRequest, ScopeCheckResponse,
)
from app.api.v1.deps import get_current_user
from app.services.scope_validator import ScopeValidator

router = APIRouter(tags=["Targets & Scopes"])


async def _get_authorized_project(project_id: UUID, user: User, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def _get_authorized_target(target_id: UUID, user: User, db: AsyncSession) -> Target:
    result = await db.execute(
        select(Target)
        .join(Project, Target.project_id == Project.id)
        .where(Target.id == target_id, Project.owner_id == user.id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target


# ── Targets ──────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/targets", response_model=TargetResponse, status_code=201)
async def create_target(
    project_id: UUID,
    payload: TargetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_authorized_project(project_id, current_user, db)
    target = Target(project_id=project_id, **payload.model_dump())
    db.add(target)
    await db.commit()
    await db.refresh(target)
    return target


@router.get("/projects/{project_id}/targets", response_model=List[TargetResponse])
async def list_targets(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_authorized_project(project_id, current_user, db)
    result = await db.execute(
        select(Target).where(Target.project_id == project_id).order_by(Target.created_at.desc())
    )
    return result.scalars().all()


@router.get("/targets/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_authorized_target(target_id, current_user, db)


@router.put("/targets/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: UUID,
    payload: TargetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = await _get_authorized_target(target_id, current_user, db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(target, field, value)
    await db.commit()
    await db.refresh(target)
    return target


@router.delete("/targets/{target_id}", status_code=204)
async def delete_target(
    target_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = await _get_authorized_target(target_id, current_user, db)
    await db.delete(target)
    await db.commit()


# ── Scopes ────────────────────────────────────────────────────────────────────

@router.post("/targets/{target_id}/scope", response_model=ScopeResponse, status_code=201)
async def create_scope(
    target_id: UUID,
    payload: ScopeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_authorized_target(target_id, current_user, db)

    existing = await db.execute(select(Scope).where(Scope.target_id == target_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Scope already exists for this target. Use PUT to update.")

    scope = Scope(target_id=target_id, **payload.model_dump())
    db.add(scope)
    await db.commit()
    await db.refresh(scope)
    return scope


@router.put("/targets/{target_id}/scope", response_model=ScopeResponse)
async def update_scope(
    target_id: UUID,
    payload: ScopeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_authorized_target(target_id, current_user, db)
    result = await db.execute(select(Scope).where(Scope.target_id == target_id))
    scope = result.scalar_one_or_none()
    if not scope:
        raise HTTPException(status_code=404, detail="No scope defined. Use POST to create.")

    for field, value in payload.model_dump(exclude_none=False).items():
        setattr(scope, field, value)

    await db.commit()
    await db.refresh(scope)
    return scope


@router.get("/targets/{target_id}/scope", response_model=ScopeResponse)
async def get_scope(
    target_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_authorized_target(target_id, current_user, db)
    result = await db.execute(select(Scope).where(Scope.target_id == target_id))
    scope = result.scalar_one_or_none()
    if not scope:
        raise HTTPException(status_code=404, detail="No scope defined")
    return scope


@router.post("/targets/{target_id}/scope/check", response_model=ScopeCheckResponse)
async def check_url_in_scope(
    target_id: UUID,
    payload: ScopeCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Interactive scope tester: check if a URL/method is in scope."""
    await _get_authorized_target(target_id, current_user, db)
    validator = ScopeValidator(db)
    result = await validator.check(
        url=payload.url,
        method=payload.method,
        target_id=str(target_id),
        user_id=str(current_user.id),
        action="scope_check",
    )
    return ScopeCheckResponse(
        allowed=result.allowed,
        reason=result.reason,
        url=result.url,
        method=result.method,
    )
