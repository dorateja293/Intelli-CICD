"""
SQLAlchemy Models for Intelli-CI

Complete database schema following the instruction specifications.
All IDs are UUID v4, timestamps are TIMESTAMPTZ (UTC).
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator, CHAR

from shared.database.connection import Base


# ================================
# Portable UUID Type (works with SQLite and PostgreSQL)
# ================================

class UUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses CHAR(36).
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif isinstance(value, uuid.UUID):
            return value
        else:
            return uuid.UUID(value)


# ================================
# Enums
# ================================

class PipelineStatus(str, Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class TriggerType(str, Enum):
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    TAG = "tag"
    MANUAL = "manual"


class Provider(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class NotificationChannel(str, Enum):
    SLACK = "slack"
    EMAIL = "email"
    PAGERDUTY = "pagerduty"
    TEAMS = "teams"
    WEBHOOK = "webhook"


class UserRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


# ================================
# Mixin Classes
# ================================

class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


# ================================
# Organization Model
# ================================

class Organization(Base, TimestampMixin):
    """Organization that owns repositories and users."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="organization")
    repositories: Mapped[list["Repository"]] = relationship(
        "Repository",
        back_populates="organization",
    )
    notification_configs: Mapped[list["NotificationConfig"]] = relationship(
        "NotificationConfig",
        back_populates="organization",
    )
    security_policy: Mapped[Optional["SecurityPolicy"]] = relationship(
        "SecurityPolicy",
        back_populates="organization",
        uselist=False,
    )


# ================================
# ================================
# User Model
# ================================

class User(Base, TimestampMixin):
    """User account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="developer", nullable=False)
    profession: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)       # e.g. student, devops_engineer
    organization_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # college / company
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("organizations.id"),
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")
    github_account: Mapped[Optional["GitHubAccount"]] = relationship("GitHubAccount", back_populates="user", uselist=False, cascade="all, delete-orphan")
    repositories: Mapped[list["Repository"]] = relationship("Repository", back_populates="user")


# ================================
# GitHub Account Model
# ================================

class GitHubAccount(Base, TimestampMixin):
    """Connected GitHub OAuth account."""

    __tablename__ = "github_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )
    github_user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    access_token: Mapped[str] = mapped_column(String(500), nullable=False)
    token_type: Mapped[str] = mapped_column(String(50), default="bearer", nullable=False)
    scopes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="github_account")


# ================================
# Repository Model
# ================================

class Repository(Base, TimestampMixin):
    """Git repository configuration."""

    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("organizations.id"),
        nullable=False,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(),
        ForeignKey("users.id"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), default="github", nullable=False)  # github, gitlab, bitbucket
    default_branch: Mapped[str] = mapped_column(String(255), default="main", nullable=False)
    visibility: Mapped[str] = mapped_column(String(50), default="public", nullable=False)  # public, private
    language: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stars_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    forks_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    github_repo_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    webhook_secret: Mapped[str] = mapped_column(String(255), default="default_secret", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(50), default="IDLE", nullable=False)  # IDLE, SYNCING, COMPLETED, FAILED
    sync_progress: Mapped[Optional[str]] = mapped_column(String(255), default="Ready", nullable=True)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="repositories",
    )
    user: Mapped[Optional["User"]] = relationship("User", back_populates="repositories")
    pipelines: Mapped[list["Pipeline"]] = relationship("Pipeline", back_populates="repository", cascade="all, delete-orphan")


# ================================
# Pipeline Model
# ================================

class Pipeline(Base, TimestampMixin):
    """CI/CD Pipeline execution."""

    __tablename__ = "pipelines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    repo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("repositories.id"),
        nullable=False,
        index=True,
    )
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    branch: Mapped[str] = mapped_column(String(255), nullable=False)
    commit_message: Mapped[Optional[str]] = mapped_column(Text)
    author_email: Mapped[Optional[str]] = mapped_column(String(255))
    author_name: Mapped[Optional[str]] = mapped_column(String(255))
    pr_number: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        nullable=False,
        index=True,
    )
    blocked_reason: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    config_yaml: Mapped[Optional[str]] = mapped_column(Text)
    config_error: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="pipelines")
    jobs: Mapped[list["Job"]] = relationship(
        "Job",
        back_populates="pipeline",
        cascade="all, delete-orphan",
    )
    security_findings: Mapped[list["SecurityFinding"]] = relationship(
        "SecurityFinding",
        back_populates="pipeline",
        cascade="all, delete-orphan",
    )
    ai_suggestions: Mapped[list["AISuggestion"]] = relationship(
        "AISuggestion",
        back_populates="pipeline",
        cascade="all, delete-orphan",
    )


# ================================
# Job Model
# ================================

class Job(Base, TimestampMixin):
    """Individual job within a pipeline."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("pipelines.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False, index=True)
    exit_code: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wave_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    runner_id: Mapped[Optional[str]] = mapped_column(String(255))
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    artifacts_path: Mapped[Optional[str]] = mapped_column(String(500))

    # Relationships
    pipeline: Mapped["Pipeline"] = relationship("Pipeline", back_populates="jobs")

    __table_args__ = (
        UniqueConstraint("pipeline_id", "name", name="uq_job_pipeline_name"),
    )


# ================================
# Security Finding Model
# ================================

class SecurityFinding(Base, TimestampMixin):
    """Security vulnerability or issue found during scanning."""

    __tablename__ = "security_findings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("pipelines.id"),
        nullable=False,
        index=True,
    )
    scanner: Mapped[str] = mapped_column(String(50), nullable=False)  # trivy, gitleaks, semgrep
    severity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    affected_file: Mapped[Optional[str]] = mapped_column(String(500))
    line_number: Mapped[Optional[int]] = mapped_column(Integer)
    cve_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    cvss_score: Mapped[Optional[float]] = mapped_column(Float)
    remediation: Mapped[Optional[str]] = mapped_column(Text)
    suppressed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    suppressed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID())
    suppressed_reason: Mapped[Optional[str]] = mapped_column(Text)
    suppressed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    pipeline: Mapped["Pipeline"] = relationship("Pipeline", back_populates="security_findings")


# ================================
# AI Suggestion Model
# ================================

class AISuggestion(Base, TimestampMixin):
    """AI-generated fix suggestion for errors."""

    __tablename__ = "ai_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("pipelines.id"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(),
        ForeignKey("jobs.id"),
        index=True,
    )
    error_fingerprint: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    error_type: Mapped[str] = mapped_column(String(255), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rule_id: Mapped[Optional[str]] = mapped_column(String(100))
    model_used: Mapped[str] = mapped_column(String(100), default="rule_engine", nullable=False)
    helpful_votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    not_helpful_votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    pipeline: Mapped["Pipeline"] = relationship("Pipeline", back_populates="ai_suggestions")


# ================================
# Notification Config Model
# ================================

class NotificationConfig(Base, TimestampMixin):
    """Notification channel configuration."""

    __tablename__ = "notification_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)  # slack, email, pagerduty, teams
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)  # channel-specific config
    events: Mapped[list[str]] = mapped_column(JSON, default=list)  # List of event types
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="notification_configs",
    )


# ================================
# Security Policy Model
# ================================

class SecurityPolicy(Base, TimestampMixin):
    """Organization security policy configuration."""

    __tablename__ = "security_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("organizations.id"),
        unique=True,
        nullable=False,
    )
    block_on_critical: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    block_on_high: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    block_on_secrets: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_critical_allowed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_high_allowed: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    allowed_licenses: Mapped[list[str]] = mapped_column(JSON, default=list)  # Allowed licenses
    blocked_packages: Mapped[list[str]] = mapped_column(JSON, default=list)  # Blocked packages

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="security_policy",
    )


# ================================
# Refresh Token Model
# ================================

class RefreshToken(Base, TimestampMixin):
    """JWT Refresh token storage."""

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


# ================================
# Pipeline Event Log Model
# ================================

class PipelineEventLog(Base):
    """Audit log for pipeline state changes."""

    __tablename__ = "pipeline_event_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("pipelines.id"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    previous_status: Mapped[Optional[str]] = mapped_column(String(50))
    new_status: Mapped[Optional[str]] = mapped_column(String(50))
    event_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )


# ================================
# OTP Model
# ================================

class OTP(Base):
    """OTP storage for email verification."""

    __tablename__ = "otps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    otp_code: Mapped[str] = mapped_column(String(6), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
