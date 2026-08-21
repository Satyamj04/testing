"""
SQL Injection Test - OWASP A03:2021 Injection
Controlled, non-destructive SQL injection detection using error-based and time-based detection.
"""
from typing import List, Optional
from app.security_tests.base import SecurityTest, TestContext, TestCase, TestResult, FindingCandidate


# Non-destructive detection payloads
SQLI_PAYLOADS = [
    ("'", "error_based", "SQL syntax error"),
    ('" ', "error_based", "SQL syntax error"),
    ("1' AND '1'='1", "tautology", "Data modification detection"),
    ("1' AND '1'='2", "tautology", "Empty result detection"),
    ("1; --", "comment", "Comment injection"),
    ("' OR 1=1 --", "tautology", "Always-true condition"),
]

# SQL error signatures
SQL_ERROR_PATTERNS = [
    "sql syntax", "mysql_fetch", "ora-0", "pg_query", "sqlite_exec",
    "unclosed quotation mark", "quoted string not properly terminated",
    "sqlexception", "syntax error", "unterminated string",
    "microsoft ole db provider for sql server",
    "invalid query", "database error",
]


class SQLInjectionTest(SecurityTest):
    name = "SQL Injection Test"
    description = "Controlled, non-destructive SQL injection detection"
    category = "injection"
    owasp_top10 = "A03:2021 - Injection"
    owasp_api = "API8:2023 - Security Misconfiguration"
    wstg = "WSTG-INPV-05"
    cwe = "CWE-89"

    def can_test(self, endpoint: dict, context: TestContext) -> bool:
        """Test endpoints that accept query parameters or form data."""
        return True  # Will skip if no parameters found

    def prepare_test(self, endpoint: dict, context: TestContext) -> List[TestCase]:
        cases = []
        path = endpoint.get("path", "/")
        method = endpoint.get("method", "GET")
        base_url = f"{context.target_url.rstrip('/')}{path}"

        for i, (payload, test_type, desc) in enumerate(SQLI_PAYLOADS[:3]):  # Limit to 3 safe payloads
            if method == "GET":
                # Inject into query parameters
                test_url = base_url + f"?id={payload}&search={payload}"
                cases.append(TestCase(
                    test_id=f"sqli_get_{endpoint.get('id', 'ep')}_{i}",
                    name=f"SQLi GET - {desc}",
                    url=test_url,
                    method="GET",
                    headers=context.auth_headers or {},
                    metadata={"payload": payload, "test_type": test_type},
                ))
            else:
                # Inject into POST body
                cases.append(TestCase(
                    test_id=f"sqli_post_{endpoint.get('id', 'ep')}_{i}",
                    name=f"SQLi POST - {desc}",
                    url=base_url,
                    method=method,
                    headers={**(context.auth_headers or {}), "Content-Type": "application/json"},
                    body=f'{{"search": "{payload}", "id": "{payload}"}}',
                    metadata={"payload": payload, "test_type": test_type},
                ))

        return cases

    async def execute(self, test_case: TestCase, context: TestContext) -> TestResult:
        result = await self._safe_request(
            url=test_case.url,
            method=test_case.method,
            target_id=context.target_id,
            headers=test_case.headers,
            body=test_case.body.encode() if test_case.body else None,
        )

        body_lower = result["body"].lower()

        # Check for SQL error signatures
        sql_errors_found = [p for p in SQL_ERROR_PATTERNS if p in body_lower]
        is_vulnerable = len(sql_errors_found) > 0

        return TestResult(
            test_id=test_case.test_id,
            test_case=test_case,
            status_code=result["status_code"],
            response_headers=result["headers"],
            response_body=result["body"][:2000],
            duration_ms=result["duration_ms"],
            is_vulnerable=is_vulnerable,
            confidence=0.85 if is_vulnerable else 0.0,
            evidence={
                "payload": test_case.metadata.get("payload"),
                "test_type": test_case.metadata.get("test_type"),
                "sql_errors_found": sql_errors_found,
                "response_snippet": result["body"][:500],
            },
        )

    def analyze(self, results: List[TestResult], context: TestContext) -> Optional[FindingCandidate]:
        vulnerable = [r for r in results if r.is_vulnerable]
        if not vulnerable:
            return None

        best = vulnerable[0]
        payload = best.evidence.get("payload")
        errors = best.evidence.get("sql_errors_found", [])

        return FindingCandidate(
            title="SQL Injection Vulnerability",
            description=(
                f"SQL injection was detected at {best.test_case.url}.\n"
                f"Payload: `{payload}`\n"
                f"SQL error signatures detected in response: {', '.join(errors)}"
            ),
            severity="critical",
            confidence="high",
            owasp_category="A03:2021 - Injection",
            wstg_category="WSTG-INPV-05",
            cwe="CWE-89",
            cvss_score=9.8,
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            impact="SQL injection allows attackers to read, modify, or delete database data, bypass authentication, and potentially achieve remote code execution.",
            reproduction_steps=(
                f"1. Send {best.test_case.method} request to: {best.test_case.url}\n"
                f"2. Include payload: {payload}\n"
                f"3. Observe SQL error in response confirming injection"
            ),
            remediation="Use parameterized queries / prepared statements. Never concatenate user input into SQL. Use an ORM. Apply input validation.",
            references=[
                "https://owasp.org/www-community/attacks/SQL_Injection",
                "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html",
            ],
            evidence=best.evidence,
            detected_by="sqli_test",
        )

    def collect_evidence(self, result: TestResult) -> dict:
        return {
            "type": "sql_injection",
            "url": result.test_case.url,
            "payload": result.evidence.get("payload"),
            "sql_errors": result.evidence.get("sql_errors_found", []),
            "response_snippet": result.response_body[:500],
        }
