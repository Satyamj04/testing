"""
Unit tests for ScopeValidator.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.services.scope_validator import ScopeValidator, ScopeViolationError
from app.models.scope import Scope


def make_scope(**kwargs) -> Scope:
    s = Scope()
    s.id = "00000000-0000-0000-0000-000000000001"
    s.target_id = "00000000-0000-0000-0000-000000000002"
    s.allowed_domains = kwargs.get("allowed_domains", ["example.com"])
    s.allowed_subdomains = kwargs.get("allowed_subdomains", ["*.example.com"])
    s.allowed_ip_ranges = kwargs.get("allowed_ip_ranges", [])
    s.allowed_ports = kwargs.get("allowed_ports", [])
    s.allowed_protocols = kwargs.get("allowed_protocols", [])
    s.allowed_test_categories = kwargs.get("allowed_test_categories", [])
    s.excluded_domains = kwargs.get("excluded_domains", [])
    s.excluded_paths = kwargs.get("excluded_paths", [])
    s.excluded_methods = kwargs.get("excluded_methods", [])
    s.excluded_content_types = kwargs.get("excluded_content_types", [])
    s.max_requests_per_second = 10
    s.max_concurrent_requests = 5
    return s


class TestScopeValidatorEval:
    """Test the _evaluate method of ScopeValidator directly (no DB needed)."""

    def setup_method(self):
        mock_db = MagicMock()
        self.validator = ScopeValidator(db=mock_db)

    def test_allowed_domain(self):
        scope = make_scope(allowed_domains=["example.com"])
        result = self.validator._evaluate("https://example.com/login", "GET", scope)
        assert result.allowed is True

    def test_allowed_subdomain_wildcard(self):
        scope = make_scope(allowed_domains=[], allowed_subdomains=["*.example.com"])
        result = self.validator._evaluate("https://api.example.com/v1/users", "GET", scope)
        assert result.allowed is True

    def test_blocked_external_domain(self):
        scope = make_scope(allowed_domains=["example.com"])
        result = self.validator._evaluate("https://evil.attacker.com/steal", "GET", scope)
        assert result.allowed is False
        assert "host_not_in_scope" in result.reason

    def test_excluded_path(self):
        scope = make_scope(
            allowed_domains=["example.com"],
            excluded_paths=["/logout", "/admin/delete"]
        )
        result = self.validator._evaluate("https://example.com/logout", "POST", scope)
        assert result.allowed is False
        assert "path_excluded" in result.reason

    def test_excluded_method(self):
        scope = make_scope(
            allowed_domains=["example.com"],
            excluded_methods=["DELETE", "PURGE"]
        )
        result = self.validator._evaluate("https://example.com/resource/1", "DELETE", scope)
        assert result.allowed is False
        assert "method_excluded" in result.reason

    def test_excluded_domain(self):
        scope = make_scope(
            allowed_domains=["example.com"],
            excluded_domains=["staging.example.com"]
        )
        result = self.validator._evaluate("https://staging.example.com/test", "GET", scope)
        assert result.allowed is False
        assert "domain_excluded" in result.reason

    def test_path_prefix_exclusion(self):
        scope = make_scope(
            allowed_domains=["example.com"],
            excluded_paths=["/admin"]
        )
        result = self.validator._evaluate("https://example.com/admin/users", "GET", scope)
        assert result.allowed is False

    def test_allowed_ip_range(self):
        scope = make_scope(
            allowed_domains=[],
            allowed_ip_ranges=["192.168.1.0/24"]
        )
        result = self.validator._evaluate("http://192.168.1.50/api", "GET", scope)
        assert result.allowed is True

    def test_blocked_ip_outside_range(self):
        scope = make_scope(
            allowed_domains=[],
            allowed_ip_ranges=["192.168.1.0/24"]
        )
        result = self.validator._evaluate("http://10.0.0.1/api", "GET", scope)
        assert result.allowed is False

    def test_invalid_url(self):
        scope = make_scope()
        result = self.validator._evaluate("not-a-url", "GET", scope)
        assert result.allowed is False

    def test_no_domains_configured_blocks_everything(self):
        scope = make_scope(allowed_domains=[], allowed_subdomains=[], allowed_ip_ranges=[])
        result = self.validator._evaluate("https://example.com/test", "GET", scope)
        assert result.allowed is False

    def test_path_matches_regex(self):
        scope = make_scope(
            allowed_domains=["example.com"],
            excluded_paths=[r"/payment/.*"]
        )
        result = self.validator._evaluate("https://example.com/payment/checkout", "POST", scope)
        assert result.allowed is False


@pytest.mark.asyncio
async def test_enforce_raises_on_violation():
    """Test that enforce() raises ScopeViolationError."""
    mock_db = AsyncMock()
    validator = ScopeValidator(db=mock_db)

    mock_scope = make_scope(allowed_domains=["example.com"])
    mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=mock_scope)

    with pytest.raises(ScopeViolationError):
        await validator.enforce(
            url="https://evil.com/steal",
            method="GET",
            target_id="00000000-0000-0000-0000-000000000002",
        )
