"""
HTTP Request and Response models (stored in PostgreSQL for metadata,
large bodies stored in MinIO).
"""
import uuid
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import String, Text, Integer, ForeignKey, Enum, JSON, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base, TimestampMixin


class HTTPMethod(str, PyEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"


class HTTPRequest(Base, TimestampMixin):
    __tablename__ = "http_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("targets.id"), nullable=False)
    scan_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=True)

    # Request metadata
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    host: Mapped[str] = mapped_column(String(512), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    query_string: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scheme: Mapped[str] = mapped_column(String(10), default="https")
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    http_version: Mapped[str] = mapped_column(String(10), default="HTTP/1.1")

    # Headers (masked)
    request_headers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    request_body_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Large body stored in MinIO
    request_body_storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Response metadata
    response_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_headers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    response_body_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body_storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    response_content_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Context
    auth_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("auth_profiles.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="proxy")  # proxy, browser, scanner, repeater
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    target: Mapped["Target"] = relationship("Target", back_populates="http_requests")
    scan: Mapped[Optional["Scan"]] = relationship("Scan", back_populates="http_requests")
    auth_profile: Mapped[Optional["AuthProfile"]] = relationship("AuthProfile")
    replays: Mapped[List["Replay"]] = relationship("Replay", back_populates="original_request")
    evidence: Mapped[List["FindingEvidence"]] = relationship("FindingEvidence", back_populates="http_request")

    def __repr__(self) -> str:
        return f"<HTTPRequest {self.method} {self.path} [{self.response_status}]>"


class Replay(Base, TimestampMixin):
    """Stores replayed/modified requests and their responses."""
    __tablename__ = "replays"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("http_requests.id"), nullable=False)

    # Modified request
    modified_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    modified_method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    modified_headers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    modified_body_storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    modification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Replay response
    response_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_headers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    response_body_storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    original_request: Mapped["HTTPRequest"] = relationship("HTTPRequest", back_populates="replays")
