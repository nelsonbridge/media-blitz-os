"""Append-only persistence for governed transaction events and receipts."""

from __future__ import annotations

import json
from pathlib import Path

from nks.application.governed_transactions import (
    GovernedTransactionEvent,
    GovernedTransactionReceipt,
)


class GovernedTransactionRecordConflictError(RuntimeError):
    """Raised when an immutable transaction record id has different content."""


class JsonGovernedTransactionRepository:
    """Durable append-only transaction journal and terminal receipt repository."""

    def __init__(self, repository_root: Path) -> None:
        self._events = repository_root / "records" / "governed-transaction-events"
        self._receipts = repository_root / "records" / "governed-transaction-receipts"
        self._events.mkdir(parents=True, exist_ok=True)
        self._receipts.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_identifier(value: str) -> str:
        return value.replace("/", "_").replace("\\", "_")

    @staticmethod
    def _serialize(record: GovernedTransactionEvent | GovernedTransactionReceipt) -> str:
        return json.dumps(
            record.model_dump(mode="json", exclude_none=False),
            indent=2,
            sort_keys=True,
        ) + "\n"

    def _append(
        self,
        directory: Path,
        record_id: str,
        record: GovernedTransactionEvent | GovernedTransactionReceipt,
    ) -> None:
        path = directory / f"{self._safe_identifier(record_id)}.json"
        content = self._serialize(record)
        if path.exists():
            if path.read_text(encoding="utf-8") == content:
                return
            raise GovernedTransactionRecordConflictError(
                f"immutable governed transaction record already exists: {record_id}"
            )
        path.write_text(content, encoding="utf-8")

    def append_event(self, event: GovernedTransactionEvent) -> None:
        self._append(self._events, event.event_id, event)

    def list_events(self, transaction_id: str) -> list[GovernedTransactionEvent]:
        events = [
            GovernedTransactionEvent.model_validate_json(
                path.read_text(encoding="utf-8")
            )
            for path in sorted(self._events.glob("*.json"))
        ]
        return [event for event in events if event.transaction_id == transaction_id]

    def append_receipt(self, receipt: GovernedTransactionReceipt) -> None:
        self._append(self._receipts, receipt.transaction_id, receipt)

    def get_receipt(
        self,
        transaction_id: str,
    ) -> GovernedTransactionReceipt | None:
        path = self._receipts / f"{self._safe_identifier(transaction_id)}.json"
        if not path.exists():
            return None
        return GovernedTransactionReceipt.model_validate_json(
            path.read_text(encoding="utf-8")
        )
