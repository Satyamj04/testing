"""
API v1 Router - aggregates all route modules.
"""
from fastapi import APIRouter

from app.api.v1 import auth, projects, targets, scans, http_history, repeater, findings, endpoints, ai, reports, proxy

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(targets.router)
api_router.include_router(scans.router)
api_router.include_router(http_history.router)
api_router.include_router(repeater.router)
api_router.include_router(findings.router)
api_router.include_router(endpoints.router)
api_router.include_router(ai.router)
api_router.include_router(reports.router)
api_router.include_router(proxy.router)
