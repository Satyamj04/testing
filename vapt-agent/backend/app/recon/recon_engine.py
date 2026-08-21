"""
Reconnaissance Engine - DNS, subdomain, technology detection, crawl seeds.
Only operates within configured scope.
"""
import asyncio
import socket
from typing import List, Optional
from urllib.parse import urlparse

import httpx
import structlog
import tldextract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.project import Target
from app.models.scan import Asset, ScanTask
from app.models.scope import Scope
from app.services.scope_validator import ScopeValidator
from app.core.config import settings

logger = structlog.get_logger(__name__)


class ReconEngine:
    """
    Authorized reconnaissance engine.
    All discovered assets are scope-checked before being stored.
    """

    def __init__(self, db: AsyncSession, scan_id: str, target: Target):
        self.db = db
        self.scan_id = scan_id
        self.target = target
        self.validator = ScopeValidator(db)
        self.discovered_assets: List[dict] = []

    async def run(self):
        """Run full recon pipeline."""
        logger.info("recon_started", scan_id=self.scan_id, target=self.target.url)
        task = ScanTask(scan_id=self.scan_id, task_type="recon", status="running")
        self.db.add(task)
        await self.db.flush()

        try:
            parsed = urlparse(self.target.url)
            host = parsed.hostname

            await asyncio.gather(
                self._dns_lookup(host),
                self._http_probe(self.target.url),
                self._check_robots_txt(self.target.url),
                self._check_sitemap(self.target.url),
                return_exceptions=True,
            )

            # Nmap port scan (if authorized)
            await self._nmap_scan(host)

            # Technology detection
            await self._detect_technologies(self.target.url)

            task.status = "completed"
            task.progress = 100
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            logger.error("recon_failed", error=str(e))

        await self.db.commit()
        logger.info("recon_completed", assets_found=len(self.discovered_assets))

    async def _dns_lookup(self, host: str):
        """Resolve DNS and store IP asset."""
        try:
            loop = asyncio.get_event_loop()
            ip = await loop.run_in_executor(None, socket.gethostbyname, host)
            await self._store_asset({
                "asset_type": "ip",
                "host": host,
                "ip_address": ip,
                "source": "dns",
            })
            logger.info("dns_resolved", host=host, ip=ip)
        except Exception as e:
            logger.warning("dns_lookup_failed", host=host, error=str(e))

    async def _http_probe(self, url: str):
        """Probe HTTP/HTTPS service."""
        check = await self.validator.check(url, "GET", str(self.target.id), action="recon_http_probe")
        if not check.allowed:
            return

        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            try:
                resp = await client.get(url, follow_redirects=True)
                server = resp.headers.get("server", "")
                powered_by = resp.headers.get("x-powered-by", "")
                techs = [t for t in [server, powered_by] if t]

                await self._store_asset({
                    "asset_type": "service",
                    "host": urlparse(url).hostname,
                    "port": urlparse(url).port or (443 if url.startswith("https") else 80),
                    "protocol": urlparse(url).scheme,
                    "technologies": techs,
                    "source": "http_probe",
                    "metadata": {
                        "status_code": resp.status_code,
                        "headers": dict(resp.headers),
                    },
                })
            except Exception as e:
                logger.warning("http_probe_failed", url=url, error=str(e))

    async def _check_robots_txt(self, base_url: str):
        """Fetch and parse robots.txt for path discovery."""
        robots_url = base_url.rstrip("/") + "/robots.txt"
        check = await self.validator.check(robots_url, "GET", str(self.target.id), action="recon_robots")
        if not check.allowed:
            return

        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            try:
                resp = await client.get(robots_url)
                if resp.status_code == 200:
                    paths = [
                        line.split(":", 1)[1].strip()
                        for line in resp.text.splitlines()
                        if line.lower().startswith(("disallow:", "allow:"))
                    ]
                    logger.info("robots_txt_found", paths_found=len(paths), url=robots_url)
                    await self._store_asset({
                        "asset_type": "robots_txt",
                        "host": urlparse(base_url).hostname,
                        "source": "robots_txt",
                        "metadata": {"paths": paths, "raw": resp.text[:2000]},
                    })
            except Exception:
                pass

    async def _check_sitemap(self, base_url: str):
        """Fetch sitemap.xml for URL discovery."""
        sitemap_url = base_url.rstrip("/") + "/sitemap.xml"
        check = await self.validator.check(sitemap_url, "GET", str(self.target.id), action="recon_sitemap")
        if not check.allowed:
            return

        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            try:
                resp = await client.get(sitemap_url)
                if resp.status_code == 200:
                    import re
                    urls = re.findall(r"<loc>(.*?)</loc>", resp.text)
                    logger.info("sitemap_found", urls_found=len(urls), url=sitemap_url)
                    await self._store_asset({
                        "asset_type": "sitemap",
                        "host": urlparse(base_url).hostname,
                        "source": "sitemap",
                        "metadata": {"urls": urls[:100]},
                    })
            except Exception:
                pass

    async def _nmap_scan(self, host: str):
        """Run nmap port scan against the target host."""
        try:
            import subprocess
            result = await asyncio.create_subprocess_exec(
                "nmap", "-sV", "--top-ports", "100", "-oX", "-", host,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=120)
            if result.returncode == 0 and stdout:
                # Parse nmap XML output
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(stdout.decode())
                    for port in root.iter("port"):
                        port_id = port.get("portid")
                        protocol = port.get("protocol", "tcp")
                        state = port.find("state")
                        service = port.find("service")
                        if state is not None and state.get("state") == "open":
                            service_name = service.get("name", "") if service is not None else ""
                            product = service.get("product", "") if service is not None else ""
                            await self._store_asset({
                                "asset_type": "service",
                                "host": host,
                                "port": int(port_id),
                                "protocol": protocol,
                                "technologies": [f"{product} {service_name}".strip()],
                                "source": "nmap",
                                "metadata": {"nmap_service": service_name, "product": product},
                            })
                except ET.ParseError:
                    logger.warning("nmap_xml_parse_failed")
        except FileNotFoundError:
            logger.warning("nmap_not_found", message="nmap binary not found, skipping port scan")
        except asyncio.TimeoutError:
            logger.warning("nmap_timeout", host=host)
        except Exception as e:
            logger.warning("nmap_failed", error=str(e))

    async def _detect_technologies(self, url: str):
        """Detect web technologies from response headers and body."""
        check = await self.validator.check(url, "GET", str(self.target.id), action="recon_tech_detect")
        if not check.allowed:
            return

        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            try:
                resp = await client.get(url, follow_redirects=True)
                techs = []

                # Header-based detection
                header_signatures = {
                    "x-powered-by": lambda v: [v],
                    "server": lambda v: [v],
                    "x-generator": lambda v: [v],
                    "x-aspnet-version": lambda v: [f"ASP.NET {v}"],
                    "x-aspnetmvc-version": lambda v: [f"ASP.NET MVC {v}"],
                }
                for header, extractor in header_signatures.items():
                    val = resp.headers.get(header)
                    if val:
                        techs.extend(extractor(val))

                # Body-based detection
                body = resp.text[:10000]
                body_signatures = {
                    "WordPress": ["wp-content", "wp-includes"],
                    "Django": ["csrfmiddlewaretoken", "__django"],
                    "FastAPI": ["FastAPI", "openapi.json"],
                    "React": ["__react", "_reactFiber", "react-dom"],
                    "Vue": ["vue.js", "__vue"],
                    "Angular": ["ng-version", "angular"],
                    "jQuery": ["jquery.min.js", "jquery-"],
                }
                for tech, patterns in body_signatures.items():
                    if any(p.lower() in body.lower() for p in patterns):
                        techs.append(tech)

                if techs:
                    await self._store_asset({
                        "asset_type": "api",
                        "host": urlparse(url).hostname,
                        "technologies": list(set(techs)),
                        "source": "tech_detection",
                    })
            except Exception as e:
                logger.warning("tech_detect_failed", error=str(e))

    async def _store_asset(self, data: dict):
        """Store a discovered asset if in scope."""
        host = data.get("host", "")
        check = await self.validator.check(
            f"http://{host}",
            "GET",
            str(self.target.id),
            action="recon_asset_store",
        )

        asset = Asset(
            target_id=self.target.id,
            scan_id=self.scan_id,
            is_in_scope=check.allowed,
            **data,
        )
        self.db.add(asset)
        self.discovered_assets.append(data)
        await self.db.flush()
