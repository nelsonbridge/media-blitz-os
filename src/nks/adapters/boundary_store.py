"""Zero-cost local stores used to prove Enki boundary isolation semantics."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

from nks.application.boundary_isolation import BoundaryConflict, BoundaryRecord
from nks.governance.boundaries import BoundaryContext


class _JsonBoundaryStore:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _record_token(record_id: str) -> str:
        return hashlib.sha256(record_id.encode("utf-8")).hexdigest()

    def _path(self, boundary: BoundaryContext, record_id: str) -> Path:
        raise NotImplementedError

    def put(self, record: BoundaryRecord) -> BoundaryRecord:
        path = self._path(record.boundary, record.record_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            existing = BoundaryRecord.model_validate_json(path.read_text(encoding="utf-8"))
            if existing != record:
                raise BoundaryConflict("immutable boundary record conflict")
            return existing

        payload = record.model_dump_json(indent=2)
        fd, temporary = tempfile.mkstemp(prefix=".boundary-", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return record

    def get(self, boundary: BoundaryContext, record_id: str) -> BoundaryRecord | None:
        path = self._path(boundary, record_id)
        if not path.exists():
            return None
        record = BoundaryRecord.model_validate_json(path.read_text(encoding="utf-8"))
        if record.boundary != boundary:
            return None
        return record

    def count(self, boundary: BoundaryContext) -> int:
        directory = self._path(boundary, "count-placeholder").parent
        return len(list(directory.glob("*.json"))) if directory.exists() else 0


class SharedLogicalBoundaryStore(_JsonBoundaryStore):
    """One physical store with content-addressed logical boundary partitions."""

    def _path(self, boundary: BoundaryContext, record_id: str) -> Path:
        token = boundary.boundary_sha256.removeprefix("sha256:")
        return self._root / "shared" / token / f"{self._record_token(record_id)}.json"


class SeparatedLocalBoundaryStore(_JsonBoundaryStore):
    """Separate local directory for each namespace and tenant pair."""

    @staticmethod
    def _tenant_token(boundary: BoundaryContext) -> str:
        raw = f"{boundary.namespace_id}|{boundary.tenant_id}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _path(self, boundary: BoundaryContext, record_id: str) -> Path:
        return (
            self._root
            / "tenants"
            / self._tenant_token(boundary)
            / boundary.boundary_sha256.removeprefix("sha256:")
            / f"{self._record_token(record_id)}.json"
        )
