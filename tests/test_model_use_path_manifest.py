from __future__ import annotations

import pytest

from nks.application.model_use_path_manifest import model_use_path_manifest


TESTED_MODEL_USE_PATHS = {
    "exact-include",
    "missing-directive-defer",
    "retracted-withhold",
    "expired-withhold",
    "superseded-withhold",
    "inapplicable-withhold",
    "disputed-defer",
    "unknown-confidence-defer",
    "low-confidence-defer",
    "moderate-confidence-include",
    "high-confidence-include",
    "consent-denied-withhold",
    "consent-revoked-withhold",
    "consent-unknown-withhold",
    "item-expiry-withhold",
    "item-revocation-withhold",
    "purpose-withhold",
    "internal-external-withhold",
    "private-external-withhold",
    "restricted-withhold",
    "redaction-withhold",
    "transition-choice-required",
    "transition-explicit-exclusion",
    "transition-explicit-inclusion",
    "duplicate-item-id",
    "duplicate-directive-id",
    "duplicate-directive",
    "absent-item-directive",
    "directive-purpose-withhold",
    "directive-audience-withhold",
    "directive-context-withhold",
    "directive-expiry-withhold",
    "directive-revocation-withhold",
    "directive-explicit-exclusion",
    "package-context-substitution",
    "package-tamper",
    "exact-package-revocation",
    "revocation-hash-conflict",
    "test-no-effect-dispatch",
    "test-dispatcher-production-rejection",
    "production-dispatcher-test-rejection",
    "production-shaped-fake-transport",
    "test-effect-invariant",
    "append-only-package-effect-revocation",
    "immutable-package-conflict",
    "immutable-revocation-conflict",
}


def test_every_declared_model_use_path_has_automated_coverage() -> None:
    model_use_path_manifest().assert_complete_coverage(TESTED_MODEL_USE_PATHS)


def test_model_use_coverage_fails_when_a_path_is_missing() -> None:
    with pytest.raises(AssertionError, match="missing paths: package-tamper"):
        model_use_path_manifest().assert_complete_coverage(
            TESTED_MODEL_USE_PATHS - {"package-tamper"}
        )


def test_model_use_coverage_fails_for_undeclared_paths() -> None:
    with pytest.raises(AssertionError, match="undeclared paths: invented"):
        model_use_path_manifest().assert_complete_coverage(
            TESTED_MODEL_USE_PATHS | {"invented"}
        )
