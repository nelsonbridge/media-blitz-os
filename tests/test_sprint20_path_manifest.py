from __future__ import annotations

import pytest

from nks.application.sprint20_path_manifest import sprint20_concurrency_path_manifest


SPRINT20_TESTED_PATHS = {
    "exclusive-lease-acquired",
    "concurrent-cas-one-winner",
    "competing-cas-conflict",
    "split-authority-denied",
    "stale-lease-denied",
    "exact-duplicate-no-effect",
    "delivery-id-conflict",
    "intent-id-conflict",
    "partition-delivery-deferred",
    "out-of-order-delivery-reordered",
    "partition-healed",
    "partition-contention-receipted",
    "interrupted-after-effect-recovered",
    "lost-receipt-detected",
    "complete-reconstruction",
    "pending-reconstruction",
    "conflict-reconstruction",
    "repairable-reconstruction",
    "filesystem-github-adapter-parity",
    "adapter-exact-retry-idempotent",
    "github-adapter-interruption-recovered",
    "adapter-immutable-conflict-denied",
    "adapter-incomplete-reconstruction",
    "intent-tamper-denied",
    "production-context-denied",
}


def test_every_declared_sprint20_path_has_automated_coverage() -> None:
    sprint20_concurrency_path_manifest().assert_complete_coverage(SPRINT20_TESTED_PATHS)


def test_sprint20_coverage_gate_rejects_missing_and_unknown_paths() -> None:
    manifest = sprint20_concurrency_path_manifest()
    with pytest.raises(AssertionError, match="missing paths: split-authority-denied"):
        manifest.assert_complete_coverage(SPRINT20_TESTED_PATHS - {"split-authority-denied"})
    with pytest.raises(AssertionError, match="undeclared paths: duplicate-production-effect"):
        manifest.assert_complete_coverage(SPRINT20_TESTED_PATHS | {"duplicate-production-effect"})


def test_sprint20_paths_are_test_only_and_prohibit_split_or_duplicate_effects() -> None:
    manifest = sprint20_concurrency_path_manifest()
    assert manifest.execution_context.value == "TEST"
    assert all("production-effect" in item.prohibited_effects for item in manifest.paths)
    assert all("split-authority" in item.prohibited_effects for item in manifest.paths)
    assert all("duplicate-effect" in item.prohibited_effects for item in manifest.paths)
