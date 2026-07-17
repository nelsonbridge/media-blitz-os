from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from nks.application.hosting_direction import (
    DecisionOption,
    HostingDirectionDecisionPackage,
    ProductionPrerequisiteStatus,
    build_cross_finalist_evaluation,
    build_hosting_direction_decision_package,
)
from nks.application.hosting_options import REQUIRED_PRODUCTION_PREREQUISITES
from nks.application.sprint30_path_manifest import sprint30_hosting_direction_path_manifest
from nks.governance.approvals import ExecutionContext


ROOT = Path(__file__).resolve().parents[1]


def test_cross_finalist_evaluation_is_deterministic_and_deferred() -> None:
    first = build_cross_finalist_evaluation()
    second = build_cross_finalist_evaluation()

    assert first == second
    assert first.evaluation_sha256 == second.evaluation_sha256
    assert first.winner_option_id is None
    assert "DEFER" in first.recommendation


def test_hosting_direction_package_is_test_only_and_fail_closed() -> None:
    package = build_hosting_direction_decision_package()

    assert package.execution_context == ExecutionContext.TEST
    assert package.human_decision_required is True
    assert package.production_approval is False
    assert package.production_deployment_authorized is False
    assert package.recommended_option_id is None
    assert "DEFER" in package.recommendation


def test_package_declares_all_production_prerequisites_as_unresolved() -> None:
    package = build_hosting_direction_decision_package()

    assert {item.prerequisite_id for item in package.production_controls} == REQUIRED_PRODUCTION_PREREQUISITES
    assert all(item.status == ProductionPrerequisiteStatus.UNRESOLVED for item in package.production_controls)


def test_package_exposes_required_decision_options() -> None:
    package = build_hosting_direction_decision_package()

    assert package.decision_options == (
        DecisionOption.SELECT_RECOMMENDED,
        DecisionOption.DEFER,
        DecisionOption.REQUEST_MORE_EVIDENCE,
        DecisionOption.REJECT,
    )


def test_package_hash_tamper_fails_closed() -> None:
    package = build_hosting_direction_decision_package()
    payload = package.model_dump(mode="python")
    payload["package_sha256"] = "sha256:" + "0" * 64

    with pytest.raises(ValidationError, match="hosting direction package hash is invalid"):
        HostingDirectionDecisionPackage.model_validate(payload)


def test_contract_matches_decision_package_boundary() -> None:
    contract = json.loads(
        (ROOT / "contracts" / "enki-hosting-direction-v1.json").read_text(encoding="utf-8")
    )
    package = build_hosting_direction_decision_package()

    assert contract["contract_version"] == package.contract_version
    assert contract["execution_context"] == package.execution_context.value
    assert contract["human_decision_required"] is True
    assert contract["production_approval"] is False
    assert contract["production_deployment_authorized"] is False
    assert set(contract["required_production_prerequisites"]) == REQUIRED_PRODUCTION_PREREQUISITES
    assert contract["decision_options"] == [item.value for item in package.decision_options]


SPRINT30_TESTED_PATHS = {
    "finalist-evidence-status-explicit",
    "cross-finalist-evaluation-hash-bound",
    "recommendation-separated-from-human-approval",
    "production-prerequisites-explicit",
    "production-control-validation-sequenced",
    "migration-rollback-dr-obligations-explicit",
    "decision-options-select-defer-more-evidence-reject",
    "no-production-deployment-authorized",
    "winner-selection-with-incomplete-evidence-denied",
    "default-selection-without-human-decision-denied",
}


def test_every_declared_sprint30_path_has_automated_coverage() -> None:
    sprint30_hosting_direction_path_manifest().assert_complete_coverage(SPRINT30_TESTED_PATHS)


def test_sprint30_paths_are_test_only_and_prohibit_production_effects() -> None:
    manifest = sprint30_hosting_direction_path_manifest()
    assert manifest.execution_context == ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "production-approval" in path.prohibited_effects
        assert "default-hosting-selection" in path.prohibited_effects
        assert "unvalidated-control-promotion" in path.prohibited_effects
