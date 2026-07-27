"""Minimal HTTP runtime for Cloud Run deployment.

Serves /healthz (liveness) and /version (identity) endpoints using only the
Python standard library.  No application business logic runs here — this is
the sole hosted entry-point that makes the container observable to Cloud Run.

Identity metadata is injected at build time via Docker ARG → ENV so that the
running container can answer:
  * What service is this?   → service
  * What version?           → version
  * What commit built it?   → git_commit
  * What release?           → release_id
  * What environment?       → environment (TEST | PRODUCTION)
  * When was it built?      → build_timestamp

Graceful shutdown is handled via SIGTERM / SIGINT so that Cloud Run can drain
in-flight requests before terminating the revision.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any


_SERVICE_NAME = "nks"


def _build_metadata() -> dict[str, str]:
    from nks import __version__

    return {
        "service": _SERVICE_NAME,
        "version": __version__,
        "git_commit": os.environ.get("NKS_GIT_COMMIT", ""),
        "release_id": os.environ.get("NKS_RELEASE_ID", ""),
        "environment": os.environ.get("NKS_ENVIRONMENT", ""),
        "build_timestamp": os.environ.get("NKS_BUILD_TIMESTAMP", ""),
    }


class _Handler(BaseHTTPRequestHandler):
    """Stateless request handler. A new instance is created per request."""

    _metadata: dict[str, Any] = {}

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path in {"/healthz", "/health"}:
            self._respond(200, {"status": "ok", **self._metadata})
        elif path in {"/version", "/readyz"}:
            self._respond(200, self._metadata)
        else:
            self._respond(404, {"error": "not found"})

    def _respond(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[container_runtime] {fmt % args}", file=sys.stderr)


def serve(port: int) -> None:
    """Start the HTTP server and block until SIGTERM or SIGINT."""
    _Handler._metadata = _build_metadata()

    server = HTTPServer(("", port), _Handler)

    # Register SIGTERM / SIGINT only when running in the main thread.
    # In test environments the server may be started in a daemon thread where
    # signal registration is not permitted.
    if threading.current_thread() is threading.main_thread():

        def _shutdown(signum: int, _frame: object) -> None:
            print(
                f"[container_runtime] signal {signum} received, shutting down",
                file=sys.stderr,
            )
            server.shutdown()

        signal.signal(signal.SIGTERM, _shutdown)
        signal.signal(signal.SIGINT, _shutdown)

    print(f"[container_runtime] listening on :{port}", file=sys.stderr)
    server.serve_forever()


if __name__ == "__main__":
    _port = int(os.environ.get("PORT", "8080"))
    serve(_port)
