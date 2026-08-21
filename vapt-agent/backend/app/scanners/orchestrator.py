"""
External Scanner Orchestrator - coordinates Nmap, ZAP, and Nuclei.
"""
import asyncio
from typing import List

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan import Scan
from app.models.project import Target
from app.models.finding import ScannerResult

logger = structlog.get_logger(__name__)


class ScannerOrchestrator:
    def __init__(self, db: AsyncSession, scan: Scan, target: Target):
        self.db = db
        self.scan = scan
        self.target = target

    async def run(self):
        logger.info("scanners_started", scan_id=str(self.scan.id))
        await asyncio.gather(
            self._run_zap(),
            self._run_nuclei(),
            return_exceptions=True,
        )

    async def _run_zap(self):
        """Run OWASP ZAP spider and active scan."""
        try:
            from zapv2 import ZAPv2
            from app.core.config import settings

            zap = ZAPv2(
                apikey=settings.ZAP_API_KEY,
                proxies={"http": f"http://{settings.ZAP_HOST}:{settings.ZAP_PORT}",
                         "https": f"http://{settings.ZAP_HOST}:{settings.ZAP_PORT}"}
            )

            # Spider
            spider_id = zap.spider.scan(self.target.url)
            await asyncio.sleep(5)

            timeout = 120
            elapsed = 0
            while int(zap.spider.status(spider_id)) < 100 and elapsed < timeout:
                await asyncio.sleep(5)
                elapsed += 5

            # Get alerts
            alerts = zap.core.alerts(baseurl=self.target.url)
            for alert in alerts[:50]:  # Limit
                result = ScannerResult(
                    scan_id=self.scan.id,
                    scanner="zap",
                    target=self.target.url,
                    endpoint=alert.get("url"),
                    category=alert.get("name"),
                    severity=self._map_zap_risk(alert.get("risk", "Low")),
                    title=alert.get("name"),
                    description=alert.get("description"),
                    evidence={"solution": alert.get("solution"), "reference": alert.get("reference"),
                              "param": alert.get("param"), "attack": alert.get("attack")},
                )
                self.db.add(result)

            await self.db.flush()
            logger.info("zap_completed", alerts_found=len(alerts))

        except ImportError:
            logger.warning("zap_client_not_installed")
        except Exception as e:
            logger.warning("zap_failed", error=str(e))

    async def _run_nuclei(self):
        """Run Nuclei template scan."""
        try:
            from app.core.config import settings
            import json

            cmd = [
                settings.NUCLEI_BINARY,
                "-u", self.target.url,
                "-json-export", "-",
                "-severity", "low,medium,high,critical",
                "-no-interactsh",
                "-timeout", "10",
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

            findings_count = 0
            for line in stdout.decode().splitlines():
                try:
                    data = json.loads(line)
                    result = ScannerResult(
                        scan_id=self.scan.id,
                        scanner="nuclei",
                        target=self.target.url,
                        endpoint=data.get("matched-at", self.target.url),
                        category=data.get("info", {}).get("classification", {}).get("cve-id", ""),
                        severity=data.get("info", {}).get("severity", "medium"),
                        title=data.get("info", {}).get("name", ""),
                        description=data.get("info", {}).get("description", ""),
                        evidence={
                            "template": data.get("template-id"),
                            "extracted": data.get("extracted-results", []),
                            "matcher_name": data.get("matcher-name"),
                        },
                    )
                    self.db.add(result)
                    findings_count += 1
                except json.JSONDecodeError:
                    pass

            await self.db.flush()
            logger.info("nuclei_completed", findings=findings_count)

        except FileNotFoundError:
            logger.warning("nuclei_not_found")
        except asyncio.TimeoutError:
            logger.warning("nuclei_timeout")
        except Exception as e:
            logger.warning("nuclei_failed", error=str(e))

    def _map_zap_risk(self, risk: str) -> str:
        mapping = {
            "High": "high",
            "Medium": "medium",
            "Low": "low",
            "Informational": "informational",
        }
        return mapping.get(risk, "low")
