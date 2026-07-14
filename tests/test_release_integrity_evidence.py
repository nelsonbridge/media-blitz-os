from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMMITTED = ROOT / "releases" / "enki-0.1.0-rc1" / "integrity"
FILES = {
    "dependency-inventory.json",
    "workflow-inventory.json",
    "sbom.json",
    "supply-chain-attestation.json",
    "provenance.json",
}


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_committed_release_integrity_evidence_matches_clean_regeneration(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "integrity"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_release_integrity_evidence.py"),
            "--repository-root",
            str(ROOT),
            "--output-directory",
            str(generated),
            "--verifier-source-commit",
            "8161b23b2e883278f25f3539ee3e392b8eb04033",
        ],
        check=True,
        cwd=ROOT,
    )

    assert {path.name for path in COMMITTED.glob("*.json")} == FILES
    assert {path.name for path in generated.glob("*.json")} == FILES
    for filename in sorted(FILES):
        assert (COMMITTED / filename).read_bytes() == (generated / filename).read_bytes()


def test_provenance_binds_every_integrity_file_and_preserves_authority() -> None:
    provenance = json.loads((COMMITTED / "provenance.json").read_text(encoding="utf-8"))

    assert provenance["execution_context"] == "TEST"
    assert provenance["verifier_source_commit_sha"] == (
        "8161b23b2e883278f25f3539ee3e392b8eb04033"
    )
    assert provenance["candidate_source_commit_sha"] == (
        "cb84fbc8eef6096e8a707e1b922dfa2eddb23e51"
    )
    assert provenance["production_credentials_used"] is False
    assert provenance["human_release_decision_issued"] is False
    assert provenance["external_effect"] is False

    expected = FILES - {"provenance.json"}
    assert set(provenance["evidence_file_hashes"]) == expected
    for filename in expected:
        assert provenance["evidence_file_hashes"][filename] == _sha256(
            COMMITTED / filename
        )
