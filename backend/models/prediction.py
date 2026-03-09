import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    commit_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("commits.id", ondelete="CASCADE"), nullable=True, index=True)
    # User who triggered this prediction (manual /predict or webhook repo owner)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # ML output
    failure_probability: Mapped[float] = mapped_column(Float, nullable=False)
    ml_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # LLM output
    llm_risk_level: Mapped[str] = mapped_column(String(10), nullable=True)    # LOW|MEDIUM|HIGH
    llm_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    llm_affected_modules: Mapped[str] = mapped_column(Text, nullable=True)    # comma-separated
    llm_reasoning: Mapped[str] = mapped_column(Text, nullable=True)

    # Final decision
    decision: Mapped[str] = mapped_column(String(20), nullable=False)         # RUN_TESTS|SKIP_TESTS|PARTIAL_TESTS
    partial_test_paths: Mapped[str] = mapped_column(Text, nullable=True)      # JSON list

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
