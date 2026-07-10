from nks.adapters.workspaces import (
    CanonicalWinsReconciler,
    InMemoryDocumentWorkspace,
    InMemorySyncQueue,
    InMemoryTabularWorkspace,
)
from nks.ports.workspaces import DocumentView, SyncRequest, SyncStatus, TableView


def test_document_workspace_upsert_is_idempotent():
    workspace = InMemoryDocumentWorkspace()
    document = DocumentView(view_id="DOC-1", title="Title", content="body")
    workspace.upsert_document(document, "editorial/doc-1")
    workspace.upsert_document(document, "editorial/doc-1")
    assert workspace.read_document("editorial/doc-1") == document


def test_tabular_workspace_round_trip():
    workspace = InMemoryTabularWorkspace()
    table = TableView(
        view_id="TBL-1",
        title="Table",
        columns=("id", "status"),
        rows=(("1", "ready"),),
    )
    workspace.upsert_table(table, "ops/table-1")
    assert workspace.read_table("ops/table-1") == table


def test_sync_queue_deduplicates_by_request_id():
    queue = InMemorySyncQueue()
    request = SyncRequest(
        request_id="SYNC-1",
        source_id="NKS-PUB-000001",
        target_surface="document-workspace",
        target_location="editorial/pub-1",
    )
    first = queue.enqueue(request)
    second = queue.enqueue(request)
    assert first == second
    assert first.status == SyncStatus.QUEUED
    assert len(queue.list()) == 1


def test_canonical_reconciler_never_promotes_remote_drift():
    reconciler = CanonicalWinsReconciler()
    canonical = DocumentView(view_id="DOC-1", title="Canonical", content="approved")
    remote = DocumentView(view_id="DOC-1", title="Edited", content="unreviewed")
    assert reconciler.reconcile_document(canonical, remote) == canonical
