"""
AI Chat and Analysis API endpoints.
"""
import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.models.scan import Scan
from app.models.finding import Finding
from app.models.audit import AIRun
from app.models.project import Target, Project
from app.schemas.schemas import AIChatRequest, AIChatResponse, AIAnalyzeRequest
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Assistant"])
logger = structlog.get_logger(__name__)


@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(
    payload: AIChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI Security Assistant chat endpoint.
    The AI reasons over actual stored findings/evidence - no hallucination.
    """
    from app.agents.vapt_agent import VAPTAgent
    agent = VAPTAgent(db=db, user_id=str(current_user.id))

    try:
        result = await agent.chat(
            message=payload.message,
            scan_id=str(payload.scan_id) if payload.scan_id else None,
            finding_id=str(payload.finding_id) if payload.finding_id else None,
            context=payload.context,
        )

        # Log AI run
        ai_run = AIRun(
            user_id=current_user.id,
            agent_type="chat",
            response=result.get("response", ""),
            tokens_used=result.get("tokens_used"),
            latency_ms=result.get("latency_ms"),
        )
        db.add(ai_run)
        await db.commit()

        return AIChatResponse(
            response=result.get("response", ""),
            tool_calls=result.get("tool_calls"),
            tokens_used=result.get("tokens_used"),
        )
    except Exception as e:
        logger.error("ai_chat_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"AI assistant error: {str(e)}")


@router.post("/analyze")
async def ai_analyze_scan(
    payload: AIAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run AI analysis on a completed scan - correlates findings,
    generates risk summary, and produces remediation prioritization.
    """
    result = await db.execute(
        select(Scan)
        .join(Project, Scan.project_id == Project.id)
        .where(Scan.id == payload.scan_id, Project.owner_id == current_user.id)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    from app.agents.vapt_agent import VAPTAgent
    agent = VAPTAgent(db=db, user_id=str(current_user.id))

    analysis = await agent.analyze_scan(
        scan_id=str(scan.id),
        focus=payload.focus,
    )
    return analysis
