from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy import String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, utc_now


class EvidenceSnapshot(Base):
    """
    Immutable review snapshot binding human approvals to cryptographic evidence.
    Contains SHA-256 fingerprint of the complete state, baseline/proposed versions,
    test results, impact blast radius, and deterministic readiness verdicts.
    """
    __tablename__ = "evidence_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # SNAP-<hash[:12]>
    change_request_id: Mapped[str] = mapped_column(String(64), ForeignKey("change_requests.id"), nullable=False, index=True)
    workflow_run_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    target_rule_id: Mapped[str] = mapped_column(String(64), nullable=False)
    baseline_version_id: Mapped[str] = mapped_column(String(100), nullable=False)
    baseline_version_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    proposed_version_id: Mapped[str] = mapped_column(String(100), nullable=False)
    proposed_version_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    graph_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    readiness_status: Mapped[str] = mapped_column(String(50), nullable=False)
    is_blocked: Mapped[bool] = mapped_column(nullable=False, default=False)
    test_summary: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    selected_test_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    impacted_artifact_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    full_snapshot_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
