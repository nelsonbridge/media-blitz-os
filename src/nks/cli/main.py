"""Command-line entry point for the portable NKS runtime."""

from __future__ import annotations

from pathlib import Path

import typer

from nks import __version__
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


@app.command("test")
def test_runtime() -> None:
    """Explain the canonical command for the deterministic functional test."""
    typer.echo("Run: python -m pytest")


if __name__ == "__main__":
    app()
