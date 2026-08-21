"""
Pydantic schemas for Auth, User, Project, Target, Scope.
"""
from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, validator


# ── Auth ─────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Project ───────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    client_name: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    client_name: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    client_name: Optional[str]
    status: str
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    target_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ── Target ────────────────────────────────────────────────────────────────────

class TargetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1)
    description: Optional[str] = None
    is_authorized: bool = False
    authorization_notes: Optional[str] = None


class TargetUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    is_authorized: Optional[bool] = None
    authorization_notes: Optional[str] = None
    status: Optional[str] = None


class TargetResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    url: str
    description: Optional[str]
    status: str
    is_authorized: bool
    authorization_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Scope ─────────────────────────────────────────────────────────────────────

class ScopeCreate(BaseModel):
    allowed_domains: List[str] = Field(default_factory=list)
    allowed_subdomains: List[str] = Field(default_factory=list)
    allowed_ip_ranges: List[str] = Field(default_factory=list)
    allowed_ports: List[int] = Field(default_factory=list)
    allowed_protocols: List[str] = Field(default_factory=list, description="e.g. ['http', 'https']")
    allowed_test_categories: List[str] = Field(default_factory=list)
    excluded_domains: List[str] = Field(default_factory=list)
    excluded_paths: List[str] = Field(default_factory=list)
    excluded_methods: List[str] = Field(default_factory=list)
    excluded_content_types: List[str] = Field(default_factory=list)
    max_requests_per_second: int = Field(default=10, ge=1, le=100)
    max_concurrent_requests: int = Field(default=5, ge=1, le=20)
    notes: Optional[str] = None


class ScopeUpdate(ScopeCreate):
    pass


class ScopeResponse(BaseModel):
    id: UUID
    target_id: UUID
    allowed_domains: List[str]
    allowed_subdomains: List[str]
    allowed_ip_ranges: List[str]
    allowed_ports: List[int]
    allowed_protocols: List[str]
    allowed_test_categories: List[str]
    excluded_domains: List[str]
    excluded_paths: List[str]
    excluded_methods: List[str]
    excluded_content_types: List[str]
    max_requests_per_second: int
    max_concurrent_requests: int
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ScopeCheckRequest(BaseModel):
    url: str
    method: str = "GET"


class ScopeCheckResponse(BaseModel):
    allowed: bool
    reason: str
    url: str
    method: str


# ── Scan ──────────────────────────────────────────────────────────────────────

class ScanCreate(BaseModel):
    target_id: UUID
    scan_type: str = "full"
    config: Optional[dict] = None


class ScanResponse(BaseModel):
    id: UUID
    project_id: UUID
    target_id: UUID
    scan_type: str
    status: str
    endpoints_discovered: int
    requests_captured: int
    tests_executed: int
    findings_count: int
    confirmed_findings: int
    started_at: Optional[Any]
    completed_at: Optional[Any]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Finding ───────────────────────────────────────────────────────────────────

class FindingResponse(BaseModel):
    id: UUID
    target_id: UUID
    scan_id: Optional[UUID]
    title: str
    description: str
    severity: str
    status: str
    confidence: str
    method: Optional[str]
    parameter: Optional[str]
    owasp_category: Optional[str]
    owasp_api_category: Optional[str]
    wstg_category: Optional[str]
    cwe: Optional[str]
    cvss_score: Optional[float]
    cvss_vector: Optional[str]
    impact: Optional[str]
    reproduction_steps: Optional[str]
    remediation: Optional[str]
    references: Optional[List[str]]
    detected_by: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── HTTPRequest ───────────────────────────────────────────────────────────────

class HTTPRequestResponse(BaseModel):
    id: UUID
    target_id: UUID
    method: str
    url: str
    host: str
    path: str
    query_string: Optional[str]
    scheme: str
    request_headers: Optional[dict]
    response_status: Optional[int]
    response_headers: Optional[dict]
    response_content_type: Optional[str]
    source: str
    duration_ms: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Replay ────────────────────────────────────────────────────────────────────

class ReplayCreate(BaseModel):
    original_request_id: UUID
    modified_url: Optional[str] = None
    modified_method: Optional[str] = None
    modified_headers: Optional[dict] = None
    modified_body: Optional[str] = None
    modification_notes: Optional[str] = None


class ReplayResponse(BaseModel):
    id: UUID
    original_request_id: UUID
    response_status: Optional[int]
    response_headers: Optional[dict]
    duration_ms: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ── AI ────────────────────────────────────────────────────────────────────────

class AIChatRequest(BaseModel):
    message: str
    scan_id: Optional[UUID] = None
    finding_id: Optional[UUID] = None
    context: Optional[dict] = None


class AIChatResponse(BaseModel):
    response: str
    tool_calls: Optional[List[dict]] = None
    tokens_used: Optional[int] = None


class AIAnalyzeRequest(BaseModel):
    scan_id: UUID
    focus: Optional[str] = None  # "findings", "coverage", "risk"


# ── Report ────────────────────────────────────────────────────────────────────

class ReportCreate(BaseModel):
    scan_id: UUID
    format: str = Field(..., pattern="^(html|pdf|json)$")
    title: Optional[str] = None


class ReportResponse(BaseModel):
    id: UUID
    project_id: UUID
    scan_id: Optional[UUID]
    title: str
    format: str
    status: str
    file_size: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
