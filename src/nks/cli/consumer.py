"""Versioned JSON consumer CLI over the governed application gateway."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import typer

from nks.application.consumer_adapters import ConsumerCliAdapter
from nks.application.consumer_contracts import ConsumerOperation
from nks.application.consumer_service import (
    ConsumerGateway,
    DeterministicConsumerApplicationService,
)
from nks.governance.boundaries import BoundaryAuthorization


app = typer.Typer(help="Stable versioned Enki consumer contract")


@app.command("call")
def call(
    request_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    authorization_path: Path = typer.Argument(..., exists=True, dir_okay=False),
) -> None:
    """Execute one governed consumer request without repository shortcuts."""

    authorization = BoundaryAuthorization.model_validate_json(
        authorization_path.read_text(encoding="utf-8")
    )
    application_service = DeterministicConsumerApplicationService()
    gateway = ConsumerGateway(
        authorizations={authorization.authorization_id: authorization},
        services={
            ConsumerOperation.QUERY: application_service,
            ConsumerOperation.COMMAND: application_service,
        },
    )
    adapter = ConsumerCliAdapter(gateway)
    typer.echo(
        adapter.invoke_json(
            request_path.read_text(encoding="utf-8"),
            now=datetime.now(timezone.utc),
        )
    )


@app.command("fixture")
def fixture() -> None:
    """Print the deterministic v1 compatibility fixture."""

    from nks.application.consumer_contracts import compatibility_fixture

    typer.echo(json.dumps(compatibility_fixture(), indent=2, sort_keys=True))
