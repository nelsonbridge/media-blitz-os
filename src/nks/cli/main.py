"""Command-line entry point for the portable NKS runtime."""

from __future__ import annotations

from pathlib import Path

import typer

from nks import __version__
from nks.application.export_import import (
    export_portable_state,
    import_portable_state,
    verify_imported_state,
)
from nks.audit.repository import audit_repository
from nks.views.markdown import write_generated_views

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
