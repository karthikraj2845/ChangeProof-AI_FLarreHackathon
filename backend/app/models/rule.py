from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy import String, Text, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rule_type: Mapped[str] = mapped_column(String(100), default="UNDERWRITING_DISCOUNT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    versions: Mapped[list["RuleVersion"]] = relationship("RuleVersion", back_populates="rule", cascade="all, delete-orphan")


class RuleVersion(Base):
    __tablename__ = "rule_versions"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # e.g. RULE-SAFE-DRIVER-v1.0
    rule_id: Mapped[str] = mapped_column(String(64), ForeignKey("rules.id"), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rule_definition: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="DRAFT")  # APPROVED, DRAFT, PROPOSED, SUPERSEDED, REJECTED
    is_immutable: Mapped[bool] = mapped_column(Boolean, default=False)
    product_scope: Mapped[str] = mapped_column(String(100), default="PERSONAL_AUTO")
    jurisdiction_scope: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    rule: Mapped["Rule"] = relationship("Rule", back_populates="versions")
