"""Command-line entry point for the portable NKS runtime."""

from __future__ import annotations

from pathlib import Path

import typer

from nks import __version__
from nks.adapters.filesystem import JsonEventRepository
from nks.application.delivery import IngestFeedback, PreparePublication
from nks.application.export_import import (
    export_portable_state,
    import_portable_state,
    verify_imported_state,
)
<<<<<<< HEAD
from nks.adapters.manual_delivery import JsonFeedbackRepository, ManualPublicationAdapter
from nks.application.feedback import FeedbackReplayHarness
from nks.application.load_records import load_record
from nks.application.runtime import build_runtime_status
from nks.domain.delivery import FeedbackRecord, FeedbackScenario, PublicationPayload
from nks.domain.models import GateStatus, PublicationRecord, VisualPackageRecord
from nks.views.health import render_corpus_health_dashboard
=======
from nks.audit.repository import audit_repository
>>>>>>> 873c3dd6c7b73cdb77c53c36108072d137a1dd39
from nks.views.markdown import write_generated_views
from nks.audit.repository import audit_repository

app = typer.Typer(help="Nelson Knowledge System runtime")


@app.command()
def version() -> None:
    """Print the runtime version."""
    typer.echo(__version__)


@app.command("inspect-store")
def inspect_store(root: Path = typer.Argument(..., exists=True, file_okay=False)) -> None:
    """Report record counts in a filesystem adapter store."""
    collections = (
        "sources",
        "artifacts",
        "proofs",
        "narratives",
        "visuals",
        "publications",
    )
    for collection in collections:
        directory = root / collection
        count = len(list(directory.glob("*.json"))) if directory.exists() else 0
        typer.echo(f"{collection}: {count}")


@app.command("generate-views")
def generate_views(
    repository_root: Path = typer.Argument(..., exists=True, file_okay=False)
) -> None:
    """Generate deterministic Markdown views from canonical JSON records."""
    for path in write_generated_views(repository_root):
        typer.echo(str(path))


<<<<<<< HEAD
@app.command("health-dashboard")
def health_dashboard(
    repository_root: Path = typer.Argument(..., exists=True, file_okay=False)
) -> None:
    """Print a corpus health dashboard generated from current canonical state."""
    typer.echo(render_corpus_health_dashboard(repository_root / "records"))


@app.command("runtime-status")
def runtime_status(
    repository_root: Path = typer.Argument(..., exists=True, file_okay=False)
) -> None:
    """Print a live runtime status summary from canonical state and workflow events."""
    status = build_runtime_status(repository_root)
    typer.echo(status.summary())


@app.command("ingest-feedback")
def ingest_feedback(
    repository_root: Path = typer.Argument(..., exists=True, file_okay=False),
    feedback_path: Path = typer.Argument(..., exists=True, dir_okay=False),
) -> None:
    """Ingest a feedback record from JSON into the NKS feedback repository."""
    feedback = FeedbackRecord.model_validate_json(
        feedback_path.read_text(encoding="utf-8")
    )
    repository = JsonFeedbackRepository(repository_root)
    events = JsonEventRepository(repository_root)
    service = IngestFeedback(repository, events)
    saved = service.execute(feedback)
    typer.echo(saved.feedback_id)


@app.command("replay-feedback")
def replay_feedback(
    repository_root: Path = typer.Argument(..., exists=True, file_okay=False),
    scenario_path: Path = typer.Argument(..., exists=True, dir_okay=False),
) -> None:
    """Replay a synthetic feedback scenario from JSON into the feedback repository."""
    scenario = FeedbackScenario.model_validate_json(
        scenario_path.read_text(encoding="utf-8")
    )
    repository = JsonFeedbackRepository(repository_root)
    events = JsonEventRepository(repository_root)
    harness = FeedbackReplayHarness(repository, events)
    played = harness.replay([scenario])
    typer.echo(played[0].feedback_id)


@app.command("prepare-publication")
def prepare_publication(
    repository_root: Path = typer.Argument(..., exists=True, file_okay=False),
    publication_id: str = typer.Argument(...),
    platform: str = typer.Option("medium", help="Target publication platform."),
) -> None:
    """Prepare a neutral publication package from a publication record."""
    publication = load_record(
        repository_root / "records",
        "publications",
        publication_id,
        PublicationRecord,
    )

    if publication.user_approval != GateStatus.APPROVED:
        raise typer.BadParameter(
            "publication requires explicit user approval before packaging"
        )

    draft_path = repository_root / publication.draft_path
    body = draft_path.read_text(encoding="utf-8") if draft_path.exists() else ""

    asset_ids: list[str] = []
    try:
        visual = load_record(
            repository_root / "records",
            "visuals",
            publication.visual_package_id,
            VisualPackageRecord,
        )
        asset_ids = visual.asset_ids
    except FileNotFoundError:
        asset_ids = []

    payload = PublicationPayload(
        publication_id=publication.id,
        platform=platform,
        title=publication.title,
        body=body,
        asset_ids=asset_ids,
        metadata={
            "draft_path": publication.draft_path,
            "publication_record": publication.id,
        },
    )

    adapter = ManualPublicationAdapter(repository_root)
    events = JsonEventRepository(repository_root)
    service = PreparePublication(adapter, events)
    receipt = service.execute(publication, payload)

    typer.echo(f"receipt_id: {receipt.receipt_id}")
    typer.echo(f"package_path: {receipt.metadata.get('package_path')}")


@app.command("audit-repository")
def audit_repository_command(
    repository_root: Path = typer.Argument(..., exists=True, file_okay=False),
    output_dir: Path | None = typer.Option(
        None,
        help="Output directory. Defaults to generated/audit under the repository root.",
    ),
) -> None:
    """Generate deterministic census, integrity, drift, and readiness reports."""
    result = audit_repository(repository_root, output_dir)
    typer.echo(f"report: {result.report_path}")
    typer.echo(f"json: {result.json_path}")
    typer.echo(f"files: {result.file_count}")
    typer.echo(f"findings: {result.issue_count}")


@app.command("export-state")
def export_state(
    repository_root: Path = typer.Argument(..., exists=True, file_okay=False),
    archive_path: Path = typer.Argument(...),
) -> None:
    """Export canonical state, schemas, and contracts to a portable bundle."""
    result = export_portable_state(repository_root, archive_path)
    typer.echo(f"archive: {result.archive_path}")
    typer.echo(f"files: {result.file_count}")
    typer.echo(f"manifest_sha256: {result.manifest_sha256}")


@app.command("import-state")
def import_state(
    archive_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    destination_root: Path = typer.Argument(...),
    replace: bool = typer.Option(False, help="Replace a non-empty destination."),
) -> None:
    """Import and verify a portable NKS state bundle."""
    manifest = import_portable_state(
        archive_path,
        destination_root,
        replace=replace,
    )
    verify_imported_state(destination_root, manifest)
    typer.echo(f"imported_files: {len(manifest.get('files', []))}")
    typer.echo("verification: passed")


@app.command("test")
def test_runtime() -> None:
    """Explain the canonical command for the deterministic functional test."""
    typer.echo("Run: python -m pytest")


if __name__ == "__main__":
    app()
