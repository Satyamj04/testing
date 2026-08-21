"""
Authentication Bypass Test - OWASP A07:2021 Identification and Authentication Failures
Tests authentication state and session management.
"""
from typing import List, Optional
from app.security_tests.base import SecurityTest, TestContext, TestCase, TestResult, FindingCandidate


class AuthBypassTest(SecurityTest):
    name = "Authentication Bypass Test"
    description = "Tests authentication enforcement on protected endpoints"
    category = "authentication"
    owasp_top10 = "A07:2021 - Identification and Authentication Failures"
    owasp_api = "API2:2023 - Broken Authentication"
    wstg = "WSTG-ATHN-01"
    cwe = "CWE-287"

    def can_test(self, endpoint: dict, context: TestContext) -> bool:
        return endpoint.get("requires_auth", True)

    def prepare_test(self, endpoint: dict, context: TestContext) -> List[TestCase]:
        path = endpoint.get("path", "/")
        method = endpoint.get("method", "GET")
        base_url = f"{context.target_url.rstrip('/')}{path}"

        return [
            # No auth at all
            TestCase(
                test_id=f"auth_bypass_no_auth_{endpoint.get('id', 'ep')}",
                name="Auth Bypass - No Authentication",
                url=base_url,
                method=method,
                headers={},
                metadata={"test_type": "no_auth"},
            ),
            # Empty auth header
            TestCase(
                test_id=f"auth_bypass_empty_{endpoint.get('id', 'ep')}",
                name="Auth Bypass - Empty Authorization",
                url=base_url,
                method=method,
                headers={"Authorization": ""},
                metadata={"test_type": "empty_auth"},
            ),
            # Invalid token
            TestCase(
                test_id=f"auth_bypass_invalid_{endpoint.get('id', 'ep')}",
                name="Auth Bypass - Invalid Token",
                url=base_url,
                method=method,
                headers={"Authorization": "Bearer invalid.token.here"},
                metadata={"test_type": "invalid_token"},
            ),
        ]

    async def execute(self, test_case: TestCase, context: TestContext) -> TestResult:
        result = await self._safe_request(
            url=test_case.url,
            method=test_case.method,
            target_id=context.target_id,
            headers=test_case.headers,
        )

        # Should return 401 or 403 - if 200, authentication is not enforced
        is_vulnerable = result["status_code"] in (200, 201, 202)

        return TestResult(
            test_id=test_case.test_id,
            test_case=test_case,
            status_code=result["status_code"],
            response_headers=result["headers"],
            response_body=result["body"][:2000],
            duration_ms=result["duration_ms"],
            is_vulnerable=is_vulnerable,
            confidence=0.9 if is_vulnerable else 0.0,
            evidence={
                "test_type": test_case.metadata.get("test_type"),
                "expected_status": "401 or 403",
                "actual_status": result["status_code"],
                "response_preview": result["body"][:300],
            },
        )

    def analyze(self, results: List[TestResult], context: TestContext) -> Optional[FindingCandidate]:
        vulnerable = [r for r in results if r.is_vulnerable]
        if not vulnerable:
            return None

        best = vulnerable[0]
        test_type = best.evidence.get("test_type")

        return FindingCandidate(
            title="Authentication Bypass - Endpoint Accessible Without Valid Credentials",
            description=(
                f"The endpoint {best.test_case.url} returned HTTP {best.status_code} "
                f"without valid authentication credentials (test: {test_type}). "
                f"This endpoint should require authentication."
            ),
            severity="critical",
            confidence="high",
            owasp_category="A07:2021 - Identification and Authentication Failures",
            owasp_api_category="API2:2023 - Broken Authentication",
            wstg_category="WSTG-ATHN-01",
            cwe="CWE-287",
            cvss_score=9.1,
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
            impact="Unauthenticated access to this endpoint may allow attackers to view or modify sensitive data without any credentials.",
            reproduction_steps=(
                f"1. Send {best.test_case.method} to {best.test_case.url}\n"
                f"2. Do NOT include any Authorization header\n"
                f"3. Observe HTTP {best.status_code} - endpoint is accessible"
            ),
            remediation="Enforce authentication on all protected endpoints. Apply authentication middleware globally and explicitly mark public endpoints as excepted.",
            references=[
                "https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/",
                "https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/04-Authentication_Testing/01-Testing_for_Credentials_Transported_over_an_Encrypted_Channel",
            ],
            evidence=best.evidence,
            detected_by="auth_bypass_test",
        )

    def collect_evidence(self, result: TestResult) -> dict:
        return {
            "type": "auth_bypass",
            "url": result.test_case.url,
            "test_type": result.evidence.get("test_type"),
            "status_code": result.status_code,
            "response_preview": result.response_body[:300],
        }
