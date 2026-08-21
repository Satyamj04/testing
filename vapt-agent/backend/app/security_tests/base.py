"""
SecurityTest base interface.
All security tests MUST implement this interface.
Tests MUST use ScopeValidator before executing any HTTP request.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Any
from enum import Enum


class TestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestContext:
    """Context provided to every security test."""
    scan_id: str
    target_id: str
    target_url: str
    endpoint_id: Optional[str] = None
    endpoint_method: Optional[str] = None
    endpoint_path: Optional[str] = None
    auth_profile_id: Optional[str] = None
    auth_headers: Optional[dict] = None
    scope_id: Optional[str] = None
    extra: dict = field(default_factory=dict)


@dataclass
class TestCase:
    """A single test case to execute."""
    test_id: str
    name: str
    url: str
    method: str
    headers: dict = field(default_factory=dict)
    body: Optional[Any] = None
    expected_behavior: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class TestResult:
    """Result of executing a test case."""
    test_id: str
    test_case: TestCase
    status_code: int
    response_headers: dict
    response_body: str
    duration_ms: float
    is_vulnerable: bool = False
    confidence: float = 0.0
    evidence: dict = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class FindingCandidate:
    """A candidate finding produced by a security test."""
    title: str
    description: str
    severity: str  # critical, high, medium, low, informational
    confidence: str  # low, medium, high
    owasp_category: Optional[str] = None
    owasp_api_category: Optional[str] = None
    wstg_category: Optional[str] = None
    cwe: Optional[str] = None
    cvss_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    impact: Optional[str] = None
    reproduction_steps: Optional[str] = None
    remediation: Optional[str] = None
    references: List[str] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)
    detected_by: str = "custom_test"


class SecurityTest(ABC):
    """
    Base interface for all VAPT security tests.

    Architecture:
        AI decides which test to run
        SecurityTest.can_test() confirms applicability
        SecurityTest.prepare_test() generates test cases
        SecurityTest.execute() runs the test with scope validation
        SecurityTest.analyze() determines vulnerability presence
        SecurityTest.collect_evidence() builds the evidence record
    """

    # Test metadata (define in subclasses)
    name: str = "Unnamed Test"
    description: str = ""
    category: str = "general"
    owasp_top10: Optional[str] = None
    owasp_api: Optional[str] = None
    wstg: Optional[str] = None
    cwe: Optional[str] = None

    def __init__(self, scope_validator, db=None):
        self.scope_validator = scope_validator
        self.db = db

    @abstractmethod
    def can_test(self, endpoint: dict, context: TestContext) -> bool:
        """Return True if this test is applicable to the given endpoint."""
        ...

    @abstractmethod
    def prepare_test(self, endpoint: dict, context: TestContext) -> List[TestCase]:
        """Generate test cases for the given endpoint."""
        ...

    @abstractmethod
    async def execute(self, test_case: TestCase, context: TestContext) -> TestResult:
        """Execute the test case. MUST call scope_validator before any HTTP request."""
        ...

    @abstractmethod
    def analyze(self, results: List[TestResult], context: TestContext) -> Optional[FindingCandidate]:
        """Analyze test results and return a FindingCandidate if vulnerable."""
        ...

    @abstractmethod
    def collect_evidence(self, result: TestResult) -> dict:
        """Build a structured evidence record from a test result."""
        ...

    async def _safe_request(
        self,
        url: str,
        method: str,
        target_id: str,
        headers: dict = None,
        body=None,
        timeout: float = 15.0,
    ) -> Optional[dict]:
        """
        Execute an HTTP request only after passing scope validation.
        NEVER bypass this method.
        """
        import httpx
        import time

        await self.scope_validator.enforce(
            url=url,
            method=method,
            target_id=target_id,
            action=f"security_test_{self.category}",
        )

        headers = headers or {}
        start = time.monotonic()
        async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
            resp = await client.request(method=method, url=url, headers=headers, content=body)
            duration = (time.monotonic() - start) * 1000

        return {
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": resp.text,
            "duration_ms": duration,
        }
