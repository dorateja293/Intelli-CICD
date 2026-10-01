"""
Intelli-CI Configuration Module

Centralized configuration management using Pydantic Settings.
All secrets loaded from environment variables.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    database_url: str = Field(
        default="postgresql+asyncpg://intellici:password@localhost:5432/intellici",
        alias="DATABASE_URL",
    )
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30


class RedisSettings(BaseSettings):
    """Redis configuration."""

    model_config = SettingsConfigDict(env_prefix="REDIS_", env_file=".env", extra="ignore")

    url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    max_connections: int = 100


class KafkaSettings(BaseSettings):
    """Kafka configuration."""

    model_config = SettingsConfigDict(env_prefix="KAFKA_", env_file=".env", extra="ignore")

    bootstrap_servers: str = Field(
        default="localhost:9092",
        alias="KAFKA_BOOTSTRAP_SERVERS",
    )

    # Topic names
    topic_pipeline_trigger: str = "pipeline.trigger"
    topic_job_queue: str = "job.queue"
    topic_job_events: str = "job.events"
    topic_log_stream: str = "log.stream"
    topic_log_errors: str = "log.errors"
    topic_alerts: str = "alerts"
    topic_security_results: str = "security.results"


class ElasticsearchSettings(BaseSettings):
    """Elasticsearch configuration."""

    model_config = SettingsConfigDict(env_prefix="ELASTICSEARCH_", env_file=".env", extra="ignore")

    hosts: str = Field(default="http://localhost:9200", alias="ELASTICSEARCH_HOSTS")
    index_prefix: str = "logs"
    bulk_size: int = 1000
    flush_interval: int = 5


class JWTSettings(BaseSettings):
    """JWT Authentication configuration."""

    model_config = SettingsConfigDict(env_prefix="JWT_", env_file=".env", extra="ignore")

    secret_key: str = Field(default="change-me-in-production", alias="JWT_SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")


class VaultSettings(BaseSettings):
    """HashiCorp Vault configuration."""

    model_config = SettingsConfigDict(env_prefix="VAULT_", env_file=".env", extra="ignore")

    addr: str = Field(default="http://localhost:8200", alias="VAULT_ADDR")
    token: str = Field(default="", alias="VAULT_TOKEN")
    enabled: bool = False


class MinIOSettings(BaseSettings):
    """MinIO / S3 configuration for artifact storage."""

    model_config = SettingsConfigDict(env_prefix="MINIO_", env_file=".env", extra="ignore")

    endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    access_key: str = Field(default="minio", alias="MINIO_ACCESS_KEY")
    secret_key: str = Field(default="minio123", alias="MINIO_SECRET_KEY")
    bucket: str = Field(default="intellici-artifacts", alias="MINIO_BUCKET")
    secure: bool = False


class SMTPSettings(BaseSettings):
    """SMTP configuration for email notifications."""

    model_config = SettingsConfigDict(env_prefix="SMTP_", env_file=".env", extra="ignore")

    host: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    port: int = Field(default=587, alias="SMTP_PORT")
    username: str = Field(default="", alias="SMTP_USERNAME")
    password: str = Field(default="", alias="SMTP_PASSWORD")
    from_address: str = Field(default="noreply@intelli-ci.dev", alias="SMTP_FROM_ADDRESS")


class ServiceSettings(BaseSettings):
    """Service-specific configuration."""

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    # Service identification
    service_name: str = Field(default="intelli-ci", alias="SERVICE_NAME")
    log_level: Literal["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    # Service ports
    webhook_port: int = Field(default=8001, alias="WEBHOOK_SERVICE_PORT")
    orchestrator_port: int = Field(default=8002, alias="ORCHESTRATOR_SERVICE_PORT")
    log_processor_port: int = Field(default=8003, alias="LOG_PROCESSOR_SERVICE_PORT")
    security_scanner_port: int = Field(default=8004, alias="SECURITY_SCANNER_SERVICE_PORT")
    notification_port: int = Field(default=8005, alias="NOTIFICATION_SERVICE_PORT")
    api_port: int = Field(default=8000, alias="API_SERVICE_PORT")

    # Dashboard URL for notification links
    dashboard_url: str = Field(default="http://localhost:3000", alias="DASHBOARD_URL")


class GitHubSettings(BaseSettings):
    """GitHub integration and OAuth configuration."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    client_id: str = Field(default="", alias="GITHUB_CLIENT_ID")
    client_secret: str = Field(default="", alias="GITHUB_CLIENT_SECRET")
    redirect_uri: str = Field(
        default="http://localhost:3000/auth/github/callback",
        alias="GITHUB_REDIRECT_URI",
    )
    token: str = Field(default="", alias="GITHUB_TOKEN")
    webhook_secret: str = Field(default="default_secret", alias="GITHUB_WEBHOOK_SECRET")


class WorkerSettings(BaseSettings):
    """Worker agent configuration."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    concurrency: int = Field(default=1, alias="WORKER_CONCURRENCY")
    default_timeout: int = Field(default=3600, alias="JOB_DEFAULT_TIMEOUT")
    k8s_namespace: str = Field(default="ci-workers", alias="K8S_NAMESPACE")
    k8s_in_cluster: bool = Field(default=False, alias="K8S_IN_CLUSTER")


class Settings(BaseSettings):
    """Main settings aggregating all configuration."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)
    elasticsearch: ElasticsearchSettings = Field(default_factory=ElasticsearchSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    vault: VaultSettings = Field(default_factory=VaultSettings)
    minio: MinIOSettings = Field(default_factory=MinIOSettings)
    smtp: SMTPSettings = Field(default_factory=SMTPSettings)
    service: ServiceSettings = Field(default_factory=ServiceSettings)
    worker: WorkerSettings = Field(default_factory=WorkerSettings)
    github: GitHubSettings = Field(default_factory=GitHubSettings)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

