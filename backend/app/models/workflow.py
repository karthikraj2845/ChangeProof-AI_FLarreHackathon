from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy import String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, utc_now


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    change_request_id: Mapped[str] = mapped_column(String(64), ForeignKey("change_requests.id"), nullable=False, index=True)
    workflow_type: Mapped[str] = mapped_column(String(50), default="CHANGE_ASSURANCE")  # CHANGE_ASSURANCE, INTENT_GUARD
    status: Mapped[str] = mapped_column(String(50), default="RUNNING")  # RUNNING, PAUSED_FOR_REVIEW, COMPLETED, FAILED, BLOCKED
    current_node: Mapped[str] = mapped_column(String(100), default="start")
    state_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completion_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
