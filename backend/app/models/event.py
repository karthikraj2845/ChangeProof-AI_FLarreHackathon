from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy import String, Boolean, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, utc_now


class ObservedEvent(Base):
    __tablename__ = "observed_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # e.g. EVT-TXN-2026-001
    transaction_identifier: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), default="QUOTE_RATING_REQUEST")
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    observed_outcome: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    reported_rule_version: Mapped[str] = mapped_column(String(100), nullable=False)
    simulated: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
