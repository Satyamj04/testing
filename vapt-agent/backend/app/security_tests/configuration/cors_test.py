"""
CORS Configuration Test - OWASP A01:2021 Broken Access Control
Tests for overly permissive CORS policies.
"""
from typing import List, Optional
from app.security_tests.base import SecurityTest, TestContext, TestCase, TestResult, FindingCandidate


class CORSTest(SecurityTest):
    name = "CORS Configuration Test"
    description = "Tests for misconfigured Cross-Origin Resource Sharing (CORS) policies"
    category = "configuration"
    owasp_top10 = "A01:2021 - Broken Access Control"
    wstg = "WSTG-CONF-07"
    cwe = "CWE-942"

    EVIL_ORIGINS = [
        "https://evil.attacker.com",
        "null",
        "https://trusted.com.evil.com",
    ]

    def can_test(self, endpoint: dict, context: TestContext) -> bool:
        return True

    def prepare_test(self, endpoint: dict, context: TestContext) -> List[TestCase]:
        url = f"{context.target_url.rstrip('/')}{endpoint.get('path', '/')}"
        cases = []
        for origin in self.EVIL_ORIGINS:
            cases.append(TestCase(
                test_id=f"cors_{endpoint.get('id', 'root')}_{origin}",
                name=f"CORS Test - {origin}",
                url=url,
                method=endpoint.get("method", "GET"),
                headers={
                    **(context.auth_headers or {}),
                    "Origin": origin,
                },
                metadata={"test_origin": origin},
            ))
        return cases

    async def execute(self, test_case: TestCase, context: TestContext) -> TestResult:
        result = await self._safe_request(
            url=test_case.url,
            method=test_case.method,
            target_id=context.target_id,
            headers=test_case.headers,
        )

        resp_headers_lower = {k.lower(): v for k, v in result["headers"].items()}
        acao = resp_headers_lower.get("access-control-allow-origin", "")
        acac = resp_headers_lower.get("access-control-allow-credentials", "")
        test_origin = test_case.metadata.get("test_origin", "")

        is_vulnerable = False
        issues = []

        if acao == "*" and acac.lower() == "true":
            is_vulnerable = True
            issues.append("Wildcard ACAO with credentials allowed (invalid but dangerous if supported)")

        if acao == test_origin and test_origin not in ("null",):
            is_vulnerable = True
            issues.append(f"Arbitrary origin '{test_origin}' reflected in ACAO")

        if acao == "null":
            is_vulnerable = True
            issues.append("ACAO: null is dangerous (allows sandboxed iframes)")

        return TestResult(
            test_id=test_case.test_id,
            test_case=test_case,
            status_code=result["status_code"],
            response_headers=result["headers"],
            response_body=result["body"][:500],
            duration_ms=result["duration_ms"],
            is_vulnerable=is_vulnerable,
            confidence=0.85 if is_vulnerable else 0.0,
            evidence={
                "test_origin": test_origin,
                "acao_header": acao,
                "acac_header": acac,
                "issues": issues,
            },
        )

    def analyze(self, results: List[TestResult], context: TestContext) -> Optional[FindingCandidate]:
        vulnerable_results = [r for r in results if r.is_vulnerable]
        if not vulnerable_results:
            return None

        best = max(vulnerable_results, key=lambda r: r.confidence)
        issues = best.evidence.get("issues", [])
        issue_text = "\n".join(f"- {i}" for i in issues)

        return FindingCandidate(
            title="CORS Misconfiguration - Arbitrary Origin Allowed",
            description=f"The application has a misconfigured CORS policy:\n\n{issue_text}\n\nTest origin used: {best.evidence.get('test_origin')}",
            severity="high",
            confidence="high",
            owasp_category="A01:2021 - Broken Access Control",
            wstg_category="WSTG-CONF-07",
            cwe="CWE-942",
            cvss_score=8.1,
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N",
            impact="An attacker can craft a malicious website that makes authenticated cross-origin requests to the API, reading sensitive data.",
            reproduction_steps=(
                f"1. Send a request to {context.target_url} with Origin: {best.evidence.get('test_origin')}\n"
                f"2. Observe Access-Control-Allow-Origin reflects the evil origin\n"
                f"3. A malicious page can now make credentialed cross-origin requests"
            ),
            remediation="Validate the Origin header against an allowlist. Never reflect arbitrary origins. Set ACAO only for trusted domains.",
            references=[
                "https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/11-Client_Side_Testing/07-Testing_Cross_Origin_Resource_Sharing",
                "https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS",
            ],
            evidence=best.evidence,
            detected_by="cors_test",
        )

    def collect_evidence(self, result: TestResult) -> dict:
        return {
            "type": "cors",
            "url": result.test_case.url,
            "test_origin": result.evidence.get("test_origin"),
            "acao_header": result.evidence.get("acao_header"),
            "acac_header": result.evidence.get("acac_header"),
            "issues": result.evidence.get("issues", []),
        }
