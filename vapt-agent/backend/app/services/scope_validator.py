"""
ScopeValidator - The central authorization enforcement engine.

EVERY scanner, browser worker, proxy action, replay, and security test
MUST pass through this validator before executing any request.

Architecture:
    Request
      |
      v
    ScopeValidator
      |
      +-- Allowed --> Execute
      |
      +-- Blocked --> AuditLog + Raise ScopeViolation
"""
import ipaddress
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import structlog
import tldextract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.scope import Scope
from app.models.audit import AuditLog

logger = structlog.get_logger(__name__)


class ScopeViolationError(Exception):
    """Raised when a request violates the configured scope."""
    def __init__(self, message: str, url: str, reason: str):
        super().__init__(message)
        self.url = url
        self.reason = reason


@dataclass
class ScopeCheckResult:
    allowed: bool
    reason: str
    url: str
    method: str
    scope_id: Optional[str] = None


class ScopeValidator:
    """
    Centralized scope enforcement engine.
    Validates URLs and HTTP methods against target scope configuration.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def load_scope(self, target_id: str) -> Optional[Scope]:
        """Load scope configuration from database."""
        result = await self.db.execute(
            select(Scope).where(Scope.target_id == target_id)
        )
        return result.scalar_one_or_none()

    async def check(
        self,
        url: str,
        method: str,
        target_id: str,
        user_id: Optional[str] = None,
        action: str = "request",
    ) -> ScopeCheckResult:
        """
        Primary scope check method. Returns ScopeCheckResult.
        Logs blocked requests to the audit log.
        """
        scope = await self.load_scope(target_id)

        if scope is None:
            reason = "no_scope_defined"
            result = ScopeCheckResult(
                allowed=False, reason=reason, url=url, method=method
            )
            await self._log_blocked(user_id, target_id, url, method, action, reason)
            return result

        check_result = self._evaluate(url, method, scope)

        if not check_result.allowed:
            await self._log_blocked(
                user_id, target_id, url, method, action, check_result.reason
            )
            logger.warning(
                "scope_violation_blocked",
                url=url,
                method=method,
                reason=check_result.reason,
                target_id=str(target_id),
            )

        return check_result

    async def enforce(
        self,
        url: str,
        method: str,
        target_id: str,
        user_id: Optional[str] = None,
        action: str = "request",
    ) -> None:
        """
        Like check(), but raises ScopeViolationError if not allowed.
        Use this in security tests and scanners.
        """
        result = await self.check(url, method, target_id, user_id, action)
        if not result.allowed:
            raise ScopeViolationError(
                f"Scope violation: {result.reason}",
                url=url,
                reason=result.reason,
            )

    def _evaluate(self, url: str, method: str, scope: Scope) -> ScopeCheckResult:
        """Deterministic scope evaluation logic."""
        try:
            parsed = urlparse(url)
        except Exception:
            return ScopeCheckResult(
                allowed=False, reason="invalid_url", url=url, method=method
            )

        host = parsed.hostname or ""
        path = parsed.path or "/"
        port = parsed.port
        scheme = parsed.scheme

        # ── 1. Check excluded methods ────────────────────────────────────────
        excluded_methods = [m.upper() for m in (scope.excluded_methods or [])]
        if method.upper() in excluded_methods:
            return ScopeCheckResult(
                allowed=False,
                reason=f"method_excluded:{method}",
                url=url,
                method=method,
            )

        # ── 2. Check excluded domains ────────────────────────────────────────
        for exc_domain in (scope.excluded_domains or []):
            if self._host_matches(host, exc_domain):
                return ScopeCheckResult(
                    allowed=False,
                    reason=f"domain_excluded:{exc_domain}",
                    url=url,
                    method=method,
                )

        # ── 3. Check excluded paths ──────────────────────────────────────────
        for exc_path in (scope.excluded_paths or []):
            if self._path_matches(path, exc_path):
                return ScopeCheckResult(
                    allowed=False,
                    reason=f"path_excluded:{exc_path}",
                    url=url,
                    method=method,
                )

        # ── 4. Check allowed domains / subdomains ────────────────────────────
        allowed_domains = list(scope.allowed_domains or []) + list(scope.allowed_subdomains or [])
        if allowed_domains:
            if not any(self._host_matches(host, d) for d in allowed_domains):
                # Check allowed IP ranges
                if not self._check_ip_in_ranges(host, scope.allowed_ip_ranges or []):
                    return ScopeCheckResult(
                        allowed=False,
                        reason=f"host_not_in_scope:{host}",
                        url=url,
                        method=method,
                    )

        return ScopeCheckResult(
            allowed=True,
            reason="allowed",
            url=url,
            method=method,
            scope_id=str(scope.id),
        )

    def _host_matches(self, host: str, pattern: str) -> bool:
        """
        Match host against a domain pattern.
        Supports wildcard subdomains like *.example.com
        """
        pattern = pattern.lstrip("*").lstrip(".")
        host_clean = host.lower()
        pat_clean = pattern.lower()
        return host_clean == pat_clean or host_clean.endswith("." + pat_clean)

    def _path_matches(self, path: str, pattern: str) -> bool:
        """
        Match path against exclusion pattern.
        Supports prefix matching and basic glob patterns.
        """
        # Exact match
        if path == pattern:
            return True
        # Prefix match
        if path.startswith(pattern):
            return True
        # Glob / regex pattern
        try:
            if re.match(pattern, path):
                return True
        except re.error:
            pass
        return False

    def _check_ip_in_ranges(self, host: str, ip_ranges: list[str]) -> bool:
        """Check if host is an IP inside allowed CIDR ranges."""
        try:
            ip = ipaddress.ip_address(host)
            for cidr in ip_ranges:
                try:
                    network = ipaddress.ip_network(cidr, strict=False)
                    if ip in network:
                        return True
                except ValueError:
                    continue
        except ValueError:
            # Not a valid IP - it's a hostname
            pass
        return False

    async def _log_blocked(
        self,
        user_id: Optional[str],
        target_id: str,
        url: str,
        method: str,
        action: str,
        reason: str,
    ):
        """Write a blocked-request audit log entry."""
        try:
            import uuid as uuid_mod
            log = AuditLog(
                user_id=uuid_mod.UUID(user_id) if user_id else None,
                target_id=uuid_mod.UUID(target_id) if target_id else None,
                action=action,
                resource_type="http_request",
                resource_id=url,
                result="blocked",
                reason=reason,
                metadata={"url": url, "method": method},
            )
            self.db.add(log)
            await self.db.flush()
        except Exception as e:
            logger.error("audit_log_failed", error=str(e))
