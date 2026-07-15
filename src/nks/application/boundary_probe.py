"""Local-process adversarial probe for Sprint 16.

This module intentionally has no network, credential, endpoint, or callback
surface. It is invoked in a separate Python process to prove that a forged
cross-tenant request fails before storage access.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from nks.adapters.boundary_store import SeparatedLocalBoundaryStore
from nks.application.boundary_isolation import BoundaryIsolationError, BoundaryIsolationService
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryAction, BoundaryAuthorization, BoundaryContext


def _boundary(tenant_id: str) -> BoundaryContext:
    return BoundaryContext(
        namespace_id="NKS-TEST",
        tenant_id=tenant_id,
        subject_id="SUBJECT-1",
        domain="operations",
        audience="internal",
        execution_context=ExecutionContext.TEST,
    )


def _worker(root: Path) -> int:
    now = datetime(2026, 7, 15, 3, 0, tzinfo=timezone.utc)
    requested = _boundary("TENANT-A")
    forged_authority = BoundaryAuthorization(
        authorization_id="AUTH-TENANT-B",
        boundary=_boundary("TENANT-B"),
        permitted_actions={BoundaryAction.READ},
        authority_class="TEST-HARNESS",
        issued_at=now,
    )
    service = BoundaryIsolationService(SeparatedLocalBoundaryStore(root))
    try:
        service.read(
            boundary=requested,
            record_id="REC-1",
            authorization=forged_authority,
            now=now,
        )
    except BoundaryIsolationError as error:
        return 0 if error.reason_code == "BOUNDARY_MISMATCH" else 3
    return 2


def run_local_process_denial_probe(root: Path) -> subprocess.CompletedProcess[str]:
    """Run the forged request in a distinct local process."""

    return subprocess.run(
        [sys.executable, "-m", "nks.application.boundary_probe", "--worker", str(root)],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=Path, required=True)
    args = parser.parse_args(argv)
    return _worker(args.worker)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
