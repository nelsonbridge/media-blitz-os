from __future__ import annotations

import pytest

from nks.application.sprint14_path_manifest import sprint14_path_manifest
from nks.governance.approvals import ExecutionContext


def test_sprint14_manifest_declares_complete_supply_chain_surface() -> None:
    manifest = sprint14_path_manifest()

    assert manifest.execution_context == ExecutionContext.TEST
    assert manifest.operation_family == "enki-reproducible-release-supply-chain-integrity"
    assert len(manifest.paths) == len(manifest.declared_path_ids)
    assert {
        "clean-room-success",
        "exact-candidate-regeneration",
        "dependency-inventory-deterministic",
        "workflow-inventory-deterministic",
        "sbom-deterministic",
        "attestation-deterministic",
        "artifact-substitution",
        "missing-artifact",
        "dependency-drift",
        "workflow-drift",
        "source-provenance-mismatch",
        "candidate-hash-tamper",
        "loop-receipt-tamper",
        "secret-aws",
        "secret-github",
        "secret-openai",
        "private-key-leak",
        "release-decision-populated",
        "production-credential-not-required",
        "test-evidence-cannot-authorize-release",
    } <= manifest.declared_path_ids
    assert all(
        "production-credential-use" in path.prohibited_effects for path in manifest.paths
    )
    assert all("release-self-approval" in path.prohibited_effects for path in manifest.paths)


def test_sprint14_manifest_accepts_exact_path_coverage() -> None:
    manifest = sprint14_path_manifest()
    manifest.assert_complete_coverage(manifest.declared_path_ids)


def test_sprint14_manifest_rejects_missing_and_undeclared_paths() -> None:
    manifest = sprint14_path_manifest()
    observed = set(manifest.declared_path_ids)
    observed.remove("clean-room-success")
    observed.add("undeclared-production-release")

    with pytest.raises(AssertionError) as exc:
        manifest.assert_complete_coverage(observed)

    assert "missing paths: clean-room-success" in str(exc.value)
    assert "undeclared paths: undeclared-production-release" in str(exc.value)
