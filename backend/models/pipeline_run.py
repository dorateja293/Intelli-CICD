import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    commit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("commits.id", ondelete="CASCADE"), nullable=False, index=True)
    # RUN_TESTS | SKIP_TESTS | PARTIAL_TESTS
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")   # pending|running|passed|failed
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    tests_total: Mapped[int] = mapped_column(Integer, default=0)
    tests_skipped: Mapped[int] = mapped_column(Integer, default=0)
    tests_run: Mapped[int] = mapped_column(Integer, default=0)
    tests_failed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
