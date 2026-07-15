"""Composite Typer application for core and stable consumer commands."""

from nks.cli.consumer import app as consumer_app
from nks.cli.main import app

app.add_typer(consumer_app, name="consumer")
