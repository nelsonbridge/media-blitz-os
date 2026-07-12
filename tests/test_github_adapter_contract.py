from nks.adapters.github import GitHubRecordRepository
from nks.domain.models import ArtifactRecord, RecordStatus


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
    repository = GitHubRecordRepository(client, ArtifactRecord, "artifacts")
    record = ArtifactRecord(
        id="NKS-ART-ADAPTER-0001",
        title="Adapter Contract Artifact",
        status=RecordStatus.APPROVED,
        source_ids=["NKS-SRC-ADAPTER-0001"],
    )

    repository.save(record)
    repository.save(record)

    assert repository.get(record.id) == record
    assert repository.list() == [record]
    assert len(client.writes) == 1
    assert client.writes[0][0] == "records/artifacts/NKS-ART-ADAPTER-0001.json"
