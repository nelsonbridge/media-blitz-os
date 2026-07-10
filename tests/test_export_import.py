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
