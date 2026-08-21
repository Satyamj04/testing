"""
Finding, FindingEvidence, ValidationRun, and ScannerResult models.
"""
import uuid
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import String, Text, Integer, ForeignKey, Enum, JSON, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base, TimestampMixin


class Severity(str, PyEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class FindingStatus(str, PyEnum):
    SUSPECTED = "suspected"
    VALIDATING = "validating"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class ValidationMethod(str, PyEnum):
    REPRODUCIBLE = "reproducible"
    SCANNER_CONFIRMED = "scanner_confirmed"
    MANUAL = "manual"
    AUTOMATED = "automated"


class Finding(Base, TimestampMixin):
    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("targets.id"), nullable=False)
    scan_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=True)
    endpoint_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("endpoints.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), nullable=False)
    status: Mapped[FindingStatus] = mapped_column(Enum(FindingStatus), default=FindingStatus.SUSPECTED)
    confidence: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high

    # HTTP context
    method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    parameter: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # OWASP / Standards mapping
    owasp_category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    owasp_api_category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    wstg_category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cwe: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cvss_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cvss_vector: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Content
    impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reproduction_steps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remediation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    references: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)

    # Source
    detected_by: Mapped[str] = mapped_column(String(100), nullable=False)  # scanner, custom_test, ai
    is_false_positive: Mapped[bool] = mapped_column(Boolean, default=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    duplicate_of_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("findings.id"), nullable=True)

    # Relationships
    target: Mapped["Target"] = relationship("Target", back_populates="findings")
    scan: Mapped[Optional["Scan"]] = relationship("Scan", back_populates="findings")
    endpoint: Mapped[Optional["Endpoint"]] = relationship("Endpoint", back_populates="findings")
    evidence: Mapped[List["FindingEvidence"]] = relationship("FindingEvidence", back_populates="finding", cascade="all, delete-orphan")
    validation_runs: Mapped[List["ValidationRun"]] = relationship("ValidationRun", back_populates="finding", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Finding [{self.severity}] {self.title} [{self.status}]>"


class FindingEvidence(Base, TimestampMixin):
    """Evidence attached to a finding."""
    __tablename__ = "finding_evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    finding_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("findings.id"), nullable=False)
    http_request_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("http_requests.id"), nullable=True)

    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)  # request, response, screenshot, diff, scanner_output
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Inline data for small evidence
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Large evidence in MinIO
    storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    auth_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("auth_profiles.id"), nullable=True)

    finding: Mapped["Finding"] = relationship("Finding", back_populates="evidence")
    http_request: Mapped[Optional["HTTPRequest"]] = relationship("HTTPRequest", back_populates="evidence")


class ValidationRun(Base, TimestampMixin):
    """Tracks each validation attempt for a finding."""
    __tablename__ = "validation_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    finding_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("findings.id"), nullable=False)

    validation_method: Mapped[ValidationMethod] = mapped_column(Enum(ValidationMethod), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # confirmed, rejected, needs_review
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)

    finding: Mapped["Finding"] = relationship("Finding", back_populates="validation_runs")


class ScannerResult(Base, TimestampMixin):
    """Normalized result from an external scanner (Nmap, ZAP, Nuclei)."""
    __tablename__ = "scanner_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=True)

    scanner: Mapped[str] = mapped_column(String(50), nullable=False)  # nmap, zap, nuclei
    target: Mapped[str] = mapped_column(String(512), nullable=False)
    endpoint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    raw_result_storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    finding_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("findings.id"), nullable=True)

    scan: Mapped[Optional["Scan"]] = relationship("Scan", back_populates="scanner_results")
