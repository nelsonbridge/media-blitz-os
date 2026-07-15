from __future__ import annotations

import pytest

from nks.application.sprint18_path_manifest import sprint18_observability_path_manifest


SPRINT18_TESTED_PATHS = {
    "health-event",
    "metric-event",
    "trace-event",
    "diagnostic-event",
    "stable-correlation",
    "loss-detected",
    "duplicate-detected",
    "hash-conflict-detected",
    "correlation-break-detected",
    "incident-reconstructed",
    "exact-duplicate-idempotent",
    "protected-content-denied",
    "human-state-denied",
    "secret-denied",
    "unbounded-metadata-denied",
    "production-context-denied",
    "identity-conflict-denied",
    "telemetry-tamper-denied",
}


def test_every_declared_sprint18_path_has_automated_coverage() -> None:
    sprint18_observability_path_manifest().assert_complete_coverage(SPRINT18_TESTED_PATHS)


def test_sprint18_coverage_gate_rejects_missing_and_unknown_paths() -> None:
    manifest = sprint18_observability_path_manifest()
    with pytest.raises(AssertionError, match="missing paths: secret-denied"):
        manifest.assert_complete_coverage(SPRINT18_TESTED_PATHS - {"secret-denied"})
    with pytest.raises(AssertionError, match="undeclared paths: emit-human-payload"):
        manifest.assert_complete_coverage(SPRINT18_TESTED_PATHS | {"emit-human-payload"})


def test_sprint18_paths_are_test_only_and_prohibit_protected_content() -> None:
    manifest = sprint18_observability_path_manifest()
    assert manifest.execution_context.value == "TEST"
    assert all("production-effect" in item.prohibited_effects for item in manifest.paths)
    assert all("protected-content-telemetry" in item.prohibited_effects for item in manifest.paths)
