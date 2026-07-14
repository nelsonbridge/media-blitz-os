#!/usr/bin/env python3
"""Generate deterministic release-integrity evidence for governed promotion."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from nks.application.governed_transactions import canonical_sha256
from nks.application.release_integrity import verify_release_integrity


def _write_json(path: Path, payload: object) -> str:
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path.write_text(rendered, encoding="utf-8")
    return "sha256:" + hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--release-directory",
        type=Path,
        default=Path("releases/enki-0.1.0-rc1"),
    )
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--verifier-source-commit", required=True)
    args = parser.parse_args()

    root = args.repository_root.resolve()
    release = args.release_directory
    if not release.is_absolute():
        release = root / release
    output = args.output_directory
    if not output.is_absolute():
        output = root / output
    output.mkdir(parents=True, exist_ok=True)

    result = verify_release_integrity(
        root,
        release,
        expected_source_commit="cb84fbc8eef6096e8a707e1b922dfa2eddb23e51",
    )
    if not result.valid or result.inventory is None or result.sbom is None or result.attestation is None:
        print(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True))
        return 1

    dependency_payload = {
        "schema_version": "1.0",
        "project_name": result.inventory.project_name,
        "project_version": result.inventory.project_version,
        "python_requirement": result.inventory.python_requirement,
        "dependency_sha256": result.inventory.dependency_sha256,
        "dependencies": [item.model_dump(mode="json") for item in result.inventory.dependencies],
    }
    workflow_payload = {
        "schema_version": "1.0",
        "workflow_sha256": result.inventory.workflow_sha256,
        "workflow_actions": [item.model_dump(mode="json") for item in result.inventory.workflow_actions],
    }

    file_hashes = {
        "dependency-inventory.json": _write_json(
            output / "dependency-inventory.json", dependency_payload
        ),
        "workflow-inventory.json": _write_json(
            output / "workflow-inventory.json", workflow_payload
        ),
        "sbom.json": _write_json(output / "sbom.json", result.sbom),
        "supply-chain-attestation.json": _write_json(
            output / "supply-chain-attestation.json",
            result.attestation.model_dump(mode="json"),
        ),
        "verification-result.json": _write_json(
            output / "verification-result.json",
            result.model_dump(mode="json"),
        ),
    }
    provenance = {
        "schema_version": "1.0",
        "execution_context": "TEST",
        "verifier_source_commit_sha": args.verifier_source_commit,
        "candidate_source_commit_sha": result.candidate.manifest.source_commit_sha,
        "candidate_sha256": result.candidate.candidate_sha256,
        "inventory_sha256": result.inventory.inventory_sha256,
        "dependency_sha256": result.inventory.dependency_sha256,
        "workflow_sha256": result.inventory.workflow_sha256,
        "sbom_sha256": canonical_sha256(result.sbom),
        "attestation_sha256": result.attestation.attestation_sha256,
        "evidence_file_hashes": dict(sorted(file_hashes.items())),
        "production_credentials_used": False,
        "human_release_decision_issued": False,
        "external_effect": False,
    }
    _write_json(output / "provenance.json", provenance)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
