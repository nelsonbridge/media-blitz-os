from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from nks.application.governed_transactions import canonical_sha256
from nks.application.hosting_direction import (
    CrossFinalistEvaluation,
    FinalistEvaluationResult,
    FinalistEvidenceState,
    RecommendationConfidence,
    build_cross_finalist_evaluation,
)
from nks.application.hosting_validation import FINALISTS
from nks.application.sprint29_path_manifest import sprint29_cross_finalist_path_manifest
from nks.governance.approvals import ExecutionContext


ROOT = Path(__file__).resolve().parents[1]


def test_cross_finalist_evaluation_is_deterministic() -> None:
    first = build_cross_finalist_evaluation()
    second = build_cross_finalist_evaluation()

    assert first == second
    assert first.evaluation_sha256 == second.evaluation_sha256
    assert tuple(item.option_id for item in first.finalist_results) == FINALISTS


def test_incomplete_evidence_forces_defer_and_no_winner() -> None:
    evaluation = build_cross_finalist_evaluation()

    assert any(item.state != FinalistEvidenceState.COMPLETE for item in evaluation.finalist_results)
    assert evaluation.winner_option_id is None
    assert "DEFER" in evaluation.recommendation


def test_winner_is_rejected_when_evidence_is_incomplete() -> None:
    evaluation = build_cross_finalist_evaluation()
    payload = evaluation.model_dump(mode="python")
    payload["winner_option_id"] = "CF-NEON-R2"
    payload["evaluation_sha256"] = canonical_sha256(
        {k: v for k, v in payload.items() if k != "evaluation_sha256"}
    )

    with pytest.raises(ValidationError, match="winner cannot be selected"):
        CrossFinalistEvaluation.model_validate(payload)


def test_non_defer_recommendation_is_rejected_when_incomplete() -> None:
    evaluation = build_cross_finalist_evaluation()
    payload = evaluation.model_dump(mode="python")
    payload["recommendation"] = "SELECT CF-NEON-R2"
    payload["evaluation_sha256"] = canonical_sha256(
        {k: v for k, v in payload.items() if k != "evaluation_sha256"}
    )

    with pytest.raises(ValidationError, match="must preserve an explicit defer recommendation"):
        CrossFinalistEvaluation.model_validate(payload)


def test_cross_finalist_contract_matches_runtime_model_boundary() -> None:
    contract = json.loads(
        (ROOT / "contracts" / "enki-cross-finalist-evaluation-v1.json").read_text(
            encoding="utf-8"
        )
    )
    evaluation = build_cross_finalist_evaluation()

    assert contract["contract_version"] == evaluation.contract_version
    assert contract["execution_context"] == evaluation.execution_context.value
    assert contract["external_services_budget_usd"] == evaluation.external_services_budget_usd
    assert tuple(contract["expected_finalists"]) == FINALISTS
    assert tuple(contract["required_comparison_dimensions"]) == evaluation.comparison_dimensions


SPRINT29_TESTED_PATHS = {
    "all-finalists-reported-in-canonical-order",
    "comparison-dimensions-explicit",
    "incomplete-evidence-preserves-deferral",
    "recommendation-separate-from-human-decision",
    "evaluation-hash-bound",
    "production-prerequisites-remain-unresolved",
    "winner-selection-with-incomplete-evidence-denied",
    "non-defer-recommendation-with-incomplete-evidence-denied",
}


def test_every_declared_sprint29_path_has_automated_coverage() -> None:
    sprint29_cross_finalist_path_manifest().assert_complete_coverage(SPRINT29_TESTED_PATHS)


def test_sprint29_paths_are_test_only_and_prohibit_unsafe_effects() -> None:
    manifest = sprint29_cross_finalist_path_manifest()
    assert manifest.execution_context == ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "default-hosting-selection" in path.prohibited_effects
        assert "silent-evidence-substitution" in path.prohibited_effects
        assert "unvalidated-control-promotion" in path.prohibited_effects
