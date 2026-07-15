from __future__ import annotations

import pytest

from nks.application.sprint19_path_manifest import sprint19_retention_path_manifest


SPRINT19_TESTED_PATHS = {
    "versioned-policy-created",
    "archive-receipted",
    "restriction-receipted",
    "redaction-receipted",
    "tombstone-receipted",
    "expiration-receipted",
    "revocation-receipted",
    "restore-allowed-state",
    "exact-retry-idempotent",
    "historical-lineage-preserved",
    "downstream-control-denied",
    "hash-continuity-proved",
    "hash-tamper-detected",
    "unsupported-algorithm-denied",
    "premature-archive-denied",
    "premature-expiry-denied",
    "authority-mismatch-denied",
    "purpose-mismatch-denied",
    "boundary-mismatch-denied",
    "unpermitted-action-denied",
    "terminal-state-rewrite-denied",
    "immutable-conflict-denied",
}


def test_every_declared_sprint19_path_has_automated_coverage() -> None:
    sprint19_retention_path_manifest().assert_complete_coverage(SPRINT19_TESTED_PATHS)


def test_sprint19_coverage_gate_rejects_missing_and_unknown_paths() -> None:
    manifest = sprint19_retention_path_manifest()
    with pytest.raises(AssertionError, match="missing paths: hash-continuity-proved"):
        manifest.assert_complete_coverage(SPRINT19_TESTED_PATHS - {"hash-continuity-proved"})
    with pytest.raises(AssertionError, match="undeclared paths: erase-history"):
        manifest.assert_complete_coverage(SPRINT19_TESTED_PATHS | {"erase-history"})


def test_sprint19_paths_are_test_only_and_prohibit_historical_rewrite() -> None:
    manifest = sprint19_retention_path_manifest()
    assert manifest.execution_context.value == "TEST"
    assert all("production-effect" in item.prohibited_effects for item in manifest.paths)
    assert all("historical-rewrite" in item.prohibited_effects for item in manifest.paths)
