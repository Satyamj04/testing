"""
Endpoint, Parameter, and AuthProfile models.
"""
import uuid
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import String, Text, Integer, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base, TimestampMixin


class AuthType(str, PyEnum):
    JWT = "jwt"
    SESSION_COOKIE = "session_cookie"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    OIDC = "oidc"
    BASIC = "basic"
    CUSTOM_HEADER = "custom_header"
    NONE = "none"


class Endpoint(Base, TimestampMixin):
    """Discovered application endpoint with full context."""
    __tablename__ = "endpoints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("targets.id"), nullable=False)
    scan_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=True)

    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    host: Mapped[str] = mapped_column(String(512), nullable=False)
    scheme: Mapped[str] = mapped_column(String(10), default="https")
    content_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    group: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # e.g., "Contracts", "Users"

    # Auth context
    requires_auth: Mapped[bool] = mapped_column(Boolean, default=True)
    observed_roles: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)

    # Examples
    request_examples: Mapped[Optional[List[dict]]] = mapped_column(JSON, default=list)
    response_examples: Mapped[Optional[List[dict]]] = mapped_column(JSON, default=list)

    # Source & testing state
    source: Mapped[str] = mapped_column(String(50), default="crawler")
    is_tested: Mapped[bool] = mapped_column(Boolean, default=False)
    test_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    target: Mapped["Target"] = relationship("Target", back_populates="endpoints")
    parameters: Mapped[List["Parameter"]] = relationship("Parameter", back_populates="endpoint", cascade="all, delete-orphan")
    findings: Mapped[List["Finding"]] = relationship("Finding", back_populates="endpoint")

    def __repr__(self) -> str:
        return f"<Endpoint {self.method} {self.path}>"


class Parameter(Base, TimestampMixin):
    """Endpoint parameter: path, query, header, or body."""
    __tablename__ = "parameters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("endpoints.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(20), nullable=False)  # path, query, header, body
    data_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    example_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    endpoint: Mapped["Endpoint"] = relationship("Endpoint", back_populates="parameters")


class AuthProfile(Base, TimestampMixin):
    """Authentication profile for testing as a specific user/role."""
    __tablename__ = "auth_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("targets.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "Admin", "Normal User"
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    auth_type: Mapped[AuthType] = mapped_column(Enum(AuthType), default=AuthType.NONE)

    # Credentials stored encrypted / masked
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Never store password in plain text - hash or encrypt
    credentials_storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Auth headers/tokens (masked in API responses)
    auth_header_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    auth_header_value_storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Login configuration
    login_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    login_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    target: Mapped["Target"] = relationship("Target", back_populates="auth_profiles")
