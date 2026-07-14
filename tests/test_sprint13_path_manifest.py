from __future__ import annotations

import pytest

from nks.application.sprint13_path_manifest import sprint13_path_manifest
from nks.governance.approvals import ExecutionContext


def test_sprint13_manifest_declares_complete_internal_test_surface() -> None:
    manifest = sprint13_path_manifest()

    assert manifest.execution_context == ExecutionContext.TEST
    assert manifest.operation_family == "enki-integrated-test-proof-release-candidate"
    assert len(manifest.paths) == len(manifest.declared_path_ids)
    assert {
        "publication-loop-success",
        "nonpublication-loop-success",
        "interruption-before-consumption",
        "interruption-after-effect",
        "synthetic-feedback-accepted",
        "controlled-real-test-feedback-accepted",
        "replay-feedback-attributed",
        "duplicate-feedback",
        "conflicting-feedback-id",
        "zero-response-window",
        "forensic-reconstruction-complete",
        "release-candidate-two-lane",
        "release-decision-human-only",
        "test-evidence-cannot-satisfy-production",
    } <= manifest.declared_path_ids
    assert all(
        "production-effect" in path.prohibited_effects for path in manifest.paths
    )
    assert all(
        "audience-widening" in path.prohibited_effects for path in manifest.paths
    )


def test_sprint13_manifest_accepts_exact_path_coverage() -> None:
    manifest = sprint13_path_manifest()
    manifest.assert_complete_coverage(manifest.declared_path_ids)


def test_sprint13_manifest_rejects_missing_and_undeclared_paths() -> None:
    manifest = sprint13_path_manifest()
    observed = set(manifest.declared_path_ids)
    observed.remove("publication-loop-success")
    observed.add("undeclared-production-effect")

    with pytest.raises(AssertionError) as exc:
        manifest.assert_complete_coverage(observed)

    assert "missing paths: publication-loop-success" in str(exc.value)
    assert "undeclared paths: undeclared-production-effect" in str(exc.value)
