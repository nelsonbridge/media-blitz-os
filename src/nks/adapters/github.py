"""GitHub storage adapters isolated behind a minimal client contract."""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar

from nks.domain.models import CanonicalRecord, SourceRecord, WorkflowEvent
from nks.ports.canonicalization import DirectCanonicalSourceWriteError

RecordT = TypeVar("RecordT", bound=CanonicalRecord)


class GitHubContentClient(Protocol):
    """Minimal platform client required by the adapters.

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
        if isinstance(record, SourceRecord):
            raise DirectCanonicalSourceWriteError(
                "canonical sources must be created through CanonicalSourceWriter"
            )
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


class GitHubEventRepository:
    """Append-only event repository using one immutable JSON file per event.

    Per-event files avoid shared append conflicts and make duplicate event IDs
    naturally idempotent. An existing event ID with different content is an
    integrity conflict rather than an update.
    """

    def __init__(self, client: GitHubContentClient) -> None:
        self._client = client
        self._prefix = "records/events/"

    def _path(self, event_id: str) -> str:
        safe_id = event_id.replace("/", "_").replace(":", "_")
        return f"{self._prefix}{safe_id}.json"

    def append(self, event: WorkflowEvent) -> None:
        path = self._path(event.event_id)
        serialized = event.model_dump_json(indent=2)
        existing = self._client.read_text(path)
        if existing == serialized:
            return
        if existing is not None:
            raise ValueError(f"event integrity conflict: {event.event_id}")
        self._client.write_text(
            path,
            serialized,
            f"Append workflow event {event.event_id}",
        )

    def list(self) -> list[WorkflowEvent]:
        events: list[WorkflowEvent] = []
        for path in sorted(self._client.list_paths(self._prefix)):
            if not path.endswith(".json"):
                continue
            content = self._client.read_text(path)
            if content is not None:
                events.append(WorkflowEvent.model_validate_json(content))
        return events
