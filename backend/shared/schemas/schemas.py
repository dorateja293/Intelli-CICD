"""
Pydantic Schemas for Intelli-CI

Request/Response validation schemas for all services.
"""

import uuid
from datetime import datetime
from typing import Any, Generic, Literal, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ================================
# Generic Response Wrappers
# ================================

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int = 1
    per_page: int = 20
    total: int = 0
    total_pages: int = 0


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    data: Optional[T] = None
    meta: Optional[PaginationMeta] = None
    error: Optional[dict[str, Any]] = None


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


# ================================
# Webhook Schemas
# ================================

class PipelineTriggerEvent(BaseModel):
    """Canonical pipeline trigger event from webhook."""

    idempotency_key: str
    trigger_type: Literal["push", "pull_request", "tag", "manual"]
    provider: Literal["github", "gitlab", "bitbucket"]
    repo_id: str
    repo_url: str
    branch: str
    commit_sha: str = Field(min_length=40, max_length=40)
    commit_message: str
    author_email: str
    author_name: str
    pr_number: Optional[int] = None
    triggered_at: datetime


class WebhookResponse(BaseModel):
    """Webhook endpoint response."""

    accepted: bool
    pipeline_id: Optional[str] = None
    message: str = ""


# ================================
# Pipeline Schemas
# ================================

class PipelineBase(BaseModel):
    """Base pipeline schema."""

    trigger_type: str
    commit_sha: str
    branch: str
    commit_message: Optional[str] = None
    author_email: Optional[str] = None
    author_name: Optional[str] = None
    pr_number: Optional[int] = None


class PipelineCreate(PipelineBase):
    """Schema for creating a pipeline."""

    repo_id: uuid.UUID


class PipelineUpdate(BaseModel):
    """Schema for updating a pipeline."""

    status: Optional[str] = None
    blocked_reason: Optional[str] = None


class PipelineResponse(PipelineBase):
    """Pipeline response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repo_id: uuid.UUID
    status: str
    blocked_reason: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class PipelineListResponse(BaseModel):
    """List of pipelines with pagination."""

    data: list[PipelineResponse]
    meta: PaginationMeta


# ================================
# Job Schemas
# ================================

class JobBase(BaseModel):
    """Base job schema."""

    name: str
    stage: str


class JobConfig(BaseModel):
    """Job configuration from YAML."""

    stage: str
    image: str = "ubuntu:22.04"
    commands: list[str]
    depends_on: list[str] = Field(default_factory=list)
    allow_failure: bool = False
    timeout: int = 3600
    retry: Optional[dict[str, Any]] = None
    artifacts: Optional[dict[str, Any]] = None
    rules: list[dict[str, Any]] = Field(default_factory=list)
    cache: Optional[dict[str, Any]] = None
    environment: Optional[str] = None


class JobResponse(JobBase):
    """Job response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pipeline_id: uuid.UUID
    status: str
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    retry_count: int = 0
    wave_index: int = 0
    runner_id: Optional[str] = None
    created_at: datetime


class JobEventMessage(BaseModel):
    """Job completion event (Kafka message)."""

    pipeline_id: str
    job_id: str
    status: Literal["SUCCESS", "FAILED"]
    exit_code: int
    duration_seconds: int
    runner_id: str
    timestamp: str


# ================================
# Pipeline YAML Config Schemas
# ================================

class RetryConfig(BaseModel):
    """Retry configuration."""

    max_attempts: int = 3
    backoff: Literal["fixed", "exponential", "linear"] = "exponential"
    backoff_base_seconds: int = 30
    retry_on_exit_codes: list[int] = Field(default_factory=lambda: [1, 2])


class ArtifactsConfig(BaseModel):
    """Artifacts configuration."""

    paths: list[str]
    expire_in: str = "7d"


class CacheConfig(BaseModel):
    """Cache configuration."""

    key: str
    paths: list[str]


class RuleConfig(BaseModel):
    """Conditional rule configuration."""

    condition: Optional[str] = Field(None, alias="if")
    when: Literal["always", "never", "manual", "on_success", "on_failure"] = "always"


class PipelineYAMLConfig(BaseModel):
    """Full pipeline YAML configuration."""

    version: str
    stages: list[str]
    jobs: dict[str, JobConfig]
    defaults: Optional[dict[str, Any]] = None


# ================================
# Log Schemas
# ================================

class RawLogEvent(BaseModel):
    """Raw log event from worker (Kafka message)."""

    job_id: str
    pipeline_id: str
    line_number: int
    content: str
    timestamp: str
    level: str


class EnrichedLogEvent(BaseModel):
    """Enriched log event for Elasticsearch."""

    job_id: str
    pipeline_id: str
    repo_id: str
    line_number: int
    content: str
    timestamp: datetime
    level: str
    is_error: bool
    error_fingerprint: Optional[str] = None
    stack_trace_group: Optional[str] = None
    section: Optional[str] = None


class LogErrorEvent(BaseModel):
    """Error event for AI Engine (Kafka message)."""

    job_id: str
    pipeline_id: str
    repo_id: str
    error_lines: list[str]
    error_fingerprint: str
    stack_trace_group: Optional[str] = None
    timestamp: str


# ================================
# Security Schemas
# ================================

class SecurityFindingBase(BaseModel):
    """Base security finding schema."""

    scanner: str
    severity: str
    category: str
    title: str
    description: Optional[str] = None
    affected_file: Optional[str] = None
    line_number: Optional[int] = None
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    remediation: Optional[str] = None


class SecurityFindingResponse(SecurityFindingBase):
    """Security finding response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pipeline_id: uuid.UUID
    suppressed: bool
    suppressed_reason: Optional[str] = None
    created_at: datetime


class SecuritySummary(BaseModel):
    """Security scan summary (Kafka message)."""

    pipeline_id: str
    total_findings: int
    critical: int
    high: int
    medium: int
    low: int
    blocked: bool
    timestamp: str


class SuppressFindingRequest(BaseModel):
    """Request to suppress a finding."""

    reason: str = Field(min_length=10)


# ================================
# Notification Schemas
# ================================

class AlertEvent(BaseModel):
    """Alert event for notification service (Kafka message)."""

    event_type: Literal[
        "pipeline_failed",
        "pipeline_succeeded",
        "pipeline_cancelled",
        "security_critical",
        "secret_detected",
        "job_failed",
        "slo_breach",
    ]
    org_id: str
    repo_id: str
    pipeline_id: str
    job_id: Optional[str] = None
    severity: Literal["INFO", "WARN", "ERROR", "CRITICAL"]
    title: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: str


class NotificationConfigBase(BaseModel):
    """Base notification config schema."""

    name: str
    channel: Literal["slack", "email", "pagerduty", "teams", "webhook"]
    config: dict[str, Any]
    events: list[str]
    active: bool = True


class NotificationConfigCreate(NotificationConfigBase):
    """Create notification config."""

    pass


class NotificationConfigUpdate(BaseModel):
    """Update notification config."""

    name: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    events: Optional[list[str]] = None
    active: Optional[bool] = None


class NotificationConfigResponse(NotificationConfigBase):
    """Notification config response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ================================
# AI Suggestion Schemas
# ================================

class AISuggestionResponse(BaseModel):
    """AI suggestion response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pipeline_id: uuid.UUID
    job_id: Optional[uuid.UUID] = None
    error_fingerprint: str
    error_type: str
    error_message: str
    suggestion_text: str
    confidence_score: float
    rule_id: Optional[str] = None
    model_used: str
    helpful_votes: int
    not_helpful_votes: int
    created_at: datetime


class VoteSuggestionRequest(BaseModel):
    """Request to vote on a suggestion."""

    helpful: bool


# ================================
# Auth Schemas
# ================================

VALID_PROFESSIONS = {
    "student", "developer", "software_engineer", "devops_engineer",
    "team_lead", "project_manager", "researcher", "other",
}

class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    name: str = Field(min_length=1, max_length=255)


class UserCreate(UserBase):
    """Create user request."""

    password: str = Field(min_length=8)
    profession: Optional[str] = None
    organization_name: Optional[str] = Field(default=None, max_length=255)
    organization_id: Optional[uuid.UUID] = None

    @field_validator("profession")
    @classmethod
    def validate_profession(cls, v):
        if v is None:
            return v
        normalized = v.lower().strip().replace(" ", "_")
        if normalized not in VALID_PROFESSIONS:
            raise ValueError(f"Invalid profession. Must be one of: {', '.join(sorted(VALID_PROFESSIONS))}")
        return normalized


class UserLogin(BaseModel):
    """Login request."""

    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    profession: Optional[str] = None
    organization_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    organization_id: uuid.UUID
    created_at: datetime


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


# ================================
# OTP Authentication Schemas
# ================================

class SendOTPRequest(BaseModel):
    """Send OTP request."""

    email: EmailStr


class SendOTPResponse(BaseModel):
    """Send OTP response."""

    message: str
    email: str
    expires_in_minutes: int = 5


class VerifyOTPRequest(BaseModel):
    """Verify OTP request."""

    email: EmailStr
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class VerifyOTPResponse(BaseModel):
    """Verify OTP response."""

    message: str
    is_new_user: bool
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class ResendOTPRequest(BaseModel):
    """Resend OTP request."""

    email: EmailStr


class OTPStatusResponse(BaseModel):
    """OTP status response."""

    email: str
    expires_at: str
    attempts: int
    max_attempts: int
    is_verified: bool
    is_expired: bool


# ================================
# Repository Schemas
# ================================

class RepositoryBase(BaseModel):
    """Base repository schema."""

    name: str
    url: str
    provider: Literal["github", "gitlab", "bitbucket"]
    default_branch: str = "main"


class RepositoryCreate(RepositoryBase):
    """Create repository request."""

    pass


class RepositoryResponse(RepositoryBase):
    """Repository response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ================================
# Organization Schemas
# ================================

class OrganizationBase(BaseModel):
    """Base organization schema."""

    name: str
    slug: str


class OrganizationCreate(OrganizationBase):
    """Create organization request."""

    pass


class OrganizationResponse(OrganizationBase):
    """Organization response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ================================
# Security Policy Schemas
# ================================

class SecurityPolicyBase(BaseModel):
    """Base security policy schema."""

    block_on_critical: bool = True
    block_on_high: bool = False
    block_on_secrets: bool = True
    max_critical_allowed: int = 0
    max_high_allowed: int = 5


class SecurityPolicyCreate(SecurityPolicyBase):
    """Create security policy."""

    pass


class SecurityPolicyUpdate(SecurityPolicyBase):
    """Update security policy."""

    pass


class SecurityPolicyResponse(SecurityPolicyBase):
    """Security policy response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
