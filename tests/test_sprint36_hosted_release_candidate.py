from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from nks.application.governed_transactions import canonical_sha256
from nks.application.hosted_release_candidate import (
    ConclusionKind,
    ConclusionStatus,
    DecisionState,
    EvidenceStatus,
    HostedReleaseCandidate,
    HumanDecisionDisposition,
    HumanDeploymentDecisionRequest,
    build_hosted_release_candidate,
    build_human_deployment_decision_request,
    hosted_release_candidate_fixture,
    human_deployment_decision_fixture,
)
from nks.application.production_control_readiness import ProductionControl
from nks.application.sprint36_path_manifest import sprint36_hosted_release_candidate_path_manifest
from nks.governance.approvals import ExecutionContext

ROOT = Path(__file__).resolve().parents[1]


def _conclusions(candidate):
    return {item.kind: item for item in candidate.conclusions}


def test_candidate_reports_four_separate_truthful_conclusions() -> None:
    candidate = build_hosted_release_candidate()
    conclusions = _conclusions(candidate)
    assert set(conclusions) == set(ConclusionKind)
    assert conclusions[ConclusionKind.SOFTWARE_READINESS].status == ConclusionStatus.PASS_TEST
    assert conclusions[ConclusionKind.HOSTED_ARCHITECTURE_VALIDATION].status == ConclusionStatus.BLOCKED
    assert conclusions[ConclusionKind.ZERO_COST_OPERATING_ENVELOPE].status == ConclusionStatus.PARTIAL
    assert conclusions[ConclusionKind.PRODUCTION_DEPLOYMENT_READINESS].status == ConclusionStatus.BLOCKED
    assert candidate.production_deployment_authorized is False
    assert candidate.production_approval is False


def test_candidate_preserves_actual_hosted_campaign_state() -> None:
    by_id = {item.evidence_id: item for item in build_hosted_release_candidate().evidence}
    assert by_id["SPRINT-024"].status == EvidenceStatus.COMPLETE
    assert by_id["SPRINT-025"].status == EvidenceStatus.COMPLETE
    assert by_id["SPRINT-026"].status == EvidenceStatus.BLOCKED
    assert all(by_id[f"SPRINT-{n:03d}"].status == EvidenceStatus.PLANNED for n in range(27, 31))


def test_candidate_binds_corrected_architecture_and_all_unresolved_controls() -> None:
    candidate = build_hosted_release_candidate()
    assert set(candidate.architecture_documents) == {
        "architecture/enki/enki-split-cloud-reference-architecture.md",
        "architecture/enki/enki-canonical-nine-layer-architecture.md",
    }
    assert set(candidate.unresolved_production_controls) == set(ProductionControl)
    assert len(candidate.unresolved_production_controls) == 7


def test_hosted_validation_cannot_be_changed_to_pass() -> None:
    candidate = build_hosted_release_candidate()
    payload = candidate.model_dump(mode="python")
    conclusions = list(payload["conclusions"])
    for item in conclusions:
        if item["kind"] == ConclusionKind.HOSTED_ARCHITECTURE_VALIDATION:
            item["status"] = ConclusionStatus.PASS_TEST
            item["blockers"] = ()
            item["conclusion_sha256"] = canonical_sha256(
                {k: v for k, v in item.items() if k != "conclusion_sha256"}
            )
    payload["conclusions"] = tuple(conclusions)
    payload["candidate_sha256"] = canonical_sha256(
        {k: v for k, v in payload.items() if k != "candidate_sha256"}
    )
    with pytest.raises(ValidationError):
        HostedReleaseCandidate.model_validate(payload)


def test_human_decision_request_is_pending_and_has_all_four_options() -> None:
    request = build_human_deployment_decision_request()
    assert set(request.supported_dispositions) == set(HumanDecisionDisposition)
    assert request.decision_state == DecisionState.PENDING_HUMAN_DECISION
    assert request.decision_authority == "HUMAN"
    assert request.selected_disposition is None


def test_nonhuman_process_cannot_insert_a_selected_disposition() -> None:
    request = build_human_deployment_decision_request()
    payload = request.model_dump(mode="python")
    payload["selected_disposition"] = HumanDecisionDisposition.APPROVE
    payload["request_sha256"] = canonical_sha256(
        {k: v for k, v in payload.items() if k != "request_sha256"}
    )
    with pytest.raises(ValidationError):
        HumanDeploymentDecisionRequest.model_validate(payload)


def test_release_documents_and_deterministic_manifests_exist() -> None:
    candidate = build_hosted_release_candidate()
    for path in candidate.package_documents:
        assert (ROOT / path).is_file(), path
    committed_candidate = json.loads(
        (ROOT / "releases/enki-hosted-1.0-rc2/readiness-manifest.json").read_text()
    )
    committed_decision = json.loads(
        (ROOT / "releases/enki-hosted-1.0-rc2/human-deployment-decision-request.json").read_text()
    )
    assert committed_candidate == hosted_release_candidate_fixture()
    assert committed_decision == human_deployment_decision_fixture()
    assert build_hosted_release_candidate() == build_hosted_release_candidate()


SPRINT36_TESTED_PATHS = {
    "corrected-architecture-baseline-bound",
    "software-readiness-reported-separately",
    "hosted-architecture-validation-reported-separately",
    "zero-cost-envelope-reported-separately",
    "production-deployment-readiness-reported-separately",
    "software-readiness-pass-test-only",
    "hosted-validation-blocked-incomplete-campaigns",
    "local-zero-cost-distinguished-from-hosted-envelope",
    "all-seven-production-controls-remain-unresolved",
    "production-readiness-blocked",
    "blocked-evidence-cannot-be-pass",
    "planned-evidence-cannot-be-pass",
    "production-readiness-cannot-use-test-status",
    "all-four-human-dispositions-supported",
    "decision-remains-pending-human",
    "automation-cannot-select-disposition",
    "multi-consumer-evidence-bound",
    "recovery-portability-evidence-bound",
    "performance-evidence-qualified-nonproduction",
    "known-limitations-explicit",
    "runbook-explicit",
    "rollback-plan-explicit",
    "migration-path-explicit",
    "support-boundaries-explicit",
    "independent-review-explicit",
    "release-candidate-manifest-deterministic",
    "decision-request-manifest-deterministic",
    "sprint-completion-does-not-authorize-deployment",
}


def test_declared_sprint36_paths_have_coverage_and_test_boundary() -> None:
    manifest = sprint36_hosted_release_candidate_path_manifest()
    manifest.assert_complete_coverage(SPRINT36_TESTED_PATHS)
    assert manifest.execution_context == ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "production-deployment" in path.prohibited_effects
        assert "production-approval" in path.prohibited_effects
        assert "failed-evidence-as-pass" in path.prohibited_effects
        assert "missing-evidence-as-pass" in path.prohibited_effects
        assert "automated-human-decision" in path.prohibited_effects
