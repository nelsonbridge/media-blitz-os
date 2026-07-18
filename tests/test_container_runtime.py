"""Tests for the container runtime HTTP server (GCP-02)."""

from __future__ import annotations

import json
import os
import socket
import threading
import time
import urllib.request
from unittest import mock

import pytest

from nks import __version__
from nks.application.container_runtime import _build_metadata, serve


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _free_port() -> int:
    """Return an available local TCP port."""
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _start_server(port: int) -> threading.Thread:
    """Start serve() in a daemon thread and wait until it is accepting."""
    thread = threading.Thread(target=serve, args=(port,), daemon=True)
    thread.start()
    # Wait up to 3 s for the port to open.
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.05)
    return thread


def _get(port: int, path: str) -> tuple[int, dict]:
    url = f"http://127.0.0.1:{port}{path}"
    with urllib.request.urlopen(url, timeout=3) as resp:
        return resp.status, json.loads(resp.read())


def _get_status(port: int, path: str) -> int:
    """Return only the HTTP status code, handling 4xx without raising."""
    url = f"http://127.0.0.1:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


# ---------------------------------------------------------------------------
# Unit tests — _build_metadata()
# ---------------------------------------------------------------------------


def test_build_metadata_contains_required_keys():
    meta = _build_metadata()
    for key in ("service", "version", "git_commit", "release_id", "environment", "build_timestamp"):
        assert key in meta, f"missing key: {key}"


def test_build_metadata_service_and_version():
    meta = _build_metadata()
    assert meta["service"] == "nks"
    assert meta["version"] == __version__


def test_build_metadata_reads_env_vars():
    env = {
        "NKS_GIT_COMMIT": "abc123",
        "NKS_RELEASE_ID": "enki-0.1.0-rc1",
        "NKS_ENVIRONMENT": "TEST",
        "NKS_BUILD_TIMESTAMP": "2026-01-01T00:00:00Z",
    }
    with mock.patch.dict(os.environ, env, clear=False):
        meta = _build_metadata()

    assert meta["git_commit"] == "abc123"
    assert meta["release_id"] == "enki-0.1.0-rc1"
    assert meta["environment"] == "TEST"
    assert meta["build_timestamp"] == "2026-01-01T00:00:00Z"


def test_build_metadata_defaults_to_empty_strings():
    stripped = {k: "" for k in ("NKS_GIT_COMMIT", "NKS_RELEASE_ID", "NKS_ENVIRONMENT", "NKS_BUILD_TIMESTAMP")}
    with mock.patch.dict(os.environ, stripped, clear=False):
        meta = _build_metadata()

    assert meta["git_commit"] == ""
    assert meta["release_id"] == ""
    assert meta["environment"] == ""
    assert meta["build_timestamp"] == ""


# ---------------------------------------------------------------------------
# Integration tests — live HTTP server
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def running_server():
    """Start one server instance shared across tests in this module."""
    port = _free_port()
    env = {
        "NKS_GIT_COMMIT": "deadbeef",
        "NKS_RELEASE_ID": "enki-0.1.0-rc1",
        "NKS_ENVIRONMENT": "TEST",
        "NKS_BUILD_TIMESTAMP": "2026-07-18T00:00:00Z",
    }
    with mock.patch.dict(os.environ, env, clear=False):
        _start_server(port)
    return port


def test_healthz_returns_200(running_server):
    status, body = _get(running_server, "/healthz")
    assert status == 200


def test_healthz_body_contains_status_ok(running_server):
    _, body = _get(running_server, "/healthz")
    assert body.get("status") == "ok"


def test_healthz_body_contains_service(running_server):
    _, body = _get(running_server, "/healthz")
    assert body.get("service") == "nks"


def test_healthz_body_contains_version(running_server):
    _, body = _get(running_server, "/healthz")
    assert body.get("version") == __version__


def test_health_alias_returns_200(running_server):
    status, _ = _get(running_server, "/health")
    assert status == 200


def test_version_returns_200(running_server):
    status, body = _get(running_server, "/version")
    assert status == 200


def test_version_body_contains_all_identity_fields(running_server):
    _, body = _get(running_server, "/version")
    for field in ("service", "version", "git_commit", "release_id", "environment", "build_timestamp"):
        assert field in body, f"missing field: {field}"


def test_readyz_alias_returns_200(running_server):
    status, _ = _get(running_server, "/readyz")
    assert status == 200


def test_unknown_path_returns_404(running_server):
    status = _get_status(running_server, "/unknown")
    assert status == 404


def test_query_string_is_ignored(running_server):
    status, body = _get(running_server, "/healthz?verbose=1")
    assert status == 200
    assert body.get("status") == "ok"


def test_healthz_content_type_is_json(running_server):
    url = f"http://127.0.0.1:{running_server}/healthz"
    with urllib.request.urlopen(url, timeout=3) as resp:
        assert "application/json" in resp.headers.get("Content-Type", "")
