"""
Project and Target models.
"""
import uuid
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import String, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base, TimestampMixin


class ProjectStatus(str, PyEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"


class TargetStatus(str, PyEnum):
    PENDING = "pending"
    ACTIVE = "active"
    SCANNING = "scanning"
    COMPLETED = "completed"
    PAUSED = "paused"


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    client_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="projects")
    targets: Mapped[List["Target"]] = relationship("Target", back_populates="project", cascade="all, delete-orphan")
    scans: Mapped[List["Scan"]] = relationship("Scan", back_populates="project")
    reports: Mapped[List["Report"]] = relationship("Report", back_populates="project")

    def __repr__(self) -> str:
        return f"<Project {self.name}>"


class Target(Base, TimestampMixin):
    __tablename__ = "targets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TargetStatus] = mapped_column(Enum(TargetStatus), default=TargetStatus.PENDING)
    is_authorized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    authorization_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="targets")
    scope: Mapped[Optional["Scope"]] = relationship("Scope", back_populates="target", uselist=False, cascade="all, delete-orphan")
    assets: Mapped[List["Asset"]] = relationship("Asset", back_populates="target", cascade="all, delete-orphan")
    endpoints: Mapped[List["Endpoint"]] = relationship("Endpoint", back_populates="target")
    scans: Mapped[List["Scan"]] = relationship("Scan", back_populates="target")
    auth_profiles: Mapped[List["AuthProfile"]] = relationship("AuthProfile", back_populates="target", cascade="all, delete-orphan")
    http_requests: Mapped[List["HTTPRequest"]] = relationship("HTTPRequest", back_populates="target")
    findings: Mapped[List["Finding"]] = relationship("Finding", back_populates="target")

    def __repr__(self) -> str:
        return f"<Target {self.url}>"
