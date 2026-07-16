import json
import zipfile
from pathlib import Path

import pytest

from nks.application.export_import import (
    export_portable_state,
    import_portable_state,
    verify_imported_state,
)


def test_round_trip_export_import_is_checksumming_and_platform_neutral(tmp_path: Path):
    source = tmp_path / "source"
    (source / "records" / "publications").mkdir(parents=True)
    (source / "schemas").mkdir(parents=True)
    (source / "contracts").mkdir(parents=True)
    (source / "records" / "publications" / "NKS-PUB-000001.json").write_text(
        json.dumps({"id": "NKS-PUB-000001", "status": "review"}, indent=2),
        encoding="utf-8",
    )
    (source / "schemas" / "publication.json").write_text(
        json.dumps({"type": "object"}, indent=2), encoding="utf-8"
    )
    (source / "contracts" / "adapter.md").write_text(
        "# Adapter Contract\n", encoding="utf-8"
    )

    archive = tmp_path / "nks-state.zip"
    result = export_portable_state(source, archive)

    assert result.file_count == 3
    assert archive.exists()
    assert len(result.manifest_sha256) == 64

    destination = tmp_path / "destination"
    manifest = import_portable_state(archive, destination)
    verify_imported_state(destination, manifest)

    assert (
        destination / "records" / "publications" / "NKS-PUB-000001.json"
    ).exists()
    assert not any("github" in item["path"].lower() for item in manifest["files"])


def test_import_rejects_nonempty_destination_without_replace(tmp_path: Path):
    source = tmp_path / "source"
    (source / "records").mkdir(parents=True)
    (source / "records" / "record.json").write_text("{}", encoding="utf-8")
    archive = tmp_path / "state.zip"
    export_portable_state(source, archive)

    destination = tmp_path / "destination"
    destination.mkdir()
    (destination / "existing.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError):
        import_portable_state(archive, destination)


def test_import_detects_tampered_content(tmp_path: Path):
    archive = tmp_path / "tampered.zip"
    manifest = {
        "format": "nks-portable-state",
        "version": 1,
        "files": [
            {
                "path": "records/a.json",
                "sha256": "0" * 64,
                "size": 2,
            }
        ],
    }
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("manifest.json", json.dumps(manifest))
        bundle.writestr("records/a.json", "{}")

    with pytest.raises(ValueError, match="checksum mismatch"):
        import_portable_state(archive, tmp_path / "destination")


def test_export_preserves_portable_evidence_references_and_unresolved_links(tmp_path: Path):
    source = tmp_path / "source"
    (source / "records" / "publications").mkdir(parents=True)
    (source / "records" / "evidence").mkdir(parents=True)

    (source / "records" / "evidence" / "EVD-001.json").write_text(
        json.dumps({"evidence_id": "EVD-001", "kind": "proof"}, indent=2),
        encoding="utf-8",
    )

    (source / "records" / "publications" / "NKS-PUB-000001.json").write_text(
        json.dumps(
            {
                "id": "NKS-PUB-000001",
                "status": "review",
                "provenance": {
                    "source": "records/sources/NKS-SRC-000001.json",
                    "captured_by": "test-fixture",
                },
                "source_location": "records/sources/NKS-SRC-000001.json",
                "evidence_associations": [
                    {
                        "evidence_id": "EVD-001",
                        "relationship": "supports",
                        "metadata": {"strength": "high"},
                    },
                    {
                        "evidence_id": "EVD-404",
                        "relationship": "supports",
                        "metadata": {"strength": "unknown"},
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    archive = tmp_path / "state-with-evidence.zip"
    export_portable_state(source, archive)

    destination = tmp_path / "destination"
    manifest = import_portable_state(archive, destination)

    evidence = manifest["evidence"]
    references = evidence["references"]
    unresolved = evidence["unresolved"]

    resolved_ref = next(item for item in references if item["evidence_id"] == "EVD-001")
    unresolved_ref = next(item for item in references if item["evidence_id"] == "EVD-404")

    assert resolved_ref["status"] == "resolved"
    assert resolved_ref["relationship"] == "supports"
    assert resolved_ref["source_ref"] == "records/sources/NKS-SRC-000001.json"
    assert resolved_ref["integrity_sha256"] is not None
    assert resolved_ref["provenance"]["captured_by"] == "test-fixture"

    assert unresolved_ref["status"] == "unresolved"
    assert unresolved_ref["unresolved_reason"] == "missing_exported_evidence"
    assert unresolved_ref["integrity_sha256"] is None
    assert len(unresolved) == 1
    assert unresolved[0]["evidence_id"] == "EVD-404"


def test_import_rejects_invalid_evidence_manifest_shape(tmp_path: Path):
    archive = tmp_path / "bad-evidence-shape.zip"
    manifest = {
        "format": "nks-portable-state",
        "version": 1,
        "files": [],
        "evidence": {"references": "invalid", "unresolved": []},
    }
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("manifest.json", json.dumps(manifest))

    with pytest.raises(ValueError, match="invalid evidence references"):
        import_portable_state(archive, tmp_path / "destination")


def test_export_manifest_is_deterministic_for_same_input(tmp_path: Path):
    source = tmp_path / "source"
    (source / "records" / "history").mkdir(parents=True)
    (source / "schemas").mkdir(parents=True)
    (source / "records" / "history" / "transitions.json").write_text(
        json.dumps(
            {
                "sequence_contract": "ordered-only",
                "transitions": [
                    {
                        "transition_id": "tr-1",
                        "transition_index": 0,
                        "knowledge_id": "K-001",
                        "from_state_id": None,
                        "to_state_id": "S-001",
                        "authoritative": True,
                        "state_payload": {"status": "approved"},
                        "provenance": {"source": "records/sources/SRC-001.json"},
                        "evidence_associations": [],
                        "lineage": {
                            "parent_state_id": None,
                            "supersedes_state_id": None,
                            "branch_id": "main",
                        },
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (source / "schemas" / "x.json").write_text("{}", encoding="utf-8")

    archive_a = tmp_path / "a.zip"
    archive_b = tmp_path / "b.zip"

    result_a = export_portable_state(source, archive_a)
    result_b = export_portable_state(source, archive_b)

    assert result_a.manifest_sha256 == result_b.manifest_sha256

    with zipfile.ZipFile(archive_a, "r") as bundle_a, zipfile.ZipFile(archive_b, "r") as bundle_b:
        manifest_a = bundle_a.read("manifest.json")
        manifest_b = bundle_b.read("manifest.json")

    assert manifest_a == manifest_b


def test_export_sets_reconstruction_support_metadata_when_history_present(tmp_path: Path):
    source = tmp_path / "source"
    (source / "records" / "history").mkdir(parents=True)
    (source / "records" / "history" / "transitions.json").write_text(
        json.dumps(
            {
                "sequence_contract": "ordered-only",
                "transitions": [
                    {
                        "transition_id": "tr-1",
                        "transition_index": 0,
                        "knowledge_id": "K-001",
                        "from_state_id": None,
                        "to_state_id": "S-001",
                        "authoritative": True,
                        "state_payload": {"status": "approved"},
                        "provenance": {"source": "records/sources/SRC-001.json"},
                        "evidence_associations": [],
                        "lineage": {
                            "parent_state_id": None,
                            "supersedes_state_id": None,
                            "branch_id": "main",
                        },
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    archive = tmp_path / "state.zip"
    export_portable_state(source, archive)
    manifest = import_portable_state(archive, tmp_path / "destination")

    governed = manifest["governed_reconstruction"]
    assert governed["history_present"] is True
    assert governed["reconstruction_supported"] is True
    assert governed["history_path"] == "records/history/transitions.json"
    assert isinstance(governed["history_sha256"], str)
    assert len(governed["history_sha256"]) == 64


def test_import_rejects_inconsistent_governed_reconstruction_declaration(tmp_path: Path):
    archive = tmp_path / "invalid-governed.zip"
    manifest = {
        "format": "nks-portable-state",
        "version": 1,
        "files": [],
        "governed_reconstruction": {
            "history_present": False,
            "reconstruction_supported": True,
            "history_path": "records/history/transitions.json",
            "history_sha256": None,
        },
    }
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("manifest.json", json.dumps(manifest))

    with pytest.raises(ValueError, match="invalid governed reconstruction declaration"):
        import_portable_state(archive, tmp_path / "destination")


def test_import_rejects_missing_governed_history_file_when_declared(tmp_path: Path):
    archive = tmp_path / "missing-history.zip"
    manifest = {
        "format": "nks-portable-state",
        "version": 1,
        "files": [],
        "governed_reconstruction": {
            "history_present": True,
            "reconstruction_supported": True,
            "history_path": "records/history/transitions.json",
            "history_sha256": "0" * 64,
        },
    }
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("manifest.json", json.dumps(manifest))

    with pytest.raises(ValueError, match="missing governed history file"):
        import_portable_state(archive, tmp_path / "destination")
