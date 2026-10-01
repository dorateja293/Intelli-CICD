"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2025-04-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('slug', sa.String(255), unique=True, nullable=False),
        sa.Column('settings', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, default='developer'),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Repositories table
    op.create_table(
        'repositories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('url', sa.String(500), unique=True, nullable=False, index=True),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('default_branch', sa.String(255), nullable=False, default='main'),
        sa.Column('webhook_secret', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('settings', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Pipelines table
    op.create_table(
        'pipelines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('repo_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('repositories.id'), nullable=False, index=True),
        sa.Column('trigger_type', sa.String(50), nullable=False),
        sa.Column('commit_sha', sa.String(40), nullable=False, index=True),
        sa.Column('branch', sa.String(255), nullable=False),
        sa.Column('commit_message', sa.Text),
        sa.Column('author_email', sa.String(255)),
        sa.Column('author_name', sa.String(255)),
        sa.Column('pr_number', sa.Integer),
        sa.Column('status', sa.String(50), nullable=False, default='PENDING', index=True),
        sa.Column('blocked_reason', sa.Text),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('duration_seconds', sa.Integer),
        sa.Column('config_yaml', sa.Text),
        sa.Column('config_error', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Jobs table
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pipeline_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pipelines.id'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('stage', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='PENDING', index=True),
        sa.Column('exit_code', sa.Integer),
        sa.Column('error_message', sa.Text),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('duration_seconds', sa.Integer),
        sa.Column('retry_count', sa.Integer, nullable=False, default=0),
        sa.Column('wave_index', sa.Integer, nullable=False, default=0),
        sa.Column('runner_id', sa.String(255)),
        sa.Column('config', postgresql.JSONB, default={}),
        sa.Column('artifacts_path', sa.String(500)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('pipeline_id', 'name', name='uq_job_pipeline_name'),
    )

    # Security Findings table
    op.create_table(
        'security_findings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pipeline_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pipelines.id'), nullable=False, index=True),
        sa.Column('scanner', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False, index=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('affected_file', sa.String(500)),
        sa.Column('line_number', sa.Integer),
        sa.Column('cve_id', sa.String(50), index=True),
        sa.Column('cvss_score', sa.Float),
        sa.Column('remediation', sa.Text),
        sa.Column('suppressed', sa.Boolean, nullable=False, default=False),
        sa.Column('suppressed_by', postgresql.UUID(as_uuid=True)),
        sa.Column('suppressed_reason', sa.Text),
        sa.Column('suppressed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # AI Suggestions table
    op.create_table(
        'ai_suggestions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pipeline_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pipelines.id'), nullable=False, index=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id'), index=True),
        sa.Column('error_fingerprint', sa.String(100), nullable=False, index=True),
        sa.Column('error_type', sa.String(255), nullable=False),
        sa.Column('error_message', sa.Text, nullable=False),
        sa.Column('suggestion_text', sa.Text, nullable=False),
        sa.Column('confidence_score', sa.Float, nullable=False, default=0.0),
        sa.Column('rule_id', sa.String(100)),
        sa.Column('model_used', sa.String(100), nullable=False, default='rule_engine'),
        sa.Column('helpful_votes', sa.Integer, nullable=False, default=0),
        sa.Column('not_helpful_votes', sa.Integer, nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Notification Configs table
    op.create_table(
        'notification_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('config', postgresql.JSONB, default={}),
        sa.Column('events', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Security Policies table
    op.create_table(
        'security_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), unique=True, nullable=False),
        sa.Column('block_on_critical', sa.Boolean, nullable=False, default=True),
        sa.Column('block_on_high', sa.Boolean, nullable=False, default=False),
        sa.Column('block_on_secrets', sa.Boolean, nullable=False, default=True),
        sa.Column('max_critical_allowed', sa.Integer, nullable=False, default=0),
        sa.Column('max_high_allowed', sa.Integer, nullable=False, default=5),
        sa.Column('allowed_licenses', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('blocked_packages', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Refresh Tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('token_hash', sa.String(255), unique=True, nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean, nullable=False, default=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Pipeline Event Logs table
    op.create_table(
        'pipeline_event_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pipeline_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pipelines.id'), nullable=False, index=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('previous_status', sa.String(50)),
        sa.Column('new_status', sa.String(50)),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('pipeline_event_logs')
    op.drop_table('refresh_tokens')
    op.drop_table('security_policies')
    op.drop_table('notification_configs')
    op.drop_table('ai_suggestions')
    op.drop_table('security_findings')
    op.drop_table('jobs')
    op.drop_table('pipelines')
    op.drop_table('repositories')
    op.drop_table('users')
    op.drop_table('organizations')
