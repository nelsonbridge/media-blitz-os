"""Repository ports used by application workflows."""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar

from nks.domain.models import CanonicalRecord, WorkflowEvent

RecordT = TypeVar("RecordT", bound=CanonicalRecord)


class RecordRepository(Protocol, Generic[RecordT]):
    def get(self, record_id: str) -> RecordT | None: ...

    def save(self, record: RecordT) -> RecordT: ...

    def list(self) -> list[RecordT]: ...


class EventRepository(Protocol):
    def append(self, event: WorkflowEvent) -> None: ...

    def list(self) -> list[WorkflowEvent]: ...


class RepositoryRegistry(Protocol):
    def records(self, record_type: str) -> RecordRepository[CanonicalRecord]: ...

    def events(self) -> EventRepository: ...
