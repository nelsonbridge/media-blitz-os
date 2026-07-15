from __future__ import annotations

import pytest

from nks.application.sprint15_path_manifest import sprint15_performance_path_manifest


SPRINT15_TESTED_PATHS = {
    "transaction-benchmark",
    "state-write-benchmark",
    "reconciliation-benchmark",
    "transition-benchmark",
    "model-use-benchmark",
    "reconstruction-benchmark",
    "portability-benchmark",
    "latency-budget",
    "throughput-budget",
    "memory-budget",
    "storage-growth-budget",
    "recovery-cost-budget",
    "error-rate-budget",
    "overload-denied",
    "private-data-denied",
    "production-data-denied",
    "production-context-denied",
    "production-capacity-claim-denied",
}


def test_every_declared_sprint15_path_has_automated_coverage() -> None:
    sprint15_performance_path_manifest().assert_complete_coverage(SPRINT15_TESTED_PATHS)


def test_sprint15_coverage_gate_rejects_missing_and_unknown_paths() -> None:
    manifest = sprint15_performance_path_manifest()
    with pytest.raises(AssertionError, match="missing paths: overload-denied"):
        manifest.assert_complete_coverage(SPRINT15_TESTED_PATHS - {"overload-denied"})
    with pytest.raises(AssertionError, match="undeclared paths: production-guarantee"):
        manifest.assert_complete_coverage(SPRINT15_TESTED_PATHS | {"production-guarantee"})


def test_sprint15_paths_are_test_only_and_prohibit_production_effects() -> None:
    manifest = sprint15_performance_path_manifest()
    assert manifest.execution_context.value == "TEST"
    assert all("production-effect" in item.prohibited_effects for item in manifest.paths)
