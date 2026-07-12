from pathlib import Path

import pytest

from nks.adapters.filesystem import JsonRecordRepository
from nks.adapters.github import GitHubRecordRepository
from nks.domain.models import ArtifactRecord, SourceRecord
from nks.ports.canonicalization import DirectCanonicalSourceWriteError


class MemoryGitHubClient:
    def __init__(self) -> None:
        self.files: dict[str, str] = {}

    def read_text(self, path: str) -> str | None:
        return self.files.get(path)

    def write_text(self, path: str, content: str, message: str) -> None:
        self.files[path] = content

    def list_paths(self, prefix: str) -> list[str]:
        return [path for path in self.files if path.startswith(prefix)]


def source() -> SourceRecord:
    return SourceRecord(
        id="NKS-SRC-000004",
        title="Bypass attempt",
        source_type="external-feedback",
        source_location="feedback.json",
    )


def artifact() -> ArtifactRecord:
    return ArtifactRecord(
        id="NKS-ART-TEST",
        title="Allowed artifact",
        source_ids=["NKS-SRC-000001"],
    )


def test_generic_filesystem_repository_rejects_source_writes(tmp_path: Path):
    repository = JsonRecordRepository(tmp_path, SourceRecord, "sources")
    with pytest.raises(DirectCanonicalSourceWriteError):
        repository.save(source())


def test_generic_github_repository_rejects_source_writes():
    repository = GitHubRecordRepository(
        MemoryGitHubClient(), SourceRecord, "sources"
    )
    with pytest.raises(DirectCanonicalSourceWriteError):
        repository.save(source())


def test_generic_repositories_continue_to_persist_non_source_records(tmp_path: Path):
    filesystem_repository = JsonRecordRepository(
        tmp_path, ArtifactRecord, "artifacts"
    )
    assert filesystem_repository.save(artifact()) == artifact()

    client = MemoryGitHubClient()
    github_repository = GitHubRecordRepository(client, ArtifactRecord, "artifacts")
    assert github_repository.save(artifact()) == artifact()
    assert client.files
