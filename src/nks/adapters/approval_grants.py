"""Durable, compare-and-swap filesystem repository for approval grants."""

from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from nks.governance.approvals import ApprovalGrant


class ApprovalGrantConflictError(RuntimeError):
    """Raised when immutable approval identity or lifecycle state conflicts."""


class JsonApprovalGrantRepository:
    """Persist approval grants with local-filesystem atomic replacement.

    A per-grant exclusive lock protects compare-and-swap across local processes.
    Lock contention fails immediately; callers may retry the complete governed
    operation after rereading current state. The adapter does not weaken TEST
    and PRODUCTION isolation because execution context remains inside the grant.
    """

    def __init__(self, repository_root: Path) -> None:
        self._directory = repository_root / "records" / "approval-grants"
        self._directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_identifier(approval_id: str) -> str:
        return approval_id.replace("/", "_").replace("\\", "_")

    def _path(self, approval_id: str) -> Path:
        return self._directory / f"{self._safe_identifier(approval_id)}.json"

    def _lock_path(self, approval_id: str) -> Path:
        return self._directory / f".{self._safe_identifier(approval_id)}.lock"

    @staticmethod
    def _serialize(grant: ApprovalGrant) -> str:
        payload = grant.model_dump(mode="json", exclude_none=False)
        payload["permitted_actions"] = sorted(payload["permitted_actions"])
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"

    @staticmethod
    def _read(path: Path) -> ApprovalGrant:
        return ApprovalGrant.model_validate_json(path.read_text(encoding="utf-8"))

    def get_approval(self, approval_id: str) -> ApprovalGrant | None:
        path = self._path(approval_id)
        if not path.exists():
            return None
        return self._read(path)

    def save_new(self, grant: ApprovalGrant) -> ApprovalGrant:
        """Create an approval once; identical retries are idempotent."""

        path = self._path(grant.approval_id)
        serialized = self._serialize(grant)
        try:
            with path.open("x", encoding="utf-8") as handle:
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError:
            current = self._read(path)
            if current == grant:
                return current
            raise ApprovalGrantConflictError(
                f"approval id already exists with different content: {grant.approval_id}"
            )
        return grant

    def compare_and_swap_approval(
        self,
        expected: ApprovalGrant,
        replacement: ApprovalGrant,
    ) -> bool:
        """Atomically replace one exact observed grant state."""

        if expected.approval_id != replacement.approval_id:
            raise ValueError("compare-and-swap cannot change approval_id")

        lock_path = self._lock_path(expected.approval_id)
        try:
            lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            return False

        path = self._path(expected.approval_id)
        temp_path = self._directory / (
            f".{self._safe_identifier(expected.approval_id)}.{uuid4().hex}.tmp"
        )
        try:
            os.close(lock_fd)
            if not path.exists():
                return False
            current = self._read(path)
            if current != expected:
                return False

            with temp_path.open("x", encoding="utf-8") as handle:
                handle.write(self._serialize(replacement))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
            return True
        finally:
            if temp_path.exists():
                temp_path.unlink()
            if lock_path.exists():
                lock_path.unlink()

    def list_approvals(self) -> list[ApprovalGrant]:
        return [
            self._read(path)
            for path in sorted(self._directory.glob("*.json"))
        ]
