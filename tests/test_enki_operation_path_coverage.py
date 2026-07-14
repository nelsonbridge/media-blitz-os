from __future__ import annotations

import pytest

from nks.application.enki_path_manifests import (
    disclosure_path_manifest,
    human_migration_path_manifest,
    reconciliation_path_manifest,
    state_write_path_manifest,
)


STATE_WRITE_TESTED_PATHS = {
    "person-success",
    "organization-success",
    "project-success",
    "partial-write",
    "unknown-reference",
    "subject-leakage",
    "plan-tamper",
}

HUMAN_MIGRATION_TESTED_PATHS = {
    "success",
    "partial-write",
    "consent-denied",
    "consent-unknown",
    "purpose-mismatch",
    "policy-expired",
    "policy-revoked",
    "missing-origin",
    "unknown-transition-endpoint",
    "semantic-tamper",
}

RECONCILIATION_TESTED_PATHS = {
    "applicable",
    "future",
    "retracted",
    "historical",
    "disputed",
    "context-mismatch",
    "ineligible-endpoint",
    "persistence-interruption",
}

DISCLOSURE_TESTED_PATHS = {
    "subject-requested",
    "subject-not-requested",
    "consent-revoked",
    "private-public",
    "redaction-required",
    "policy-revoked",
    "receipt-interruption",
    "approval-hash-mismatch",
}


@pytest.mark.parametrize(
    ("manifest_factory", "tested_paths"),
    [
        (state_write_path_manifest, STATE_WRITE_TESTED_PATHS),
        (human_migration_path_manifest, HUMAN_MIGRATION_TESTED_PATHS),
        (reconciliation_path_manifest, RECONCILIATION_TESTED_PATHS),
        (disclosure_path_manifest, DISCLOSURE_TESTED_PATHS),
    ],
)
def test_every_declared_enki_operation_path_has_automated_coverage(
    manifest_factory,
    tested_paths: set[str],
) -> None:
    manifest_factory().assert_complete_coverage(tested_paths)


def test_coverage_gate_fails_when_a_declared_path_is_removed_from_tests() -> None:
    with pytest.raises(AssertionError, match="missing paths: partial-write"):
        state_write_path_manifest().assert_complete_coverage(
            STATE_WRITE_TESTED_PATHS - {"partial-write"}
        )
