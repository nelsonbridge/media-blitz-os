from __future__ import annotations

import pytest

from nks.application.transition_path_manifest import transition_path_manifest


TESTED_TRANSITION_PATHS = {
    "type-correction",
    "type-refinement",
    "type-supersession",
    "type-retraction",
    "type-reversal",
    "type-expansion",
    "type-restriction",
    "type-confidence-change",
    "type-context-shift",
    "type-merge",
    "type-split",
    "type-deprecation",
    "invalid-cardinality",
    "unknown-from-state",
    "stale-input",
    "branch-denied",
    "branch-accepted",
    "overlap-accepted",
    "authority-conflict-denied",
    "authority-conflict-accepted",
    "cycle",
    "contradiction",
    "context-mismatch",
    "test-production-authority-mismatch",
    "plan-tamper",
    "persistence-interruption",
    "cross-transaction-replay",
    "immutable-record-conflict",
    "person-regression",
    "reconstruction-complete",
    "reconstruction-incomplete",
    "reconstruction-repairable",
    "reconstruction-conflict",
    "reconstruction-rolled-back",
}


def test_every_declared_transition_path_has_automated_coverage() -> None:
    transition_path_manifest().assert_complete_coverage(TESTED_TRANSITION_PATHS)


def test_transition_coverage_fails_when_a_path_is_missing() -> None:
    with pytest.raises(AssertionError, match="missing paths: cycle"):
        transition_path_manifest().assert_complete_coverage(
            TESTED_TRANSITION_PATHS - {"cycle"}
        )


def test_transition_coverage_fails_for_undeclared_paths() -> None:
    with pytest.raises(AssertionError, match="undeclared paths: invented"):
        transition_path_manifest().assert_complete_coverage(
            TESTED_TRANSITION_PATHS | {"invented"}
        )
