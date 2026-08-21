"""
Endpoints and Application Map API.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.endpoint import Endpoint, AuthProfile
from app.models.project import Target, Project
from app.models.user import User
from app.api.v1.deps import get_current_user

router = APIRouter(tags=["Endpoints & App Map"])


@router.get("/endpoints", tags=["Endpoints & App Map"])
async def list_endpoints(
    target_id: Optional[UUID] = None,
    group: Optional[str] = None,
    method: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Endpoint)
        .join(Target, Endpoint.target_id == Target.id)
        .join(Project, Target.project_id == Project.id)
        .where(Project.owner_id == current_user.id)
        .order_by(Endpoint.group, Endpoint.path)
    )
    if target_id:
        query = query.where(Endpoint.target_id == target_id)
    if group:
        query = query.where(Endpoint.group.ilike(f"%{group}%"))
    if method:
        query = query.where(Endpoint.method == method.upper())

    result = await db.execute(query)
    endpoints = result.scalars().all()

    return [
        {
            "id": str(e.id),
            "method": e.method,
            "path": e.path,
            "host": e.host,
            "scheme": e.scheme,
            "group": e.group,
            "content_type": e.content_type,
            "requires_auth": e.requires_auth,
            "observed_roles": e.observed_roles or [],
            "source": e.source,
            "is_tested": e.is_tested,
            "test_count": e.test_count,
        }
        for e in endpoints
    ]


@router.get("/targets/{target_id}/app-map", tags=["Endpoints & App Map"])
async def get_application_map(
    target_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a structured application map grouped by resource group."""
    result = await db.execute(
        select(Target)
        .join(Project, Target.project_id == Project.id)
        .where(Target.id == target_id, Project.owner_id == current_user.id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    ep_result = await db.execute(
        select(Endpoint).where(Endpoint.target_id == target_id).order_by(Endpoint.group, Endpoint.path)
    )
    endpoints = ep_result.scalars().all()

    # Group by `group` field
    groups: dict = {}
    for ep in endpoints:
        g = ep.group or "Uncategorized"
        if g not in groups:
            groups[g] = []
        groups[g].append({
            "id": str(ep.id),
            "method": ep.method,
            "path": ep.path,
            "requires_auth": ep.requires_auth,
            "observed_roles": ep.observed_roles or [],
            "is_tested": ep.is_tested,
        })

    return {
        "target_id": str(target_id),
        "target_url": target.url,
        "groups": groups,
        "total_endpoints": len(endpoints),
    }


@router.get("/targets/{target_id}/auth-profiles", tags=["Auth Profiles"])
async def list_auth_profiles(
    target_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Target)
        .join(Project, Target.project_id == Project.id)
        .where(Target.id == target_id, Project.owner_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Target not found")

    ap_result = await db.execute(
        select(AuthProfile).where(AuthProfile.target_id == target_id)
    )
    profiles = ap_result.scalars().all()
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "role": p.role,
            "auth_type": p.auth_type,
            "is_active": p.is_active,
            "notes": p.notes,
        }
        for p in profiles
    ]


@router.post("/targets/{target_id}/auth-profiles", tags=["Auth Profiles"], status_code=201)
async def create_auth_profile(
    target_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Target)
        .join(Project, Target.project_id == Project.id)
        .where(Target.id == target_id, Project.owner_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Target not found")

    profile = AuthProfile(
        target_id=target_id,
        name=payload.get("name", "Unnamed Profile"),
        role=payload.get("role"),
        auth_type=payload.get("auth_type", "none"),
        username=payload.get("username"),
        login_url=payload.get("login_url"),
        login_payload=payload.get("login_payload"),
        notes=payload.get("notes"),
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return {"id": str(profile.id), "name": profile.name, "auth_type": profile.auth_type}
