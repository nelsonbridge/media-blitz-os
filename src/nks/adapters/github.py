"""GitHub storage adapter isolated behind a minimal client contract."""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar

from nks.domain.models import CanonicalRecord

RecordT = TypeVar("RecordT", bound=CanonicalRecord)


class GitHubContentClient(Protocol):
    """Minimal platform client required by the adapter.

    Concrete REST, SDK, connector, or test implementations may satisfy this
    contract without leaking into the domain or application layers.
    """

    def read_text(self, path: str) -> str | None: ...

    def write_text(self, path: str, content: str, message: str) -> None: ...

    def list_paths(self, prefix: str) -> list[str]: ...


class GitHubRecordRepository(Generic[RecordT]):
    def __init__(
        self,
        client: GitHubContentClient,
        record_type: type[RecordT],
        collection: str,
    ) -> None:
        self._client = client
        self._record_type = record_type
        self._collection = collection.strip("/")

    def _path(self, record_id: str) -> str:
        safe_id = record_id.replace("/", "_")
        return f"records/{self._collection}/{safe_id}.json"

    def get(self, record_id: str) -> RecordT | None:
        content = self._client.read_text(self._path(record_id))
        if content is None:
            return None
        return self._record_type.model_validate_json(content)

    def save(self, record: RecordT) -> RecordT:
        path = self._path(record.id)
        serialized = record.model_dump_json(indent=2)
        if self._client.read_text(path) == serialized:
            return record
        self._client.write_text(
            path,
            serialized,
            f"Persist canonical {self._collection} record {record.id}",
        )
        return record

    def list(self) -> list[RecordT]:
        records: list[RecordT] = []
        prefix = f"records/{self._collection}/"
        for path in sorted(self._client.list_paths(prefix)):
            if not path.endswith(".json"):
                continue
            content = self._client.read_text(path)
            if content is not None:
                records.append(self._record_type.model_validate_json(content))
        return records
