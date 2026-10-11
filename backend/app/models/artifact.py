from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy import String, Text, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)  # REQUIREMENT, RULE, RULE_VERSION, PRODUCT_CONFIG, ELIGIBILITY_SERVICE, RATING_SERVICE, POLICY_WORKFLOW, REGRESSION_TEST, CHANGE_REQUEST
    description: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class DependencyEdge(Base):
    __tablename__ = "dependency_edges"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    source_artifact_id: Mapped[str] = mapped_column(String(64), ForeignKey("artifacts.id"), nullable=False, index=True)
    target_artifact_id: Mapped[str] = mapped_column(String(64), ForeignKey("artifacts.id"), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False)  # IMPLEMENTS, DEPENDS_ON, VALIDATED_BY, APPLIES_TO, SUPERSEDES
    evidence_source: Mapped[str] = mapped_column(String(100), default="CODE_ANALYSIS")
    verification_status: Mapped[str] = mapped_column(String(50), default="VERIFIED")  # VERIFIED, UNVERIFIED, INFERRED
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    version_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
