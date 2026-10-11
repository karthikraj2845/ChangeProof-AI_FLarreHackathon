from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy import String, Text, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, utc_now


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    finding_type: Mapped[str] = mapped_column(String(64), nullable=False)  # DEVIATION, REGRESSION, COVERAGE_GAP, UNCERTAIN_DEPENDENCY
    severity: Mapped[str] = mapped_column(String(32), default="HIGH")  # CRITICAL, HIGH, MEDIUM, LOW
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    linked_change_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    linked_rule_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    linked_rule_version_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    linked_requirement_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    linked_test_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    linked_event_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    evidence: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="OPEN")  # OPEN, ACKNOWLEDGED, RESOLVED, SUPPRESSED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
