"""
VAPT Report Generator - produces HTML, PDF, and JSON reports.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

import structlog
from jinja2 import Environment, BaseLoader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.scan import Scan
from app.models.project import Project, Target
from app.models.finding import Finding, FindingEvidence
from app.models.endpoint import Endpoint
from app.models.audit import Report
from app.core.storage import storage_client
from app.core.config import settings

logger = structlog.get_logger(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{{ report_title }} - VAPT Report</title>
<style>
  body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 1100px; margin: 0 auto; padding: 20px; background: #0f1117; color: #e0e0e0; }
  h1 { color: #00d4ff; border-bottom: 2px solid #00d4ff; padding-bottom: 10px; }
  h2 { color: #7c3aed; margin-top: 30px; }
  h3 { color: #a78bfa; }
  .executive-summary { background: #1a1d2e; border-left: 4px solid #00d4ff; padding: 15px; margin: 20px 0; border-radius: 4px; }
  .finding { background: #1a1d2e; border-radius: 8px; padding: 20px; margin: 15px 0; border-left: 4px solid #666; }
  .finding.critical { border-left-color: #ef4444; }
  .finding.high { border-left-color: #f97316; }
  .finding.medium { border-left-color: #eab308; }
  .finding.low { border-left-color: #22c55e; }
  .finding.informational { border-left-color: #6b7280; }
  .badge { display: inline-block; padding: 3px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; margin: 2px; }
  .badge.critical { background: #ef4444; color: white; }
  .badge.high { background: #f97316; color: white; }
  .badge.medium { background: #eab308; color: #000; }
  .badge.low { background: #22c55e; color: #000; }
  .badge.confirmed { background: #22c55e; color: #000; }
  .badge.suspected { background: #6b7280; color: white; }
  .summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }
  .stat-card { background: #1a1d2e; padding: 15px; border-radius: 8px; text-align: center; }
  .stat-number { font-size: 32px; font-weight: bold; color: #00d4ff; }
  .stat-label { font-size: 12px; color: #9ca3af; margin-top: 5px; }
  pre { background: #0a0c14; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 12px; color: #a0a0a0; }
  table { width: 100%; border-collapse: collapse; margin: 15px 0; }
  th { background: #1a1d2e; padding: 10px; text-align: left; color: #7c3aed; }
  td { padding: 10px; border-bottom: 1px solid #2d2d2d; }
  .owasp-tag { background: #7c3aed; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px; margin: 2px; display: inline-block; }
</style>
</head>
<body>

<h1>🔒 VAPT Security Assessment Report</h1>
<p style="color: #9ca3af;">{{ report_title }} | Generated: {{ generated_at }} | Scan ID: {{ scan_id }}</p>

<div class="executive-summary">
<h2>Executive Summary</h2>
<p><strong>Target:</strong> {{ target_url }}</p>
<p><strong>Assessment Scope:</strong> {{ scope_description }}</p>
<p>This assessment identified <strong>{{ total_findings }}</strong> findings across the target application, 
of which <strong>{{ confirmed_findings }}</strong> have been confirmed through reproducible evidence.</p>
</div>

<div class="summary-grid">
  <div class="stat-card">
    <div class="stat-number" style="color: #ef4444;">{{ severity_counts.critical or 0 }}</div>
    <div class="stat-label">CRITICAL</div>
  </div>
  <div class="stat-card">
    <div class="stat-number" style="color: #f97316;">{{ severity_counts.high or 0 }}</div>
    <div class="stat-label">HIGH</div>
  </div>
  <div class="stat-card">
    <div class="stat-number" style="color: #eab308;">{{ severity_counts.medium or 0 }}</div>
    <div class="stat-label">MEDIUM</div>
  </div>
  <div class="stat-card">
    <div class="stat-number" style="color: #22c55e;">{{ severity_counts.low or 0 }}</div>
    <div class="stat-label">LOW</div>
  </div>
  <div class="stat-card">
    <div class="stat-number">{{ endpoints_tested }}</div>
    <div class="stat-label">ENDPOINTS TESTED</div>
  </div>
  <div class="stat-card">
    <div class="stat-number">{{ tests_executed }}</div>
    <div class="stat-label">TESTS EXECUTED</div>
  </div>
</div>

<h2>Detailed Findings</h2>

{% for finding in findings %}
<div class="finding {{ finding.severity }}">
  <h3>
    <span class="badge {{ finding.severity }}">{{ finding.severity|upper }}</span>
    <span class="badge {{ finding.status }}">{{ finding.status|upper }}</span>
    {{ finding.title }}
  </h3>
  
  {% if finding.owasp_category %}<span class="owasp-tag">{{ finding.owasp_category }}</span>{% endif %}
  {% if finding.cwe %}<span class="owasp-tag">{{ finding.cwe }}</span>{% endif %}
  {% if finding.cvss_score %}<span class="badge">CVSS: {{ finding.cvss_score }}</span>{% endif %}
  
  <p><strong>Description:</strong> {{ finding.description }}</p>
  
  {% if finding.impact %}
  <p><strong>Impact:</strong> {{ finding.impact }}</p>
  {% endif %}
  
  {% if finding.reproduction_steps %}
  <p><strong>Reproduction Steps:</strong></p>
  <pre>{{ finding.reproduction_steps }}</pre>
  {% endif %}
  
  {% if finding.remediation %}
  <p><strong>Remediation:</strong> {{ finding.remediation }}</p>
  {% endif %}
  
  {% if finding.references %}
  <p><strong>References:</strong></p>
  <ul>{% for ref in finding.references %}<li><a href="{{ ref }}" style="color: #00d4ff;">{{ ref }}</a></li>{% endfor %}</ul>
  {% endif %}
</div>
{% endfor %}

<h2>OWASP Coverage</h2>
<table>
  <tr><th>Category</th><th>Findings</th></tr>
  {% for category, count in owasp_coverage.items() %}
  <tr><td>{{ category }}</td><td>{{ count }}</td></tr>
  {% endfor %}
</table>

<footer style="margin-top: 50px; color: #4b5563; text-align: center; border-top: 1px solid #2d2d2d; padding-top: 20px;">
  <p>Generated by VAPT Agent | {{ generated_at }}</p>
  <p><em>This report is confidential and intended only for authorized personnel.</em></p>
  <p><em>Vulnerability detection is not 100% complete. Manual review is recommended for critical systems.</em></p>
</footer>
</body>
</html>
"""


class ReportGenerator:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(self, report_id: str, scan_id: str, format: str):
        """Generate a VAPT report and store in MinIO."""
        logger.info("report_generation_started", report_id=report_id, format=format)

        report_result = await self.db.execute(select(Report).where(Report.id == report_id))
        report = report_result.scalar_one_or_none()
        if not report:
            return

        try:
            data = await self._gather_report_data(scan_id)

            if format == "json":
                content = json.dumps(data, indent=2, default=str).encode()
                ct = "application/json"
            elif format == "html":
                content = self._render_html(data).encode()
                ct = "text/html"
            elif format == "pdf":
                html = self._render_html(data)
                try:
                    from weasyprint import HTML as WeasyprintHTML
                    content = WeasyprintHTML(string=html).write_pdf()
                    ct = "application/pdf"
                except ImportError:
                    content = html.encode()
                    ct = "text/html"
                    format = "html"
            else:
                raise ValueError(f"Unknown format: {format}")

            obj_name = f"reports/{report_id}/report.{format}"
            storage_client.put_object(settings.MINIO_BUCKET_REPORTS, obj_name, content, ct)

            report.storage_key = f"{settings.MINIO_BUCKET_REPORTS}/{obj_name}"
            report.file_size = len(content)
            report.status = "completed"
            report.summary = {
                "total_findings": data.get("total_findings"),
                "confirmed_findings": data.get("confirmed_findings"),
                "severity_counts": data.get("severity_counts"),
            }

        except Exception as e:
            logger.error("report_generation_failed", error=str(e))
            report.status = "failed"
            report.error = str(e)

        await self.db.commit()

    async def _gather_report_data(self, scan_id: str) -> dict:
        scan_result = await self.db.execute(select(Scan).where(Scan.id == scan_id))
        scan = scan_result.scalar_one_or_none()

        target_result = await self.db.execute(select(Target).where(Target.id == scan.target_id))
        target = target_result.scalar_one_or_none()

        project_result = await self.db.execute(select(Project).where(Project.id == scan.project_id))
        project = project_result.scalar_one_or_none()

        findings_result = await self.db.execute(
            select(Finding).where(Finding.scan_id == scan_id).order_by(
                Finding.severity.desc(), Finding.status
            )
        )
        findings = findings_result.scalars().all()

        severity_counts = {}
        owasp_coverage = {}
        for f in findings:
            severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1
            if f.owasp_category:
                owasp_coverage[f.owasp_category] = owasp_coverage.get(f.owasp_category, 0) + 1
            if f.owasp_api_category:
                owasp_coverage[f.owasp_api_category] = owasp_coverage.get(f.owasp_api_category, 0) + 1

        confirmed = [f for f in findings if f.status == "confirmed"]

        return {
            "report_title": project.name if project else "Security Assessment",
            "scan_id": str(scan_id),
            "target_url": target.url if target else "",
            "scope_description": "Authorized assessment scope",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_findings": len(findings),
            "confirmed_findings": len(confirmed),
            "endpoints_tested": scan.endpoints_discovered if scan else 0,
            "tests_executed": scan.tests_executed if scan else 0,
            "severity_counts": severity_counts,
            "owasp_coverage": owasp_coverage,
            "findings": [
                {
                    "id": str(f.id),
                    "title": f.title,
                    "description": f.description,
                    "severity": f.severity,
                    "status": f.status,
                    "confidence": f.confidence,
                    "owasp_category": f.owasp_category,
                    "owasp_api_category": f.owasp_api_category,
                    "cwe": f.cwe,
                    "cvss_score": f.cvss_score,
                    "cvss_vector": f.cvss_vector,
                    "impact": f.impact,
                    "reproduction_steps": f.reproduction_steps,
                    "remediation": f.remediation,
                    "references": f.references or [],
                    "detected_by": f.detected_by,
                }
                for f in findings
            ],
        }

    def _render_html(self, data: dict) -> str:
        env = Environment(loader=BaseLoader())
        template = env.from_string(HTML_TEMPLATE)
        return template.render(**data)
