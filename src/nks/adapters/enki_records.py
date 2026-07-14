"""Append-only filesystem persistence for Enki findings and disclosure receipts.

The adapter supplies Class 1-compatible record mechanics without creating any
records during import or construction. Production use still requires the
applicable governed operation, journaling, and recovery boundary.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from nks.enki.contracts import ReconciliationFinding
from nks.enki.disclosure import DisclosureReceipt

RecordT = TypeVar("RecordT", bound=BaseModel)


class RecordConflictError(RuntimeError):
    """Raised when an existing immutable identifier has different content."""


class JsonEnkiRecordRepository:
    """Persist immutable findings and disclosure receipts under ``records/``."""

    def __init__(self, repository_root: Path) -> None:
        self._root = repository_root

    def _collection(self, name: str) -> Path:
        directory = self._root / "records" / name
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @staticmethod
    def _safe_identifier(record_id: str) -> str:
        return record_id.replace("/", "_").replace("\\", "_")

    def _path(self, collection: str, record_id: str) -> Path:
        return self._collection(collection) / f"{self._safe_identifier(record_id)}.json"

    @staticmethod
    def _serialized(record: BaseModel) -> str:
        return record.model_dump_json(indent=2, exclude_none=False) + "\n"

    def _append(self, collection: str, record_id: str, record: BaseModel) -> None:
        path = self._path(collection, record_id)
        serialized = self._serialized(record)
        if path.exists():
            existing = path.read_text(encoding="utf-8")
            if existing == serialized:
                return
            raise RecordConflictError(
                f"immutable record id already exists with different content: {record_id}"
            )
        path.write_text(serialized, encoding="utf-8")

    @staticmethod
    def _read(path: Path, record_type: type[RecordT]) -> RecordT:
        return record_type.model_validate_json(path.read_text(encoding="utf-8"))

    def append_findings(self, findings: Iterable[ReconciliationFinding]) -> None:
        for finding in findings:
            self._append("reconciliation-findings", finding.finding_id, finding)

    def get_finding(self, finding_id: str) -> ReconciliationFinding | None:
        path = self._path("reconciliation-findings", finding_id)
        if not path.exists():
            return None
        return self._read(path, ReconciliationFinding)

    def list_findings(self) -> list[ReconciliationFinding]:
        directory = self._collection("reconciliation-findings")
        return [
            self._read(path, ReconciliationFinding)
            for path in sorted(directory.glob("*.json"))
        ]

    def append_disclosure_receipt(self, receipt: DisclosureReceipt) -> None:
        self._append("disclosure-receipts", receipt.disclosure_id, receipt)

    def get_disclosure_receipt(self, disclosure_id: str) -> DisclosureReceipt | None:
        path = self._path("disclosure-receipts", disclosure_id)
        if not path.exists():
            return None
        return self._read(path, DisclosureReceipt)

    def list_disclosure_receipts(self) -> list[DisclosureReceipt]:
        directory = self._collection("disclosure-receipts")
        return [
            self._read(path, DisclosureReceipt)
            for path in sorted(directory.glob("*.json"))
        ]
