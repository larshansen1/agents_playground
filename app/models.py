import uuid

from sqlalchemy import TIMESTAMP, Column, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Task(Base):
    """SQLAlchemy model for tasks table."""

    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="pending")
    input = Column(JSONB, nullable=False)
    output = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Cost tracking fields
    user_id_hash = Column(String(64), nullable=True)
    model_used = Column(String(100), nullable=True)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_cost = Column(Numeric(10, 6), default=0)
    generation_id = Column(String(100), nullable=True)

    __table_args__ = (
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_user_hash", "user_id_hash"),
        Index("idx_tasks_cost", "total_cost"),
    )
