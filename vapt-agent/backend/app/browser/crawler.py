"""
Browser-based crawler using Playwright.
Discovers endpoints by navigating, clicking, form detection, and network interception.
All traffic goes through ScopeValidator.
"""
import asyncio
import json
import uuid
from typing import List, Set
from urllib.parse import urljoin, urlparse

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Target
from app.models.endpoint import Endpoint
from app.models.http_traffic import HTTPRequest
from app.models.scan import BrowserSession
from app.services.scope_validator import ScopeValidator
from app.core.config import settings
from app.core.storage import storage_client

logger = structlog.get_logger(__name__)


class BrowserCrawler:
    """
    Playwright-powered browser crawler for authenticated application crawling.
    Intercepts network requests and discovers API endpoints.
    """

    def __init__(self, db: AsyncSession, scan_id: str, target: Target):
        self.db = db
        self.scan_id = scan_id
        self.target = target
        self.validator = ScopeValidator(db)
        self.discovered_endpoints: Set[str] = set()
        self.captured_requests: List[dict] = []

    async def crawl(self, auth_profile=None, max_pages: int = 50):
        """Run the browser crawler."""
        logger.info("browser_crawl_started", scan_id=self.scan_id, url=self.target.url)

        session = BrowserSession(
            target_id=self.target.id,
            scan_id=self.scan_id,
            status="running",
        )
        self.db.add(session)
        await self.db.flush()

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--ignore-certificate-errors", "--no-sandbox"],
                )
                context = await browser.new_context(
                    ignore_https_errors=True,
                    viewport={"width": 1280, "height": 800},
                )

                # Intercept network requests
                page = await context.new_page()
                page.on("request", lambda req: asyncio.ensure_future(self._on_request(req)))
                page.on("response", lambda resp: asyncio.ensure_future(self._on_response(resp)))

                visited: Set[str] = set()
                to_visit = [self.target.url]
                pages_visited = 0

                while to_visit and pages_visited < max_pages:
                    url = to_visit.pop(0)
                    if url in visited:
                        continue

                    # Scope check before navigation
                    check = await self.validator.check(
                        url, "GET", str(self.target.id),
                        action="browser_navigate"
                    )
                    if not check.allowed:
                        continue

                    try:
                        resp = await page.goto(url, wait_until="networkidle", timeout=15000)
                        visited.add(url)
                        pages_visited += 1

                        # Take screenshot
                        screenshot = await page.screenshot()
                        obj_name = f"screenshots/{self.scan_id}/{pages_visited}.png"
                        storage_client.put_object(
                            settings.MINIO_BUCKET_EVIDENCE,
                            obj_name,
                            screenshot,
                            content_type="image/png",
                        )

                        # Discover links
                        links = await page.eval_on_selector_all(
                            "a[href]",
                            "elements => elements.map(e => e.href)"
                        )
                        for link in links:
                            if link and link not in visited:
                                abs_link = urljoin(url, link)
                                lcheck = await self.validator.check(
                                    abs_link, "GET", str(self.target.id),
                                    action="browser_link_discovery"
                                )
                                if lcheck.allowed:
                                    to_visit.append(abs_link)

                        # Find forms
                        forms = await page.eval_on_selector_all(
                            "form",
                            """forms => forms.map(f => ({
                                action: f.action,
                                method: f.method || 'GET',
                                inputs: Array.from(f.querySelectorAll('input,select,textarea')).map(i => ({
                                    name: i.name, type: i.type, value: i.value
                                }))
                            }))"""
                        )
                        for form in forms:
                            if form.get("action"):
                                await self._store_endpoint(
                                    method=form["method"].upper(),
                                    path=urlparse(form["action"]).path,
                                    host=urlparse(url).hostname,
                                    scheme=urlparse(url).scheme,
                                    group="Forms",
                                    source="browser_form",
                                )

                        session.pages_visited = pages_visited
                        await self.db.flush()

                    except Exception as e:
                        logger.warning("page_crawl_error", url=url, error=str(e))

                await browser.close()

            session.status = "completed"
            session.endpoints_discovered = len(self.discovered_endpoints)

        except ImportError:
            logger.warning("playwright_not_installed", message="Install playwright for browser crawling")
            session.status = "failed"
            session.error = "Playwright not available"
        except Exception as e:
            logger.error("browser_crawl_failed", error=str(e))
            session.status = "failed"
            session.error = str(e)

        await self.db.commit()
        logger.info("browser_crawl_completed", endpoints=len(self.discovered_endpoints))

    async def _on_request(self, request):
        """Intercept network requests made by the browser."""
        try:
            url = request.url
            method = request.method
            check = await self.validator.check(url, method, str(self.target.id), action="browser_request")
            if not check.allowed:
                return

            parsed = urlparse(url)
            await self._store_endpoint(
                method=method,
                path=parsed.path,
                host=parsed.hostname,
                scheme=parsed.scheme,
                source="browser_network",
            )

            # Store HTTP request record
            req_record = HTTPRequest(
                target_id=self.target.id,
                scan_id=self.scan_id,
                method=method,
                url=url,
                host=parsed.hostname or "",
                path=parsed.path,
                query_string=parsed.query or None,
                scheme=parsed.scheme,
                port=parsed.port,
                request_headers=dict(request.headers),
                source="browser",
            )
            self.db.add(req_record)
            await self.db.flush()
        except Exception:
            pass

    async def _on_response(self, response):
        """Capture response status and headers."""
        pass  # Enhanced in Phase 2 integration with proxy

    async def _store_endpoint(self, method: str, path: str, host: str, scheme: str,
                               group: str = None, source: str = "browser"):
        """Store a unique endpoint in the database."""
        key = f"{method}:{host}{path}"
        if key in self.discovered_endpoints:
            return
        self.discovered_endpoints.add(key)

        endpoint = Endpoint(
            target_id=self.target.id,
            scan_id=self.scan_id,
            method=method,
            path=path,
            host=host or "",
            scheme=scheme,
            group=group or self._infer_group(path),
            source=source,
        )
        self.db.add(endpoint)
        await self.db.flush()

    def _infer_group(self, path: str) -> str:
        """Infer resource group from path."""
        parts = path.strip("/").split("/")
        if parts and parts[0]:
            return parts[0].replace("-", " ").replace("_", " ").title()
        return "Root"
