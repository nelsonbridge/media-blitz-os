import pytest

from nks.adapters.github import GitHubEventRepository
from nks.domain.models import WorkflowEvent


class FakeGitHubClient:
    def __init__(self):
        self.files: dict[str, str] = {}
        self.writes: list[tuple[str, str]] = []

    def read_text(self, path: str) -> str | None:
        return self.files.get(path)

    def write_text(self, path: str, content: str, message: str) -> None:
        self.files[path] = content
        self.writes.append((path, message))

    def list_paths(self, prefix: str) -> list[str]:
        return [path for path in self.files if path.startswith(prefix)]


def test_event_append_is_idempotent_and_listable():
    client = FakeGitHubClient()
    repository = GitHubEventRepository(client)
    event = WorkflowEvent(
        event_id="publication.manufactured:NKS-PUB-000001",
        event_type="publication.manufactured",
        subject_id="NKS-PUB-000001",
        payload={"artifact_id": "NKS-ART-000001"},
    )

    repository.append(event)
    repository.append(event)

    assert repository.list() == [event]
    assert len(client.writes) == 1
    assert client.writes[0][0] == (
        "records/events/publication.manufactured_NKS-PUB-000001.json"
    )


def test_existing_event_id_with_different_content_is_integrity_conflict():
    client = FakeGitHubClient()
    repository = GitHubEventRepository(client)
    original = WorkflowEvent(
        event_id="event:1",
        event_type="source.recorded",
        subject_id="NKS-SRC-000001",
        payload={"version": 1},
    )
    conflicting = WorkflowEvent(
        event_id="event:1",
        event_type="source.recorded",
        subject_id="NKS-SRC-000001",
        payload={"version": 2},
    )

    repository.append(original)

    with pytest.raises(ValueError, match="event integrity conflict"):
        repository.append(conflicting)
