"""
Scope model - defines what is allowed to be tested for a target.
"""
import uuid
from typing import Optional, List

from sqlalchemy import String, Text, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.core.database import Base, TimestampMixin


class Scope(Base, TimestampMixin):
    """
    Scope configuration for a target.
    Defines exactly what is in and out of scope for testing.
    The ScopeValidator reads this model before EVERY test/request.
    """
    __tablename__ = "scopes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("targets.id"), unique=True, nullable=False)

    # ── Allowed ──────────────────────────────────────────────────────────────
    allowed_domains: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    allowed_subdomains: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    allowed_ip_ranges: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    allowed_ports: Mapped[Optional[List[int]]] = mapped_column(JSON, default=list)
    allowed_protocols: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    allowed_test_categories: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)

    # ── Excluded ─────────────────────────────────────────────────────────────
    excluded_domains: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    excluded_paths: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    excluded_methods: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    excluded_content_types: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)

    # ── Rate Limits ───────────────────────────────────────────────────────────
    max_requests_per_second: Mapped[Optional[int]] = mapped_column(Integer, default=10)
    max_concurrent_requests: Mapped[Optional[int]] = mapped_column(Integer, default=5)

    # ── Notes ─────────────────────────────────────────────────────────────────
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    target: Mapped["Target"] = relationship("Target", back_populates="scope")

    def __repr__(self) -> str:
        return f"<Scope for target {self.target_id}>"
