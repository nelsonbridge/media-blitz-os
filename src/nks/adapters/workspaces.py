"""Neutral workspace adapters used for local execution and contract testing."""

from __future__ import annotations

from dataclasses import replace

from nks.ports.workspaces import (
    DocumentView,
    SyncRequest,
    SyncStatus,
    TableView,
)


class InMemoryDocumentWorkspace:
    def __init__(self) -> None:
        self._documents: dict[str, DocumentView] = {}

    def upsert_document(self, document: DocumentView, target_location: str) -> str:
        self._documents[target_location] = document
        return target_location

    def read_document(self, target_location: str) -> DocumentView | None:
        return self._documents.get(target_location)


class InMemoryTabularWorkspace:
    def __init__(self) -> None:
        self._tables: dict[str, TableView] = {}

    def upsert_table(self, table: TableView, target_location: str) -> str:
        self._tables[target_location] = table
        return target_location

    def read_table(self, target_location: str) -> TableView | None:
        return self._tables.get(target_location)


class InMemorySyncQueue:
    def __init__(self) -> None:
        self._requests: dict[str, SyncRequest] = {}

    def enqueue(self, request: SyncRequest) -> SyncRequest:
        existing = self._requests.get(request.request_id)
        if existing is not None:
            return existing
        queued = replace(request, status=SyncStatus.QUEUED)
        self._requests[queued.request_id] = queued
        return queued

    def get(self, request_id: str) -> SyncRequest | None:
        return self._requests.get(request_id)

    def list(self) -> list[SyncRequest]:
        return [self._requests[key] for key in sorted(self._requests)]


class CanonicalWinsReconciler:
    """Default policy: canonical state wins over human workspace drift.

    Remote edits are never silently promoted to canonical state. They must enter
    a separate review workflow before becoming authoritative.
    """

    def reconcile_document(
        self,
        canonical: DocumentView,
        remote: DocumentView | None,
    ) -> DocumentView:
        return canonical

    def reconcile_table(
        self,
        canonical: TableView,
        remote: TableView | None,
    ) -> TableView:
        return canonical
