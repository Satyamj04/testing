"""
Security Headers Test - OWASP A05:2021 Security Misconfiguration
Tests for missing or misconfigured security headers.
"""
from typing import List, Optional
from app.security_tests.base import SecurityTest, TestContext, TestCase, TestResult, FindingCandidate


REQUIRED_HEADERS = {
    "strict-transport-security": {
        "description": "HTTP Strict Transport Security (HSTS) not set",
        "severity": "medium",
        "remediation": "Add: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload",
    },
    "content-security-policy": {
        "description": "Content Security Policy (CSP) not configured",
        "severity": "medium",
        "remediation": "Configure a strict Content-Security-Policy header",
    },
    "x-content-type-options": {
        "description": "X-Content-Type-Options not set to 'nosniff'",
        "severity": "low",
        "remediation": "Add: X-Content-Type-Options: nosniff",
    },
    "x-frame-options": {
        "description": "X-Frame-Options not configured (clickjacking risk)",
        "severity": "medium",
        "remediation": "Add: X-Frame-Options: DENY or SAMEORIGIN",
    },
    "referrer-policy": {
        "description": "Referrer-Policy not set",
        "severity": "low",
        "remediation": "Add: Referrer-Policy: strict-origin-when-cross-origin",
    },
    "permissions-policy": {
        "description": "Permissions-Policy header not configured",
        "severity": "informational",
        "remediation": "Configure Permissions-Policy to restrict browser features",
    },
}

DISCLOSURE_HEADERS = [
    "server", "x-powered-by", "x-aspnet-version", "x-aspnetmvc-version",
    "x-generator", "via",
]


class SecurityHeadersTest(SecurityTest):
    name = "Security Headers Check"
    description = "Tests for missing or misconfigured HTTP security headers"
    category = "configuration"
    owasp_top10 = "A05:2021 - Security Misconfiguration"
    owasp_api = "API8:2023 - Security Misconfiguration"
    wstg = "WSTG-CONF-12"
    cwe = "CWE-693"

    def can_test(self, endpoint: dict, context: TestContext) -> bool:
        return endpoint.get("method") == "GET"

    def prepare_test(self, endpoint: dict, context: TestContext) -> List[TestCase]:
        url = f"{context.target_url.rstrip('/')}{endpoint.get('path', '/')}"
        return [TestCase(
            test_id=f"sec_headers_{endpoint.get('id', 'root')}",
            name="Security Headers Check",
            url=url,
            method="GET",
            headers=context.auth_headers or {},
        )]

    async def execute(self, test_case: TestCase, context: TestContext) -> TestResult:
        import time
        result = await self._safe_request(
            url=test_case.url,
            method=test_case.method,
            target_id=context.target_id,
            headers=test_case.headers,
        )

        resp_headers_lower = {k.lower(): v for k, v in result["headers"].items()}

        missing_headers = []
        for header, info in REQUIRED_HEADERS.items():
            if header not in resp_headers_lower:
                missing_headers.append({"header": header, **info})

        disclosure_headers = []
        for header in DISCLOSURE_HEADERS:
            if header in resp_headers_lower:
                disclosure_headers.append({
                    "header": header,
                    "value": resp_headers_lower[header],
                })

        is_vulnerable = len(missing_headers) > 0 or len(disclosure_headers) > 0

        return TestResult(
            test_id=test_case.test_id,
            test_case=test_case,
            status_code=result["status_code"],
            response_headers=result["headers"],
            response_body=result["body"][:1000],
            duration_ms=result["duration_ms"],
            is_vulnerable=is_vulnerable,
            confidence=0.9,
            evidence={
                "missing_security_headers": missing_headers,
                "disclosure_headers": disclosure_headers,
                "url_tested": test_case.url,
            },
        )

    def analyze(self, results: List[TestResult], context: TestContext) -> Optional[FindingCandidate]:
        result = results[0] if results else None
        if not result or not result.is_vulnerable:
            return None

        missing = result.evidence.get("missing_security_headers", [])
        disclosure = result.evidence.get("disclosure_headers", [])

        # Determine highest severity
        severities = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}
        max_sev = "informational"
        for h in missing:
            if severities.get(h["severity"], 0) > severities[max_sev]:
                max_sev = h["severity"]

        findings_list = "\n".join([f"- Missing: {h['header']}: {h['description']}" for h in missing])
        if disclosure:
            findings_list += "\n" + "\n".join([f"- Information disclosure: {h['header']}: {h['value']}" for h in disclosure])

        return FindingCandidate(
            title="Security Headers Misconfiguration",
            description=f"The following security header issues were detected:\n\n{findings_list}",
            severity=max_sev,
            confidence="high",
            owasp_category="A05:2021 - Security Misconfiguration",
            owasp_api_category="API8:2023 - Security Misconfiguration",
            wstg_category="WSTG-CONF-12",
            cwe="CWE-693",
            cvss_score=5.3,
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
            impact="Missing security headers may allow cross-site scripting, clickjacking, MIME-type sniffing, and information disclosure attacks.",
            remediation="Add all required security headers. Remove server version disclosure headers.",
            references=[
                "https://owasp.org/www-project-secure-headers/",
                "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers",
            ],
            evidence=result.evidence,
            detected_by="security_headers_test",
        )

    def collect_evidence(self, result: TestResult) -> dict:
        return {
            "type": "security_headers",
            "url": result.test_case.url,
            "response_headers": result.response_headers,
            "missing_headers": result.evidence.get("missing_security_headers", []),
            "disclosure_headers": result.evidence.get("disclosure_headers", []),
        }
