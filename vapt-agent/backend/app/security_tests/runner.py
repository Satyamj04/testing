"""
Security Test Runner - orchestrates all registered security tests against discovered endpoints.
"""
import asyncio
import uuid
from typing import List, Type

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.security_tests.base import SecurityTest, TestContext, FindingCandidate
from app.security_tests.configuration.security_headers import SecurityHeadersTest
from app.security_tests.configuration.cors_test import CORSTest
from app.security_tests.authorization.bola_test import BOLATest
from app.security_tests.injection.sqli_test import SQLInjectionTest
from app.security_tests.authentication.auth_bypass import AuthBypassTest
from app.models.scan import Scan
from app.models.project import Target
from app.models.endpoint import Endpoint
from app.models.finding import Finding, FindingEvidence, FindingStatus
from app.services.scope_validator import ScopeValidator
from app.core.websocket_manager import ws_manager

logger = structlog.get_logger(__name__)

# Registry of all security tests
SECURITY_TESTS: List[Type[SecurityTest]] = [
    SecurityHeadersTest,
    CORSTest,
    BOLATest,
    SQLInjectionTest,
    AuthBypassTest,
]


class SecurityTestRunner:
    """
    Orchestrates security tests against discovered endpoints.
    All tests go through ScopeValidator.
    """

    def __init__(self, db: AsyncSession, scan: Scan, target: Target):
        self.db = db
        self.scan = scan
        self.target = target
        self.validator = ScopeValidator(db)

    async def run(self):
        """Run all applicable security tests against all discovered endpoints."""
        logger.info("security_tests_started", scan_id=str(self.scan.id))

        # Load endpoints
        result = await self.db.execute(
            select(Endpoint).where(Endpoint.target_id == self.target.id)
        )
        endpoints = result.scalars().all()

        if not endpoints:
            logger.warning("no_endpoints_found", scan_id=str(self.scan.id))
            return

        # Build context
        context = TestContext(
            scan_id=str(self.scan.id),
            target_id=str(self.target.id),
            target_url=self.target.url,
        )

        tests_executed = 0
        findings_created = 0

        for endpoint in endpoints:
            ep_dict = {
                "id": str(endpoint.id),
                "method": endpoint.method,
                "path": endpoint.path,
                "host": endpoint.host,
                "requires_auth": endpoint.requires_auth,
                "observed_roles": endpoint.observed_roles or [],
            }

            for TestClass in SECURITY_TESTS:
                test_instance = TestClass(scope_validator=self.validator, db=self.db)

                if not test_instance.can_test(ep_dict, context):
                    continue

                try:
                    test_cases = test_instance.prepare_test(ep_dict, context)
                    results = []

                    for tc in test_cases:
                        try:
                            result = await test_instance.execute(tc, context)
                            results.append(result)
                            tests_executed += 1
                        except Exception as e:
                            logger.warning("test_case_failed",
                                         test=TestClass.name, error=str(e))

                    # Analyze results
                    candidate = test_instance.analyze(results, context)
                    if candidate:
                        finding = await self._create_finding(candidate, endpoint)
                        findings_created += 1

                        # Broadcast finding event
                        await ws_manager.broadcast(
                            "finding.created",
                            {
                                "scan_id": str(self.scan.id),
                                "finding_id": str(finding.id),
                                "title": finding.title,
                                "severity": finding.severity,
                            },
                            channel=f"scan:{self.scan.id}",
                        )

                    # Mark endpoint as tested
                    endpoint.is_tested = True
                    endpoint.test_count += 1
                    await self.db.flush()

                except Exception as e:
                    logger.error("test_failed", test=TestClass.name, error=str(e))

        # Update scan stats
        self.scan.tests_executed = tests_executed
        self.scan.findings_count = findings_created
        await self.db.commit()

        logger.info(
            "security_tests_completed",
            scan_id=str(self.scan.id),
            tests_executed=tests_executed,
            findings=findings_created,
        )

    async def _create_finding(self, candidate: FindingCandidate, endpoint: Endpoint) -> Finding:
        """Persist a candidate finding to the database."""
        finding = Finding(
            target_id=self.target.id,
            scan_id=self.scan.id,
            endpoint_id=endpoint.id,
            title=candidate.title,
            description=candidate.description,
            severity=candidate.severity,
            status=FindingStatus.SUSPECTED,
            confidence=candidate.confidence,
            method=endpoint.method,
            owasp_category=candidate.owasp_category,
            owasp_api_category=candidate.owasp_api_category,
            wstg_category=candidate.wstg_category,
            cwe=candidate.cwe,
            cvss_score=candidate.cvss_score,
            cvss_vector=candidate.cvss_vector,
            impact=candidate.impact,
            reproduction_steps=candidate.reproduction_steps,
            remediation=candidate.remediation,
            references=candidate.references or [],
            detected_by=candidate.detected_by,
        )
        self.db.add(finding)
        await self.db.flush()

        # Store evidence
        if candidate.evidence:
            evidence = FindingEvidence(
                finding_id=finding.id,
                evidence_type="test_result",
                title=f"Evidence: {candidate.title}",
                data=candidate.evidence,
            )
            self.db.add(evidence)

        await self.db.flush()
        return finding
