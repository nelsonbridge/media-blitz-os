from __future__ import annotations

import pytest

from nks.application.sprint17_path_manifest import sprint17_policy_path_manifest


SPRINT17_TESTED_PATHS = {
    "immutable-version-created",
    "deterministic-comparison",
    "side-effect-free-simulation",
    "approval-bound-activation",
    "approval-bound-rollback",
    "approval-bound-retirement",
    "historical-policy-attribution",
    "exact-retry-idempotent",
    "invalid-version-link-denied",
    "bundle-tamper-denied",
    "cross-boundary-comparison-denied",
    "production-simulation-denied",
    "test-activation-of-production-denied",
    "immutable-conflict-denied",
}


def test_every_declared_sprint17_path_has_automated_coverage() -> None:
    sprint17_policy_path_manifest().assert_complete_coverage(SPRINT17_TESTED_PATHS)


def test_sprint17_coverage_gate_rejects_missing_and_unknown_paths() -> None:
    manifest = sprint17_policy_path_manifest()
    with pytest.raises(AssertionError, match="missing paths: approval-bound-rollback"):
        manifest.assert_complete_coverage(SPRINT17_TESTED_PATHS - {"approval-bound-rollback"})
    with pytest.raises(AssertionError, match="undeclared paths: replace-production-policy"):
        manifest.assert_complete_coverage(SPRINT17_TESTED_PATHS | {"replace-production-policy"})


def test_sprint17_paths_are_test_only_and_prohibit_production_effects() -> None:
    manifest = sprint17_policy_path_manifest()
    assert manifest.execution_context.value == "TEST"
    assert all("production-effect" in item.prohibited_effects for item in manifest.paths)
