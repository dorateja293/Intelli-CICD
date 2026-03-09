import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class Commit(Base):
    __tablename__ = "commits"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    sha: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(120), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    files_changed: Mapped[int] = mapped_column(Integer, default=0)
    lines_added: Mapped[int] = mapped_column(Integer, default=0)
    lines_deleted: Mapped[int] = mapped_column(Integer, default=0)
    # Derived / extracted features
    code_churn: Mapped[int] = mapped_column(Integer, default=0)
    file_types: Mapped[str] = mapped_column(String(500), nullable=True)   # JSON list of extensions
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("sha", "repository_id", name="uq_commit_sha_repo"),
        Index("ix_commit_created_at", "created_at"),
        Index("ix_commit_repo_created", "repository_id", "created_at"),
    )
