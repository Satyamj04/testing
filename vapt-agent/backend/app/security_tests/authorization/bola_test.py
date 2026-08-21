"""
BOLA/IDOR Test - Broken Object Level Authorization
OWASP API1:2023 - Broken Object Level Authorization
Tests whether object-level authorization is enforced.
"""
import re
from typing import List, Optional
from app.security_tests.base import SecurityTest, TestContext, TestCase, TestResult, FindingCandidate


class BOLATest(SecurityTest):
    name = "BOLA/IDOR Test"
    description = "Tests for Broken Object Level Authorization (BOLA/IDOR) vulnerabilities"
    category = "authorization"
    owasp_top10 = "A01:2021 - Broken Access Control"
    owasp_api = "API1:2023 - Broken Object Level Authorization"
    wstg = "WSTG-ATHZ-01"
    cwe = "CWE-639"

    # Path parameter patterns that suggest object IDs
    ID_PATTERNS = [
        r"/(\d+)(?:/|$)",
        r"/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})(?:/|$)",  # UUID
        r"/([a-zA-Z0-9]{20,})(?:/|$)",  # Long alphanumeric ID
    ]

    def can_test(self, endpoint: dict, context: TestContext) -> bool:
        """Can test endpoints with ID parameters in path."""
        path = endpoint.get("path", "")
        for pattern in self.ID_PATTERNS:
            if re.search(pattern, path):
                return True
        return False

    def prepare_test(self, endpoint: dict, context: TestContext) -> List[TestCase]:
        """
        Prepare BOLA test cases:
        1. Access own resource (baseline)
        2. Access resource with adjacent/incremented ID
        3. Access with different auth profile
        """
        path = endpoint.get("path", "")
        method = endpoint.get("method", "GET")
        base_url = f"{context.target_url.rstrip('/')}{path}"

        cases = []

        # Test: increment numeric IDs
        def increment_id(m):
            current = int(m.group(1))
            return m.group(0).replace(str(current), str(current + 1))

        incremented_url = re.sub(r"/(\d+)(?=/|$)", increment_id, base_url)
        if incremented_url != base_url:
            cases.append(TestCase(
                test_id=f"bola_incr_{endpoint.get('id', 'ep')}",
                name="BOLA - Incremented ID",
                url=incremented_url,
                method=method,
                headers=context.auth_headers or {},
                metadata={"test_type": "id_manipulation", "original_url": base_url},
            ))

        # Test: attempt with ID=0
        zero_url = re.sub(r"/(\d+)(?=/|$)", lambda m: m.group(0).replace(m.group(1), "0"), base_url)
        if zero_url != base_url:
            cases.append(TestCase(
                test_id=f"bola_zero_{endpoint.get('id', 'ep')}",
                name="BOLA - Zero ID",
                url=zero_url,
                method=method,
                headers=context.auth_headers or {},
                metadata={"test_type": "zero_id"},
            ))

        # Test: attempt with known-invalid UUID
        invalid_uuid_url = re.sub(
            r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
            "00000000-0000-0000-0000-000000000001",
            base_url
        )
        if invalid_uuid_url != base_url:
            cases.append(TestCase(
                test_id=f"bola_uuid_{endpoint.get('id', 'ep')}",
                name="BOLA - Different UUID",
                url=invalid_uuid_url,
                method=method,
                headers=context.auth_headers or {},
                metadata={"test_type": "uuid_manipulation"},
            ))

        return cases

    async def execute(self, test_case: TestCase, context: TestContext) -> TestResult:
        result = await self._safe_request(
            url=test_case.url,
            method=test_case.method,
            target_id=context.target_id,
            headers=test_case.headers,
        )

        # BOLA indicator: 200 response with non-empty body for manipulated IDs
        is_suspicious = (
            result["status_code"] in (200, 201)
            and len(result["body"]) > 10
        )

        return TestResult(
            test_id=test_case.test_id,
            test_case=test_case,
            status_code=result["status_code"],
            response_headers=result["headers"],
            response_body=result["body"][:2000],
            duration_ms=result["duration_ms"],
            is_vulnerable=is_suspicious,
            confidence=0.6 if is_suspicious else 0.0,
            evidence={
                "test_type": test_case.metadata.get("test_type"),
                "manipulated_url": test_case.url,
                "response_preview": result["body"][:500],
                "status_code": result["status_code"],
            },
        )

    def analyze(self, results: List[TestResult], context: TestContext) -> Optional[FindingCandidate]:
        vulnerable = [r for r in results if r.is_vulnerable and r.status_code in (200, 201)]
        if not vulnerable:
            return None

        best = vulnerable[0]
        test_type = best.evidence.get("test_type", "unknown")

        return FindingCandidate(
            title="Broken Object Level Authorization (BOLA/IDOR)",
            description=(
                f"The endpoint returned a successful response (HTTP {best.status_code}) "
                f"when accessed with a manipulated object ID ({test_type}). "
                f"This may indicate broken object-level authorization."
            ),
            severity="high",
            confidence="medium",  # Requires manual confirmation of data ownership
            owasp_category="A01:2021 - Broken Access Control",
            owasp_api_category="API1:2023 - Broken Object Level Authorization",
            wstg_category="WSTG-ATHZ-01",
            cwe="CWE-639",
            cvss_score=8.6,
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N",
            impact="An authenticated user can access or modify resources belonging to other users by manipulating object identifiers in API requests.",
            reproduction_steps=(
                f"1. Authenticate as a normal user\n"
                f"2. Send {best.test_case.method} to: {best.test_case.url}\n"
                f"3. Observe HTTP {best.status_code} with data in response\n"
                f"4. Verify the returned data belongs to a different user"
            ),
            remediation=(
                "Implement object-level authorization checks for every resource access. "
                "Verify the authenticated user owns or is authorized to access the requested object. "
                "Use non-sequential, unpredictable IDs (UUIDs) as an additional defense-in-depth measure."
            ),
            references=[
                "https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/",
                "https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/04-Testing_for_Insecure_Direct_Object_References",
            ],
            evidence=best.evidence,
            detected_by="bola_test",
        )

    def collect_evidence(self, result: TestResult) -> dict:
        return {
            "type": "bola",
            "manipulated_url": result.test_case.url,
            "response_status": result.status_code,
            "response_preview": result.response_body[:500],
            "test_type": result.evidence.get("test_type"),
        }
