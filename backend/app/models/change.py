from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy import String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now


class ChangeRequest(Base):
    __tablename__ = "change_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_rule_id: Mapped[str] = mapped_column(String(64), ForeignKey("rules.id"), nullable=False, index=True)
    baseline_version_id: Mapped[str] = mapped_column(String(100), ForeignKey("rule_versions.id"), nullable=False)
    proposed_version_id: Mapped[str] = mapped_column(String(100), ForeignKey("rule_versions.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="SUBMITTED")  # SUBMITTED, ANALYZING, REVIEW_REQUIRED, APPROVED, REJECTED, BLOCKED
    parsed_change_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    readiness_status: Mapped[str] = mapped_column(String(50), default="PENDING")  # BLOCKED, NEEDS_HUMAN_REVIEW, READY_FOR_REVIEW, PENDING
    readiness_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    creator: Mapped[str] = mapped_column(String(100), default="underwriting_analyst")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
