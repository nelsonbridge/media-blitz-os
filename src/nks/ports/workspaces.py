"""Platform-neutral contracts for human workspaces and synchronization."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class SyncStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    SYNCED = "synced"
    VERIFIED = "verified"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class DocumentView:
    view_id: str
    title: str
    content: str
    mime_type: str = "text/markdown"
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TableView:
    view_id: str
    title: str
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SyncRequest:
    request_id: str
    source_id: str
    target_surface: str
    target_location: str
    status: SyncStatus = SyncStatus.PENDING
    metadata: dict[str, str] = field(default_factory=dict)


class DocumentWorkspace(Protocol):
    def upsert_document(self, document: DocumentView, target_location: str) -> str: ...

    def read_document(self, target_location: str) -> DocumentView | None: ...


class TabularWorkspace(Protocol):
    def upsert_table(self, table: TableView, target_location: str) -> str: ...

    def read_table(self, target_location: str) -> TableView | None: ...


class SyncQueue(Protocol):
    def enqueue(self, request: SyncRequest) -> SyncRequest: ...

    def get(self, request_id: str) -> SyncRequest | None: ...

    def list(self) -> list[SyncRequest]: ...


class WorkspaceReconciler(Protocol):
    def reconcile_document(
        self,
        canonical: DocumentView,
        remote: DocumentView | None,
    ) -> DocumentView: ...

    def reconcile_table(
        self,
        canonical: TableView,
        remote: TableView | None,
    ) -> TableView: ...
