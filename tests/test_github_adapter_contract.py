from nks.adapters.github import GitHubRecordRepository
from nks.domain.models import RecordStatus, SourceRecord


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


def test_github_adapter_implements_idempotent_record_contract():
    client = FakeGitHubClient()
    repository = GitHubRecordRepository(client, SourceRecord, "sources")
    record = SourceRecord(
        id="NKS-SRC-ADAPTER-0001",
        title="Adapter Contract Source",
        status=RecordStatus.APPROVED,
        source_type="contract-test",
        source_location="fixture.md",
    )

    repository.save(record)
    repository.save(record)

    assert repository.get(record.id) == record
    assert repository.list() == [record]
    assert len(client.writes) == 1
    assert client.writes[0][0] == "records/sources/NKS-SRC-ADAPTER-0001.json"
