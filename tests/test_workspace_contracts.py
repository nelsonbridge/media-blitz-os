from nks.ports.workspaces import (
    DocumentView,
    SyncRequest,
    SyncStatus,
    TableView,
)


def test_document_view_is_platform_neutral():
    view = DocumentView(
        view_id="NKS-VIEW-0001",
        title="Publication Index",
        content="# Publication Index",
        metadata={"source": "generated/publication-index.md"},
    )
    assert view.mime_type == "text/markdown"
    assert "google" not in repr(view).lower()
    assert "github" not in repr(view).lower()


def test_table_view_preserves_deterministic_shape():
    table = TableView(
        view_id="NKS-TBL-0001",
        title="Publication Readiness",
        columns=("publication_id", "status"),
        rows=(("NKS-PUB-000001", "approval-needed"),),
    )
    assert len(table.columns) == 2
    assert all(len(row) == len(table.columns) for row in table.rows)


def test_sync_request_queues_without_changing_domain_state():
    request = SyncRequest(
        request_id="NKS-SYNC-0001",
        source_id="NKS-PUB-000001",
        target_surface="document-workspace",
        target_location="editorial/publication-000001",
        status=SyncStatus.QUEUED,
    )
    assert request.status == SyncStatus.QUEUED
    assert request.source_id == "NKS-PUB-000001"
