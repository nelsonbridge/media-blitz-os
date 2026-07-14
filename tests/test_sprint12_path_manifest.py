from __future__ import annotations

import pytest

from nks.application.sprint12_path_manifest import sprint12_path_manifest


TESTED_PATHS = {
    "reconstruction-complete",
    "reconstruction-incomplete",
    "reconstruction-repairable",
    "reconstruction-rolled-back",
    "reconstruction-conflict",
    "corrupt-record-hash",
    "stale-plan-hash",
    "cross-context-record",
    "authority-class-mismatch",
    "all-operation-families",
    "portable-export-import",
    "portable-exact-replay",
    "portable-conflicting-import",
    "test-to-production-import",
    "clean-room-recovery",
    "disaster-recovery-exact-retry",
    "filesystem-github-parity",
    "unsupported-delete-denied",
    "unsupported-replace-denied",
    "work-completion-commit",
    "work-completion-missing-evidence",
    "work-completion-stale-before",
    "work-completion-before-consumption",
    "work-completion-after-consumption",
    "work-completion-partial-write-recovery",
}


def test_every_sprint12_path_has_automated_coverage() -> None:
    sprint12_path_manifest().assert_complete_coverage(TESTED_PATHS)


def test_sprint12_coverage_fails_when_declared_path_is_missing() -> None:
    with pytest.raises(AssertionError, match="missing paths: clean-room-recovery"):
        sprint12_path_manifest().assert_complete_coverage(TESTED_PATHS - {"clean-room-recovery"})


def test_sprint12_coverage_rejects_undeclared_path() -> None:
    with pytest.raises(AssertionError, match="undeclared paths: invented"):
        sprint12_path_manifest().assert_complete_coverage(TESTED_PATHS | {"invented"})
