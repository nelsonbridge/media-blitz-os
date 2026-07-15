from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from nks.application.readiness_decision import (
    CANDIDATE_VERSION,
    PRIOR_EVIDENCE_COMMIT,
    DecisionState,
    ProductionControlStatus,
    ProductionPrerequisite,
    ReadinessManifest,
    build_readiness_manifest,
)
from nks.application.sprint23_path_manifest import sprint23_readiness_path_manifest
from nks.governance.approvals import ExecutionContext


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "releases" / "enki-1.0-candidate"


def test_committed_readiness_manifest_matches_deterministic_model() -> None:
    committed = ReadinessManifest.model_validate_json(
        (PACKAGE / "readiness-manifest.json").read_text(encoding="utf-8")
    )
    expected = build_readiness_manifest()

    assert committed == expected
    assert committed.manifest_sha256 == expected.manifest_sha256
    assert committed.candidate_version == CANDIDATE_VERSION
    assert committed.prior_evidence_commit == PRIOR_EVIDENCE_COMMIT


def test_manifest_anchors_every_prior_sprint_exactly_once() -> None:
    manifest = build_readiness_manifest()
    sprint_ids = [item.sprint_id for item in manifest.prior_sprint_evidence]

    assert sprint_ids == [f"NKS-SPR-{index:03d}" for index in range(1, 23)]
    assert len(set(sprint_ids)) == 22
    assert all(item.source_commit == PRIOR_EVIDENCE_COMMIT for item in manifest.prior_sprint_evidence)
    assert all(item.evidence_count >= 1 for item in manifest.prior_sprint_evidence)
    assert next(item for item in manifest.prior_sprint_evidence if item.sprint_id == "NKS-SPR-003").status == "superseded"


def test_campaign_matrix_is_explicit_and_test_qualified() -> None:
    manifest = build_readiness_manifest()
    expected = {
        "adversarial",
        "chaos",
        "recovery",
        "privacy",
        "logical-isolation",
        "compatibility",
        "supply-chain",
    }

    assert {item.campaign for item in manifest.campaigns} == expected
    assert all(item.status.value == "PASS_TEST" for item in manifest.campaigns)
    assert all(item.qualification == "TEST_EVIDENCE_ONLY" for item in manifest.campaigns)


def test_all_required_production_controls_remain_explicitly_unresolved() -> None:
    manifest = build_readiness_manifest()
    expected = {
        "cloud-iam",
        "production-identity-federation",
        "managed-database-row-level-isolation",
        "network-segmentation",
        "per-tenant-production-key-management",
        "production-secrets-management",
        "independent-penetration-testing",
    }

    assert {item.control for item in manifest.production_prerequisites} == expected
    assert all(item.status == ProductionControlStatus.UNRESOLVED for item in manifest.production_prerequisites)
    assert all(item.evidence_refs == [] for item in manifest.production_prerequisites)
    assert manifest.external_services_budget_usd == 0
    assert manifest.production_certification is False
    assert manifest.multitenancy_accreditation is False
    assert manifest.production_approval is False
    assert manifest.decision_state == DecisionState.HUMAN_DECISION_REQUIRED


def test_local_test_scope_cannot_be_read_as_production_certification() -> None:
    statement = build_readiness_manifest().local_test_scope_statement.lower()
    assert "not production infrastructure certification" in statement
    assert "not production infrastructure certification" in statement
    assert "multitenancy accreditation" in statement


def test_all_decision_package_documents_exist_and_preserve_nonapproval_boundary() -> None:
    manifest = build_readiness_manifest()
    for relative in manifest.package_documents:
        path = ROOT / relative
        assert path.exists()
        assert path.read_text(encoding="utf-8").strip()

    overview = (PACKAGE / "README.md").read_text(encoding="utf-8")
    limitations = (PACKAGE / "known-limitations.md").read_text(encoding="utf-8")
    runbook = (PACKAGE / "operating-runbook.md").read_text(encoding="utf-8")
    rollback = (PACKAGE / "rollback-plan.md").read_text(encoding="utf-8")
    support = (PACKAGE / "support-boundaries.md").read_text(encoding="utf-8")
    checklist = (PACKAGE / "independent-review-checklist.md").read_text(encoding="utf-8")
    decision = (PACKAGE / "human-decision-request.md").read_text(encoding="utf-8")

    assert "HUMAN_DECISION_REQUIRED" in overview
    assert "Production approval: **NO**" in overview
    for control in [
        "Cloud IAM",
        "Production identity federation",
        "Managed database row-level isolation",
        "Network segmentation",
        "Per-tenant production key management",
        "Production secrets management",
        "Independent penetration testing",
    ]:
        assert control in limitations
    assert "Entry conditions for production-control validation" in runbook
    assert "There is no approved production deployment to roll back" in rollback
    assert "Not supported or not validated for production" in support
    assert "independent human reviewer" in checklist
    assert "do not self-certify" in checklist
    assert "Decision status: **UNRESOLVED**" in decision
    assert "does not approve production deployment" in decision
    assert "Silence is not approval" in decision


def test_manifest_tamper_fails_closed() -> None:
    payload = json.loads((PACKAGE / "readiness-manifest.json").read_text(encoding="utf-8"))
    payload["manifest_sha256"] = "sha256:" + "0" * 64
    with pytest.raises(ValidationError, match="readiness manifest hash is invalid"):
        ReadinessManifest.model_validate(payload)


def test_validated_production_control_without_evidence_fails_closed() -> None:
    with pytest.raises(ValidationError, match="validated production control requires qualifying evidence"):
        ProductionPrerequisite(
            control="cloud-iam",
            status=ProductionControlStatus.VALIDATED,
            evidence_refs=[],
            rationale="invalid unsupported validation claim",
        )


SPRINT23_TESTED_PATHS = {
    "all-prior-sprint-evidence-anchored",
    "campaign-matrix-explicit",
    "known-limitations-complete",
    "production-prerequisites-explicit",
    "zero-external-services-budget-preserved",
    "local-test-proof-not-production-certification",
    "operating-runbook-present",
    "rollback-plan-present",
    "support-boundaries-present",
    "independent-review-no-self-certification",
    "enki-1.0-candidate-versioned",
    "human-decision-request-unresolved",
    "manifest-tamper-denied",
    "validated-control-without-evidence-denied",
}


def test_every_declared_sprint23_path_has_automated_coverage() -> None:
    sprint23_readiness_path_manifest().assert_complete_coverage(SPRINT23_TESTED_PATHS)


def test_sprint23_paths_are_test_only_and_prohibit_self_certification() -> None:
    manifest = sprint23_readiness_path_manifest()
    assert manifest.execution_context == ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "production-approval" in path.prohibited_effects
        assert "self-certification" in path.prohibited_effects
        assert "multitenancy-accreditation" in path.prohibited_effects
        assert "unvalidated-control-promotion" in path.prohibited_effects
