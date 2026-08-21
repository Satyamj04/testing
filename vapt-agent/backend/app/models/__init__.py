"""
Models package - import all models so Alembic can discover them.
"""
from app.models.user import User, UserRole
from app.models.project import Project, Target, ProjectStatus, TargetStatus
from app.models.scope import Scope
from app.models.http_traffic import HTTPRequest, Replay, HTTPMethod
from app.models.scan import Scan, ScanTask, Asset, ScanStatus, ScanType
from app.models.endpoint import Endpoint, Parameter, AuthProfile, AuthType
from app.models.finding import Finding, FindingEvidence, ValidationRun, ScannerResult, Severity, FindingStatus, ValidationMethod
from app.models.audit import AuditLog, AIRun, Report, BrowserSession

__all__ = [
    "User", "UserRole",
    "Project", "Target", "ProjectStatus", "TargetStatus",
    "Scope",
    "HTTPRequest", "Replay", "HTTPMethod",
    "Scan", "ScanTask", "Asset", "ScanStatus", "ScanType",
    "Endpoint", "Parameter", "AuthProfile", "AuthType",
    "Finding", "FindingEvidence", "ValidationRun", "ScannerResult",
    "Severity", "FindingStatus", "ValidationMethod",
    "AuditLog", "AIRun", "Report", "BrowserSession",
]
