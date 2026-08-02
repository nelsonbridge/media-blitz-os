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
        os.makedirs(self._io_path(self._root), exist_ok=True)

    @staticmethod
    def _record_token(record_id: str) -> str:
        return hashlib.sha256(record_id.encode("utf-8")).hexdigest()

    def _path(self, boundary: BoundaryContext, record_id: str) -> Path:
        raise NotImplementedError

    @staticmethod
    def _io_path(path: Path) -> str:
        """Return a Windows extended-length path without changing store layout."""
        resolved = str(path.resolve())
        if os.name == "nt":
            if resolved.startswith("\\\\?\\"):
                return resolved
            if resolved.startswith("\\\\"):
                return "\\\\?\\UNC\\" + resolved.lstrip("\\")
            return f"\\\\?\\{resolved}"
        return resolved

    def put(self, record: BoundaryRecord) -> BoundaryRecord:
        path = self._path(record.boundary, record.record_id)
        os.makedirs(self._io_path(path.parent), exist_ok=True)
        io_path = self._io_path(path)
        if os.path.exists(io_path):
            with open(io_path, encoding="utf-8") as handle:
                existing = BoundaryRecord.model_validate_json(handle.read())
            if existing != record:
                raise BoundaryConflict("immutable boundary record conflict")
            return existing

        payload = record.model_dump_json(indent=2)
        fd, temporary = tempfile.mkstemp(
            prefix=".boundary-",
            suffix=".tmp",
            dir=self._io_path(path.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, io_path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return record

    def get(self, boundary: BoundaryContext, record_id: str) -> BoundaryRecord | None:
        path = self._path(boundary, record_id)
        io_path = self._io_path(path)
        if not os.path.exists(io_path):
            return None
        with open(io_path, encoding="utf-8") as handle:
            record = BoundaryRecord.model_validate_json(handle.read())
        if record.boundary != boundary:
            return None
        return record

    def count(self, boundary: BoundaryContext) -> int:
        directory = self._path(boundary, "count-placeholder").parent
        io_directory = self._io_path(directory)
        if not os.path.isdir(io_directory):
            return 0
        with os.scandir(io_directory) as entries:
            return sum(
                entry.is_file() and entry.name.endswith(".json")
                for entry in entries
            )


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
