from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from nks.application.governed_transactions import canonical_sha256
from nks.application.release_integrity import (
    FindingSeverity,
    ReleaseInventory,
    SupplyChainAttestation,
    build_cyclonedx_sbom,
    build_release_inventory,
    raw_file_sha256,
    scan_for_secrets,
    verify_release_integrity,
)
from nks.governance.approvals import ExecutionContext


ROOT = Path(__file__).resolve().parents[1]
RELEASE_RELATIVE = Path("releases/enki-0.1.0-rc1")
SOURCE_COMMIT = "cb84fbc8eef6096e8a707e1b922dfa2eddb23e51"


def _copy_verification_root(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    root.mkdir()
    shutil.copy2(ROOT / "pyproject.toml", root / "pyproject.toml")
    shutil.copytree(ROOT / ".github", root / ".github")
    (root / "releases").mkdir()
    shutil.copytree(ROOT / RELEASE_RELATIVE, root / RELEASE_RELATIVE)
    return root


def _codes(result: object) -> set[str]:
    return {finding.code for finding in result.findings}  # type: ignore[attr-defined]


def test_clean_room_release_verification_is_valid_and_deterministic() -> None:
    first = verify_release_integrity(
        ROOT,
        ROOT / RELEASE_RELATIVE,
        expected_source_commit=SOURCE_COMMIT,
    )
    second = verify_release_integrity(
        ROOT,
        ROOT / RELEASE_RELATIVE,
        expected_source_commit=SOURCE_COMMIT,
        expected_dependency_sha256=first.inventory.dependency_sha256 if first.inventory else None,
        expected_workflow_sha256=first.inventory.workflow_sha256 if first.inventory else None,
    )

    assert first.valid is True
    assert first.findings == []
    assert first.candidate is not None
    assert first.inventory is not None
    assert first.sbom is not None
    assert first.attestation is not None
    assert first.candidate.candidate_sha256 == (
        "sha256:96fe1533369a3d64d6914ff5eaa849babea4e874eb6fd843bf988ad693541bd5"
    )
    assert first.inventory == second.inventory
    assert first.sbom == second.sbom
    assert first.attestation == second.attestation
    assert first.attestation.execution_context == ExecutionContext.TEST
    assert first.attestation.production_credentials_used is False
    assert first.attestation.human_release_decision_issued is False


def test_dependency_workflow_and_sbom_inventories_are_deterministic() -> None:
    first = build_release_inventory(ROOT)
    second = build_release_inventory(ROOT)
    first_sbom = build_cyclonedx_sbom(first)
    second_sbom = build_cyclonedx_sbom(second)

    assert first == second
    assert first.dependencies
    assert {dependency.name for dependency in first.dependencies} >= {
        "hatchling",
        "pydantic",
        "typer",
        "pytest",
        "pytest-cov",
        "jsonschema",
    }
    assert first.workflow_actions
    assert first.dependency_sha256 == canonical_sha256(first.dependencies)
    assert first.workflow_sha256 == canonical_sha256(first.workflow_actions)
    assert first_sbom == second_sbom
    assert first_sbom["bomFormat"] == "CycloneDX"
    assert first_sbom["specVersion"] == "1.5"
    assert canonical_sha256(first_sbom).startswith("sha256:")


def test_inventory_rejects_hash_tampering() -> None:
    inventory = build_release_inventory(ROOT)
    payload = inventory.model_dump(mode="python")
    payload["dependency_sha256"] = canonical_sha256("tampered")

    with pytest.raises(ValidationError, match="dependency inventory hash"):
        ReleaseInventory.model_validate(payload)


def test_artifact_substitution_and_missing_artifact_fail_closed(tmp_path: Path) -> None:
    root = _copy_verification_root(tmp_path)
    release = root / RELEASE_RELATIVE
    (release / "calibration-report.md").write_text("substituted", encoding="utf-8")
    substituted = verify_release_integrity(root, release, expected_source_commit=SOURCE_COMMIT)

    assert substituted.valid is False
    assert substituted.attestation is None
    assert "artifact-substitution" in _codes(substituted)

    (release / "threat-model.md").unlink()
    missing = verify_release_integrity(root, release, expected_source_commit=SOURCE_COMMIT)
    assert missing.valid is False
    assert "missing-artifact" in _codes(missing)


def test_dependency_and_workflow_drift_fail_closed(tmp_path: Path) -> None:
    baseline = build_release_inventory(ROOT)
    root = _copy_verification_root(tmp_path)
    release = root / RELEASE_RELATIVE

    with (root / "pyproject.toml").open("a", encoding="utf-8") as handle:
        handle.write("\n# drift\n")
    unchanged_comment = verify_release_integrity(
        root,
        release,
        expected_source_commit=SOURCE_COMMIT,
        expected_dependency_sha256=baseline.dependency_sha256,
        expected_workflow_sha256=baseline.workflow_sha256,
    )
    assert unchanged_comment.valid is True

    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    text = text.replace('"typer>=0.12,<1",', '"typer>=0.12,<1",\n  "httpx>=0.27,<1",')
    (root / "pyproject.toml").write_text(text, encoding="utf-8")
    dependency_drift = verify_release_integrity(
        root,
        release,
        expected_source_commit=SOURCE_COMMIT,
        expected_dependency_sha256=baseline.dependency_sha256,
        expected_workflow_sha256=baseline.workflow_sha256,
    )
    assert dependency_drift.valid is False
    assert "dependency-drift" in _codes(dependency_drift)

    workflow = next((root / ".github" / "workflows").glob("*.yml"))
    with workflow.open("a", encoding="utf-8") as handle:
        handle.write("\n      - uses: actions/cache@v4\n")
    workflow_drift = verify_release_integrity(
        root,
        release,
        expected_source_commit=SOURCE_COMMIT,
        expected_dependency_sha256=build_release_inventory(root).dependency_sha256,
        expected_workflow_sha256=baseline.workflow_sha256,
    )
    assert workflow_drift.valid is False
    assert "workflow-drift" in _codes(workflow_drift)


def test_source_candidate_and_loop_receipt_tampering_fail_closed(tmp_path: Path) -> None:
    root = _copy_verification_root(tmp_path)
    release = root / RELEASE_RELATIVE

    mismatch = verify_release_integrity(
        root,
        release,
        expected_source_commit="a" * 40,
    )
    assert mismatch.valid is False
    assert "source-provenance-mismatch" in _codes(mismatch)

    candidate_path = release / "release-candidate.json"
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    candidate["candidate_sha256"] = canonical_sha256("tampered")
    candidate_path.write_text(json.dumps(candidate, indent=2), encoding="utf-8")
    candidate_tamper = verify_release_integrity(root, release)
    assert candidate_tamper.valid is False
    assert "invalid-candidate" in _codes(candidate_tamper)

    shutil.rmtree(root)
    root = _copy_verification_root(tmp_path)
    release = root / RELEASE_RELATIVE
    receipt_path = release / "publication-loop-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["subject_id"] = "PUB-TAMPERED"
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    receipt_tamper = verify_release_integrity(root, release)
    assert receipt_tamper.valid is False
    assert "loop-receipt-tamper" in _codes(receipt_tamper)
    assert "loop-receipt-manifest-mismatch" in _codes(receipt_tamper)


def test_populated_human_release_decision_is_rejected(tmp_path: Path) -> None:
    root = _copy_verification_root(tmp_path)
    release = root / RELEASE_RELATIVE
    decision_path = release / "human-release-decision.md"
    decision = decision_path.read_text(encoding="utf-8")
    decision = decision.replace("Decision: **Not recorded**", "Decision: **APPROVE**")
    decision = decision.replace("Decided by: **Not recorded**", "Decided by: **system**")
    decision_path.write_text(decision, encoding="utf-8")

    result = verify_release_integrity(root, release)
    assert result.valid is False
    assert "self-issued-release-decision" in _codes(result)
    assert "artifact-substitution" in _codes(result)


@pytest.mark.parametrize(
    ("secret", "secret_type"),
    [
        ("AKIAABCDEFGHIJKLMNOP", "aws-access-key"),
        ("ghp_abcdefghijklmnopqrstuvwxyzABCDEFGHIJ", "github-token"),
        ("github_pat_abcdefghijklmnopqrstuvwxyz012345", "github-fine-grained-token"),
        ("sk-proj-abcdefghijklmnopqrstuvwxyz012345", "openai-key"),
        ("-----BEGIN PRIVATE KEY-----", "private-key"),
    ],
)
def test_secret_leakage_fails_closed(
    tmp_path: Path,
    secret: str,
    secret_type: str,
) -> None:
    root = _copy_verification_root(tmp_path)
    release = root / RELEASE_RELATIVE
    leaked = release / "leaked-secret.txt"
    leaked.write_text(secret, encoding="utf-8")

    findings = scan_for_secrets([release], root)
    assert any(secret_type in finding.message for finding in findings)
    assert all(finding.severity == FindingSeverity.ERROR for finding in findings)

    result = verify_release_integrity(root, release)
    assert result.valid is False
    assert "secret-leak" in _codes(result)


def test_secret_scanner_skips_binary_files(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    binary = root / "binary.dat"
    binary.write_bytes(b"\xff\xfe\xfdAKIAABCDEFGHIJKLMNOP")
    assert scan_for_secrets([binary], root) == []


def test_invalid_inventory_and_missing_candidate_fail_closed(tmp_path: Path) -> None:
    root = _copy_verification_root(tmp_path)
    release = root / RELEASE_RELATIVE
    (root / "pyproject.toml").write_text("not = [valid", encoding="utf-8")
    (release / "release-candidate.json").unlink()

    result = verify_release_integrity(root, release)
    assert result.valid is False
    assert result.inventory is None
    assert result.sbom is None
    assert result.attestation is None
    assert {"invalid-inventory", "missing-candidate"} <= _codes(result)


def test_supply_chain_attestation_cannot_claim_production_or_self_approval() -> None:
    result = verify_release_integrity(ROOT, ROOT / RELEASE_RELATIVE)
    assert result.valid is True
    assert result.attestation is not None
    payload = result.attestation.model_dump(mode="python")

    payload["production_credentials_used"] = True
    payload["attestation_sha256"] = canonical_sha256(
        {key: value for key, value in payload.items() if key != "attestation_sha256"}
    )
    with pytest.raises(ValidationError, match="production credentials"):
        SupplyChainAttestation.model_validate(payload)

    payload = result.attestation.model_dump(mode="python")
    payload["human_release_decision_issued"] = True
    payload["attestation_sha256"] = canonical_sha256(
        {key: value for key, value in payload.items() if key != "attestation_sha256"}
    )
    with pytest.raises(ValidationError, match="human decision"):
        SupplyChainAttestation.model_validate(payload)

    payload = result.attestation.model_dump(mode="python")
    payload["attestation_sha256"] = canonical_sha256("tampered")
    with pytest.raises(ValidationError, match="attestation hash"):
        SupplyChainAttestation.model_validate(payload)


def test_raw_file_hash_matches_standard_sha256(tmp_path: Path) -> None:
    path = tmp_path / "artifact.txt"
    path.write_bytes(b"Enki")
    assert raw_file_sha256(path) == (
        "sha256:9071d562a9f5ae26c40acb62ee1d7b43a40b6497acd7ac5b4f91571360b7ba1e"
    )
