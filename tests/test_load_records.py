from pathlib import Path

import pytest

from nks.application.load_records import canonical_record_path, load_record
from nks.domain.models import PublicationRecord


def test_canonical_record_path_prefers_root_collection(tmp_path: Path):
    root = tmp_path / "records"
    (root / "publications").mkdir(parents=True)
    (root / "canonical" / "publications").mkdir(parents=True)

    root_file = root / "publications" / "NKS-PUB-000001.json"
    root_file.write_text('{"id": "NKS-PUB-000001"}', encoding="utf-8")
    canonical_file = root / "canonical" / "publications" / "NKS-PUB-000001.json"
    canonical_file.write_text('{"id": "NKS-PUB-000001"}', encoding="utf-8")

    assert canonical_record_path(root, "publications", "NKS-PUB-000001") == root_file


def test_canonical_record_path_falls_back_to_canonical(tmp_path: Path):
    root = tmp_path / "records"
    (root / "canonical" / "publications").mkdir(parents=True)
    canonical_file = root / "canonical" / "publications" / "NKS-PUB-000001.json"
    canonical_file.write_text('{"id": "NKS-PUB-000001"}', encoding="utf-8")

    assert canonical_record_path(root, "publications", "NKS-PUB-000001") == canonical_file


def test_load_record_falls_back_to_canonical_directory(tmp_path: Path):
    root = tmp_path / "records"
    (root / "canonical" / "publications").mkdir(parents=True)
    canonical_file = root / "canonical" / "publications" / "NKS-PUB-000001.json"
    canonical_file.write_text(
        '{"id": "NKS-PUB-000001", "artifact_id": "NKS-ART-000001", "title": "Test", "proof_id": "NKS-PRF-000001", "narrative_id": "NKS-NAR-000001", "visual_package_id": "NKS-VIS-000001", "draft_path": "publishing/drafts/NKS-PUB-000001.md"}',
        encoding="utf-8",
    )

    publication = load_record(root, "publications", "NKS-PUB-000001", PublicationRecord)

    assert publication.id == "NKS-PUB-000001"
    assert publication.artifact_id == "NKS-ART-000001"
