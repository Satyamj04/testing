"""
Scan, ScanTask, and Asset models.
"""
import uuid
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import String, Text, Integer, ForeignKey, Enum, JSON, Boolean, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base, TimestampMixin


class ScanStatus(str, PyEnum):
    QUEUED = "queued"
    RECON = "recon"
    DISCOVERY = "discovery"
    CRAWLING = "crawling"
    TESTING = "testing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanType(str, PyEnum):
    FULL = "full"
    RECON_ONLY = "recon_only"
    CRAWL_ONLY = "crawl_only"
    SECURITY_TESTS = "security_tests"
    API_SECURITY = "api_security"


class Scan(Base, TimestampMixin):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("targets.id"), nullable=False)
    scan_type: Mapped[ScanType] = mapped_column(Enum(ScanType), default=ScanType.FULL)
    status: Mapped[ScanStatus] = mapped_column(Enum(ScanStatus), default=ScanStatus.QUEUED)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Config & Stats
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    stats: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[str]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[str]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Coverage metrics
    endpoints_discovered: Mapped[int] = mapped_column(Integer, default=0)
    requests_captured: Mapped[int] = mapped_column(Integer, default=0)
    tests_executed: Mapped[int] = mapped_column(Integer, default=0)
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    confirmed_findings: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="scans")
    target: Mapped["Target"] = relationship("Target", back_populates="scans")
    tasks: Mapped[List["ScanTask"]] = relationship("ScanTask", back_populates="scan", cascade="all, delete-orphan")
    http_requests: Mapped[List["HTTPRequest"]] = relationship("HTTPRequest", back_populates="scan")
    findings: Mapped[List["Finding"]] = relationship("Finding", back_populates="scan")
    scanner_results: Mapped[List["ScannerResult"]] = relationship("ScannerResult", back_populates="scan")

    def __repr__(self) -> str:
        return f"<Scan {self.id} [{self.status}]>"


class ScanTask(Base, TimestampMixin):
    __tablename__ = "scan_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)  # recon, browser, scanner, test
    status: Mapped[str] = mapped_column(String(50), default="pending")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    scan: Mapped["Scan"] = relationship("Scan", back_populates="tasks")


class Asset(Base, TimestampMixin):
    """Discovered asset: subdomain, IP, service, API endpoint."""
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("targets.id"), nullable=False)
    scan_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=True)

    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)  # subdomain, ip, service, api
    host: Mapped[str] = mapped_column(String(512), nullable=False)
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    protocol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    technologies: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_in_scope: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str] = mapped_column(String(50), default="recon")

    target: Mapped["Target"] = relationship("Target", back_populates="assets")
