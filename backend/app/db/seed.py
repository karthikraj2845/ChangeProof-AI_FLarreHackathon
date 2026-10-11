from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.models.base import Base
from app.models.requirement import Requirement
from app.models.rule import Rule, RuleVersion
from app.models.artifact import Artifact, DependencyEdge
from app.models.change import ChangeRequest
from app.models.test import RegressionTest
from app.models.audit import AuditEvent


def seed_database(db: Session) -> None:
    # 1. Clean existing records for fresh demo reproducibility
    Base.metadata.create_all(bind=engine)
    
    # Check if already seeded
    if db.query(Rule).filter_by(id="RULE-SAFE-DRIVER").first():
        print("Database already contains seed data. Refreshing...")
        db.query(AuditEvent).delete()
        db.query(RegressionTest).delete()
        db.query(DependencyEdge).delete()
        db.query(ChangeRequest).delete()
        db.query(RuleVersion).delete()
        db.query(Rule).delete()
        db.query(Artifact).delete()
        db.query(Requirement).delete()
        db.commit()

    now = datetime.now(timezone.utc)

    # 2. Requirements
    req1 = Requirement(
        id="REQ-AUTO-DISC-001",
        title="Motor Policy Safe Driver Discount Eligibility Specification",
        description="Defines qualification criteria for 10% personal auto safe driver discount. Restricts availability to designated regulatory jurisdictions (CA, TX, FL, NY, IL) and validated low-risk telematics driver scores.",
        domain="Personal Lines Auto Underwriting",
        status="ACTIVE",
        created_at=now,
    )
    db.add(req1)

    # 3. Rules & Versions
    rule1 = Rule(
        id="RULE-SAFE-DRIVER",
        name="Safe Driver Discount Eligibility",
        description="Evaluates driver risk score, vehicle classification, policy status, and licensed state jurisdiction to apply a 10% underwriting rating discount.",
        rule_type="UNDERWRITING_DISCOUNT",
        created_at=now,
    )
    db.add(rule1)

    # Baseline Version 1.0 (APPROVED, Immutable)
    v1_def = {
        "rule_id": "RULE-SAFE-DRIVER",
        "version": "1.0",
        "name": "Safe Driver Discount Eligibility Rule",
        "description": "Baseline production-approved discount rule with jurisdiction restriction.",
        "required_inputs": ["jurisdiction", "driver_risk_score", "vehicle_category", "policy_active"],
        "conditions": [
            {
                "field": "jurisdiction",
                "operator": "in",
                "value": ["CA", "TX", "FL", "NY", "IL"],
                "description": "Jurisdiction is within approved underwriting states (CA, TX, FL, NY, IL)",
                "mandatory": True
            },
            {
                "field": "driver_risk_score",
                "operator": "lte",
                "value": 25,
                "description": "Driver telematics risk score <= 25",
                "mandatory": True
            },
            {
                "field": "vehicle_category",
                "operator": "in",
                "value": ["SEDAN", "SUV", "COUPE", "MINIVAN"],
                "description": "Vehicle category eligible for standard personal lines discount",
                "mandatory": True
            },
            {
                "field": "policy_active",
                "operator": "eq",
                "value": True,
                "description": "Policy is currently in force and active",
                "mandatory": True
            }
        ],
        "success_action": {
            "eligible": True,
            "discount_percentage": 10.0,
            "discount_code": "SAFE_DRIVER_10",
            "message": "Eligible for 10% Safe Driver Discount"
        },
        "fallback_action": {
            "eligible": False,
            "discount_percentage": 0.0,
            "discount_code": None,
            "message": "Not eligible for Safe Driver Discount"
        },
        "product_scope": "PERSONAL_AUTO",
        "jurisdiction_scope": ["CA", "TX", "FL", "NY", "IL"]
    }

    # Proposed Version 1.1 (PROPOSED with deliberate defect: jurisdiction condition removed)
    v1_1_def = {
        "rule_id": "RULE-SAFE-DRIVER",
        "version": "1.1-proposed",
        "name": "Safe Driver Discount Eligibility Rule (Modified)",
        "description": "Proposed modification attempting to expand coverage, but accidentally omitting jurisdiction validation.",
        "required_inputs": ["driver_risk_score", "vehicle_category", "policy_active"],
        "conditions": [
            # NOTE: Jurisdiction check was accidentally deleted in this proposed version!
            {
                "field": "driver_risk_score",
                "operator": "lte",
                "value": 25,
                "description": "Driver telematics risk score <= 25",
                "mandatory": True
            },
            {
                "field": "vehicle_category",
                "operator": "in",
                "value": ["SEDAN", "SUV", "COUPE", "MINIVAN"],
                "description": "Vehicle category eligible for standard personal lines discount",
                "mandatory": True
            },
            {
                "field": "policy_active",
                "operator": "eq",
                "value": True,
                "description": "Policy is currently in force and active",
                "mandatory": True
            }
        ],
        "success_action": {
            "eligible": True,
            "discount_percentage": 10.0,
            "discount_code": "SAFE_DRIVER_10",
            "message": "Eligible for 10% Safe Driver Discount"
        },
        "fallback_action": {
            "eligible": False,
            "discount_percentage": 0.0,
            "discount_code": None,
            "message": "Not eligible for Safe Driver Discount"
        },
        "product_scope": "PERSONAL_AUTO",
        "jurisdiction_scope": None
    }

    rv_baseline = RuleVersion(
        id="RULE-SAFE-DRIVER-v1.0",
        rule_id="RULE-SAFE-DRIVER",
        version="1.0",
        description="Production baseline rule version with strict jurisdiction constraints.",
        rule_definition=v1_def,
        status="APPROVED",
        is_immutable=True,
        product_scope="PERSONAL_AUTO",
        jurisdiction_scope=["CA", "TX", "FL", "NY", "IL"],
        created_at=now,
        approved_at=now,
        approval_metadata={"approved_by": "Chief Underwriting Officer", "ticket": "PROD-REL-882"},
    )
    db.add(rv_baseline)

    rv_proposed = RuleVersion(
        id="RULE-SAFE-DRIVER-v1.1-proposed",
        rule_id="RULE-SAFE-DRIVER",
        version="1.1-proposed",
        description="Proposed rule version containing deliberate defect (omitted jurisdiction verification).",
        rule_definition=v1_1_def,
        status="PROPOSED",
        is_immutable=False,
        product_scope="PERSONAL_AUTO",
        jurisdiction_scope=None,
        created_at=now,
    )
    db.add(rv_proposed)

    # 4. Artifacts in Insurance Architecture
    artifacts_data = [
        ("ART-CR-001", "CR-2026-001: Jurisdiction Removal Change", "CHANGE_REQUEST", "Change request submitted by pricing analyst.", "1.1"),
        ("ART-VER-1.0", "RULE-SAFE-DRIVER-v1.0 (Baseline)", "RULE_VERSION", "Approved immutable baseline rule version.", "1.0"),
        ("ART-VER-1.1", "RULE-SAFE-DRIVER-v1.1 (Proposed)", "RULE_VERSION", "Proposed version lacking jurisdiction validation.", "1.1-proposed"),
        ("ART-RULE-001", "RULE-SAFE-DRIVER Definition", "RULE", "Core business rule for telematics safe-driver discount.", "1.0"),
        ("ART-REQ-001", "REQ-AUTO-DISC-001 Specification", "REQUIREMENT", "Business specification for safe driver discount.", "1.0"),
        ("ART-CFG-001", "CFG-PROD-AUTO-PREMIUM Configuration", "PRODUCT_CONFIG", "Product master configuration for Private Passenger Auto.", "2.4"),
        ("ART-SVC-ELIGIBILITY", "SVC-UNDERWRITING-ELIGIBILITY Service", "ELIGIBILITY_SERVICE", "Underwriting microservice evaluating discount rules.", "3.1"),
        ("ART-SVC-RATING", "SVC-RATING-ENGINE Service", "RATING_SERVICE", "Core rating and premium computation service.", "4.0"),
        ("ART-WF-POLICY", "WF-POLICY-NEW-BUSINESS Workflow", "POLICY_WORKFLOW", "End-to-end policy quote and issuance workflow.", "1.8"),
        ("ART-TEST-SUITE", "TEST-SUITE-SAFE-DRIVER Regression Suite", "REGRESSION_TEST", "Test suite containing boundary, positive, and negative tests.", "1.2"),
    ]

    for art_id, name, atype, desc, ver in artifacts_data:
        db.add(Artifact(
            id=art_id,
            name=name,
            artifact_type=atype,
            description=desc,
            version=ver,
            metadata_json={"domain": "Personal Auto", "tier": "Tier-1 Critical"}
        ))

    # 5. Dependency Edges (NetworkX graph relationships)
    edges_data = [
        ("EDGE-001", "ART-CR-001", "ART-VER-1.1", "SUPERSEDES", "CHANGE_PROPOSAL", "VERIFIED", 1.0),
        ("EDGE-002", "ART-VER-1.1", "ART-RULE-001", "IMPLEMENTS", "CODE_REPOSITORY", "VERIFIED", 1.0),
        ("EDGE-003", "ART-VER-1.0", "ART-RULE-001", "IMPLEMENTS", "CODE_REPOSITORY", "VERIFIED", 1.0),
        ("EDGE-004", "ART-RULE-001", "ART-REQ-001", "IMPLEMENTS", "TRACEABILITY_MATRIX", "VERIFIED", 1.0),
        ("EDGE-005", "ART-REQ-001", "ART-CFG-001", "APPLIES_TO", "PRODUCT_SPEC", "VERIFIED", 0.95),
        ("EDGE-006", "ART-CFG-001", "ART-SVC-ELIGIBILITY", "DEPENDS_ON", "SERVICE_CONTRACT", "VERIFIED", 0.95),
        ("EDGE-007", "ART-SVC-ELIGIBILITY", "ART-SVC-RATING", "DEPENDS_ON", "API_INTEGRATION", "VERIFIED", 0.90),
        ("EDGE-008", "ART-SVC-RATING", "ART-WF-POLICY", "DEPENDS_ON", "ORCHESTRATION_PIPELINE", "VERIFIED", 0.90),
        ("EDGE-009", "ART-SVC-ELIGIBILITY", "ART-TEST-SUITE", "VALIDATED_BY", "AUTOMATED_TEST_RUNNER", "VERIFIED", 1.0),
        ("EDGE-010", "ART-SVC-RATING", "ART-TEST-SUITE", "VALIDATED_BY", "AUTOMATED_TEST_RUNNER", "VERIFIED", 1.0),
    ]

    for edge_id, src, tgt, rel, ev_src, v_status, conf in edges_data:
        db.add(DependencyEdge(
            id=edge_id,
            source_artifact_id=src,
            target_artifact_id=tgt,
            relationship_type=rel,
            evidence_source=ev_src,
            verification_status=v_status,
            confidence=conf,
            version_metadata={"rule_version": "1.1-proposed"}
        ))

    # 6. Seed Change Request
    cr = ChangeRequest(
        id="CR-2026-001",
        title="Remove jurisdiction restriction from safe-driver discount eligibility rule",
        description="Remove the jurisdiction restriction from the safe-driver discount eligibility rule to evaluate customer demand across all states.",
        target_rule_id="RULE-SAFE-DRIVER",
        baseline_version_id="RULE-SAFE-DRIVER-v1.0",
        proposed_version_id="RULE-SAFE-DRIVER-v1.1-proposed",
        status="SUBMITTED",
        parsed_change_json={
            "target_rule": "RULE-SAFE-DRIVER",
            "operation": "REMOVE_CONDITION",
            "condition_field": "jurisdiction",
            "intent": "Remove jurisdiction requirement so discount evaluates nationwide.",
            "business_impact": "High risk of issuing unapproved discount rates in non-filed states.",
        },
        readiness_status="PENDING",
        creator="underwriting_analyst_sarah",
        created_at=now,
    )
    db.add(cr)

    # 7. Regression Tests (8 test cases required by problem statement)
    tests = [
        RegressionTest(
            id="TEST-SD-001",
            name="Eligible Jurisdiction & Safe Driver",
            description="Driver in approved CA jurisdiction with safe score 15, eligible sedan, active policy.",
            category="POSITIVE",
            input_data={"jurisdiction": "CA", "driver_risk_score": 15, "vehicle_category": "SEDAN", "policy_active": True},
            expected_baseline_outcome={"eligible": True, "discount_percentage": 10.0, "discount_code": "SAFE_DRIVER_10"},
            expected_proposed_outcome={"eligible": True, "discount_percentage": 10.0, "discount_code": "SAFE_DRIVER_10"},
            coverage_tags=["jurisdiction", "driver_risk_score", "vehicle_category", "policy_active"],
            linked_rule_id="RULE-SAFE-DRIVER",
            linked_requirement_id="REQ-AUTO-DISC-001",
            created_at=now,
        ),
        RegressionTest(
            id="TEST-SD-002",
            name="Unsupported Jurisdiction with Safe Driver (Seeded Regression Check)",
            description="Driver in unsupported NV jurisdiction with safe score 15. Baseline MUST reject; defective proposed version incorrectly approves!",
            category="NEGATIVE",
            input_data={"jurisdiction": "NV", "driver_risk_score": 15, "vehicle_category": "SEDAN", "policy_active": True},
            expected_baseline_outcome={"eligible": False, "discount_percentage": 0.0, "discount_code": None},
            expected_proposed_outcome={"eligible": False, "discount_percentage": 0.0, "discount_code": None},  # Expected behavior should still reject!
            coverage_tags=["jurisdiction", "unsupported_state"],
            linked_rule_id="RULE-SAFE-DRIVER",
            linked_requirement_id="REQ-AUTO-DISC-001",
            created_at=now,
        ),
        RegressionTest(
            id="TEST-SD-003",
            name="High-Risk Driver in Eligible Jurisdiction",
            description="Driver in CA with high risk score 45 (> 25 threshold). Must be rejected by both versions.",
            category="NEGATIVE",
            input_data={"jurisdiction": "CA", "driver_risk_score": 45, "vehicle_category": "SEDAN", "policy_active": True},
            expected_baseline_outcome={"eligible": False, "discount_percentage": 0.0, "discount_code": None},
            expected_proposed_outcome={"eligible": False, "discount_percentage": 0.0, "discount_code": None},
            coverage_tags=["driver_risk_score", "threshold_exceeded"],
            linked_rule_id="RULE-SAFE-DRIVER",
            linked_requirement_id="REQ-AUTO-DISC-001",
            created_at=now,
        ),
        RegressionTest(
            id="TEST-SD-004",
            name="Ineligible Vehicle Category",
            description="Vehicle category COMMERCIAL_TRUCK. Must be rejected by both versions.",
            category="NEGATIVE",
            input_data={"jurisdiction": "CA", "driver_risk_score": 15, "vehicle_category": "COMMERCIAL_TRUCK", "policy_active": True},
            expected_baseline_outcome={"eligible": False, "discount_percentage": 0.0, "discount_code": None},
            expected_proposed_outcome={"eligible": False, "discount_percentage": 0.0, "discount_code": None},
            coverage_tags=["vehicle_category", "ineligible_vehicle"],
            linked_rule_id="RULE-SAFE-DRIVER",
            linked_requirement_id="REQ-AUTO-DISC-001",
            created_at=now,
        ),
        RegressionTest(
            id="TEST-SD-005",
            name="Inactive Policy Status",
            description="Policy status is inactive/lapsed (policy_active: False). Must be rejected by both versions.",
            category="NEGATIVE",
            input_data={"jurisdiction": "CA", "driver_risk_score": 15, "vehicle_category": "SEDAN", "policy_active": False},
            expected_baseline_outcome={"eligible": False, "discount_percentage": 0.0, "discount_code": None},
            expected_proposed_outcome={"eligible": False, "discount_percentage": 0.0, "discount_code": None},
            coverage_tags=["policy_active", "lapsed_status"],
            linked_rule_id="RULE-SAFE-DRIVER",
            linked_requirement_id="REQ-AUTO-DISC-001",
            created_at=now,
        ),
        RegressionTest(
            id="TEST-SD-006",
            name="Missing Jurisdiction Field",
            description="Transaction input omitted the jurisdiction key entirely.",
            category="INVALID_INPUT",
            input_data={"driver_risk_score": 15, "vehicle_category": "SEDAN", "policy_active": True},
            expected_baseline_outcome={"eligible": False, "discount_percentage": 0.0, "discount_code": None},
            expected_proposed_outcome={"eligible": False, "discount_percentage": 0.0, "discount_code": None},
            coverage_tags=["input_validation", "missing_jurisdiction"],
            linked_rule_id="RULE-SAFE-DRIVER",
            linked_requirement_id="REQ-AUTO-DISC-001",
            created_at=now,
        ),
        RegressionTest(
            id="TEST-SD-007",
            name="Risk Score Boundary Test (Score 25)",
            description="Driver risk score exactly at boundary threshold (25). Must qualify under both versions.",
            category="BOUNDARY",
            input_data={"jurisdiction": "TX", "driver_risk_score": 25, "vehicle_category": "SUV", "policy_active": True},
            expected_baseline_outcome={"eligible": True, "discount_percentage": 10.0, "discount_code": "SAFE_DRIVER_10"},
            expected_proposed_outcome={"eligible": True, "discount_percentage": 10.0, "discount_code": "SAFE_DRIVER_10"},
            coverage_tags=["driver_risk_score", "boundary_value"],
            linked_rule_id="RULE-SAFE-DRIVER",
            linked_requirement_id="REQ-AUTO-DISC-001",
            created_at=now,
        ),
        RegressionTest(
            id="TEST-SD-008",
            name="Invalid Data Format (Negative Risk Score)",
            description="Invalid data with negative telematics risk score (-5). Evaluates graceful handling.",
            category="INVALID_INPUT",
            input_data={"jurisdiction": "CA", "driver_risk_score": -5, "vehicle_category": "SEDAN", "policy_active": True},
            expected_baseline_outcome={"eligible": True, "discount_percentage": 10.0, "discount_code": "SAFE_DRIVER_10"},
            expected_proposed_outcome={"eligible": True, "discount_percentage": 10.0, "discount_code": "SAFE_DRIVER_10"},
            coverage_tags=["input_validation", "negative_numeric"],
            linked_rule_id="RULE-SAFE-DRIVER",
            linked_requirement_id="REQ-AUTO-DISC-001",
            created_at=now,
        ),
    ]

    for t in tests:
        db.add(t)

    # 8. Audit Event for Seeding
    audit = AuditEvent(
        id="AUDIT-INIT-001",
        event_type="SYSTEM_SEED",
        entity_type="SYSTEM",
        entity_id="SEED-DATA",
        actor="SEED_RUNNER",
        details={"status": "INITIALIZED", "rules": 1, "versions": 2, "tests": len(tests), "artifacts": len(artifacts_data)},
        timestamp=now,
    )
    db.add(audit)

    db.commit()
    print(f"Successfully seeded database with {len(tests)} tests, 2 rule versions, and {len(artifacts_data)} artifacts.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
