from __future__ import annotations

import pytest

from nks.application.sprint16_path_manifest import sprint16_isolation_path_manifest


SPRINT16_TESTED_PATHS = {
    "shared-store-success",
    "separated-store-success",
    "same-id-different-tenant",
    "cross-tenant-denied",
    "cross-subject-denied",
    "cross-domain-denied",
    "cross-audience-denied",
    "test-to-production-denied",
    "boundary-tamper-denied",
    "export-import-preserves-boundary",
    "duplicate-delivery-idempotent",
    "conflicting-duplicate-denied",
    "recovery-mismatch-denied",
    "path-traversal-denied",
    "forged-envelope-denied",
    "local-process-cross-tenant-denied",
    "human-policy-stricter",
    "diagnostic-redaction",
}


def test_every_declared_sprint16_path_has_automated_coverage() -> None:
    sprint16_isolation_path_manifest().assert_complete_coverage(SPRINT16_TESTED_PATHS)


def test_sprint16_coverage_gate_fails_closed_for_missing_or_unknown_paths() -> None:
    manifest = sprint16_isolation_path_manifest()
    with pytest.raises(AssertionError, match="missing paths: cross-tenant-denied"):
        manifest.assert_complete_coverage(SPRINT16_TESTED_PATHS - {"cross-tenant-denied"})
    with pytest.raises(AssertionError, match="undeclared paths: cloud-iam-certified"):
        manifest.assert_complete_coverage(SPRINT16_TESTED_PATHS | {"cloud-iam-certified"})


def test_all_sprint16_paths_are_test_only_and_prohibit_production_effects() -> None:
    manifest = sprint16_isolation_path_manifest()
    assert manifest.execution_context.value == "TEST"
    assert all("production-effect" in path.prohibited_effects for path in manifest.paths)
