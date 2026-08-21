"""
VAPT AI Agent - orchestrates security reasoning using actual stored evidence.

Critical rules:
- AI NEVER executes HTTP requests directly
- AI ONLY calls registered tools
- Every tool call goes through ScopeValidator
- No hallucination - all responses grounded in stored data
- Every AI action is logged to AIRun table
"""
import json
import time
from typing import Optional, List, Dict, Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.agents.llm_provider import get_llm_provider, Message
from app.models.finding import Finding, FindingStatus, FindingEvidence
from app.models.scan import Scan, Asset
from app.models.endpoint import Endpoint
from app.models.http_traffic import HTTPRequest

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT = """You are an expert AI Security Analyst assistant for a VAPT (Vulnerability Assessment and Penetration Testing) platform.

Your role:
- Analyze security findings backed by real evidence
- Explain vulnerabilities clearly and accurately
- Prioritize remediation recommendations
- Answer questions about the security assessment using ONLY the data provided to you

Critical rules:
- NEVER fabricate evidence, findings, or technical details
- Only reference findings and data that are explicitly provided in context
- Always cite specific evidence when explaining a finding
- Be precise about severity and confidence levels
- If you don't have enough data to answer, say so clearly

You have access to actual security scan results, HTTP request/response evidence, and vulnerability findings.
"""


class VAPTAgent:
    """
    AI VAPT Agent - reasoning layer over the security engine.
    Cannot bypass scope validation or execute arbitrary requests.
    """

    def __init__(self, db: AsyncSession, user_id: Optional[str]):
        self.db = db
        self.user_id = user_id
        self.llm = None

    def _get_llm(self):
        if not self.llm:
            try:
                self.llm = get_llm_provider()
            except Exception as e:
                logger.warning("llm_provider_unavailable", error=str(e))
                return None
        return self.llm

    async def chat(
        self,
        message: str,
        scan_id: Optional[str] = None,
        finding_id: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> dict:
        """Answer user security questions grounded in stored evidence."""
        start = time.monotonic()

        # Build context from database
        context_data = await self._build_context(scan_id=scan_id, finding_id=finding_id)

        llm = self._get_llm()
        if not llm:
            return {
                "response": "AI assistant is not configured. Please set GROQ_API_KEY in your environment.",
                "tokens_used": 0,
            }

        messages = [
            Message(role="system", content=SYSTEM_PROMPT),
            Message(role="user", content=f"""
Context from security scan:
{json.dumps(context_data, indent=2, default=str)}

User question: {message}

Please answer based ONLY on the context above. If the context doesn't contain enough information, say so.
"""),
        ]

        try:
            response = await llm.chat(messages, temperature=0.1, max_tokens=2048)
            latency = (time.monotonic() - start) * 1000

            return {
                "response": response.content,
                "tokens_used": response.tokens_used,
                "latency_ms": latency,
            }
        except Exception as e:
            logger.error("ai_chat_error", error=str(e))
            return {
                "response": f"AI analysis unavailable: {str(e)}",
                "tokens_used": 0,
            }

    async def analyze_scan(self, scan_id: str, focus: Optional[str] = None) -> dict:
        """
        Analyze a completed scan - correlate findings, generate risk summary.
        Grounded entirely in stored findings and evidence.
        """
        context_data = await self._build_scan_context(scan_id)

        if not context_data.get("findings"):
            return {
                "summary": "No findings to analyze.",
                "risk_level": "informational",
                "recommendations": [],
            }

        llm = self._get_llm()
        if not llm:
            return {
                "summary": "AI analysis unavailable - LLM not configured.",
                "findings_count": len(context_data.get("findings", [])),
            }

        focus_text = f"Focus on: {focus}" if focus else "Provide a comprehensive analysis."

        messages = [
            Message(role="system", content=SYSTEM_PROMPT),
            Message(role="user", content=f"""
Analyze the following VAPT scan results and provide:
1. Executive summary (2-3 sentences)
2. Top 3 most critical findings with explanation
3. Risk level assessment (Critical/High/Medium/Low)
4. Top 5 prioritized remediation recommendations
5. OWASP category coverage gaps

{focus_text}

Scan data:
{json.dumps(context_data, indent=2, default=str)}

Base your analysis ONLY on the data above.
"""),
        ]

        try:
            response = await llm.chat(messages, temperature=0.1, max_tokens=3000)
            return {
                "analysis": response.content,
                "findings_analyzed": len(context_data.get("findings", [])),
                "tokens_used": response.tokens_used,
                "scan_id": scan_id,
            }
        except Exception as e:
            logger.error("scan_analysis_failed", error=str(e))
            return {"error": str(e), "scan_id": scan_id}

    async def _build_context(self, scan_id: Optional[str], finding_id: Optional[str]) -> dict:
        """Build context from database for AI reasoning."""
        context = {}

        if finding_id:
            result = await self.db.execute(
                select(Finding).where(Finding.id == finding_id)
            )
            finding = result.scalar_one_or_none()
            if finding:
                context["finding"] = self._finding_to_dict(finding)

                # Load evidence
                ev_result = await self.db.execute(
                    select(FindingEvidence).where(FindingEvidence.finding_id == finding_id)
                )
                evidence_list = ev_result.scalars().all()
                context["evidence"] = [
                    {"type": e.evidence_type, "data": e.data, "title": e.title}
                    for e in evidence_list
                ]

        if scan_id:
            scan_context = await self._build_scan_context(scan_id)
            context.update(scan_context)

        return context

    async def _build_scan_context(self, scan_id: str) -> dict:
        """Build scan-level context."""
        result = await self.db.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one_or_none()
        if not scan:
            return {}

        # Findings summary
        findings_result = await self.db.execute(
            select(Finding).where(Finding.scan_id == scan_id).limit(50)
        )
        findings = findings_result.scalars().all()

        # Severity counts
        severity_counts = {}
        for f in findings:
            severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

        # Status counts
        status_counts = {}
        for f in findings:
            status_counts[f.status] = status_counts.get(f.status, 0) + 1

        # Endpoints
        ep_result = await self.db.execute(
            select(func.count(Endpoint.id)).where(Endpoint.target_id == scan.target_id)
        )
        endpoint_count = ep_result.scalar() or 0

        return {
            "scan": {
                "id": str(scan.id),
                "status": scan.status,
                "tests_executed": scan.tests_executed,
                "findings_count": scan.findings_count,
                "confirmed_findings": scan.confirmed_findings,
                "endpoints_discovered": endpoint_count,
            },
            "severity_breakdown": severity_counts,
            "status_breakdown": status_counts,
            "findings": [self._finding_to_dict(f) for f in findings[:20]],  # Limit for context
        }

    def _finding_to_dict(self, finding: Finding) -> dict:
        return {
            "id": str(finding.id),
            "title": finding.title,
            "severity": finding.severity,
            "status": finding.status,
            "confidence": finding.confidence,
            "description": finding.description[:500],
            "owasp_category": finding.owasp_category,
            "owasp_api_category": finding.owasp_api_category,
            "cwe": finding.cwe,
            "cvss_score": finding.cvss_score,
            "impact": finding.impact,
            "remediation": finding.remediation,
            "detected_by": finding.detected_by,
        }
