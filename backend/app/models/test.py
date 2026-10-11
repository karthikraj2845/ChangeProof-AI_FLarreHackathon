from datetime import datetime
from typing import Optional, Any, Dict, List
from sqlalchemy import String, Text, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now


class RegressionTest(Base):
    __tablename__ = "regression_tests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="POSITIVE")  # POSITIVE, NEGATIVE, BOUNDARY, INVALID_INPUT, EDGE_CASE
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    expected_baseline_outcome: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    expected_proposed_outcome: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    coverage_tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    linked_rule_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    linked_requirement_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class VerificationRun(Base):
    __tablename__ = "verification_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    change_request_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    baseline_version_id: Mapped[str] = mapped_column(String(100), nullable=False)
    proposed_version_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED")  # COMPLETED, FAILED, BLOCKED
    summary: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    test_results: Mapped[list["TestResult"]] = relationship("TestResult", back_populates="verification_run", cascade="all, delete-orphan")


class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    verification_run_id: Mapped[str] = mapped_column(String(64), ForeignKey("verification_runs.id"), nullable=False, index=True)
    test_id: Mapped[str] = mapped_column(String(64), ForeignKey("regression_tests.id"), nullable=False)
    rule_version_id: Mapped[str] = mapped_column(String(100), nullable=False)
    expected_outcome: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    actual_outcome: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # PASSED, FAILED, REGRESSION, ERROR
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    verification_run: Mapped["VerificationRun"] = relationship("VerificationRun", back_populates="test_results")
    test: Mapped["RegressionTest"] = relationship("RegressionTest")
