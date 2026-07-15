"""Append-only local persistence for Sprint 19 retention evidence."""

from __future__ import annotations

import json
from pathlib import Path

from nks.application.retention_continuity import (
    CryptographicContinuityProof,
    LifecycleReceipt,
    LifecycleRecord,
    RetainedRecord,
    RetentionPolicy,
)


class RetentionRecordConflict(RuntimeError):
    pass


class JsonRetentionRepository:
    def __init__(self, root: Path) -> None:
        base = root / "records"
        self._policies = base / "retention-policies"
        self._records = base / "retained-records"
        self._lifecycle = base / "retention-lifecycle"
        self._receipts = base / "retention-receipts"
        self._continuity = base / "cryptographic-continuity"
        for path in (
            self._policies,
            self._records,
            self._lifecycle,
            self._receipts,
            self._continuity,
        ):
            path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _token(value: str) -> str:
        return value.replace("/", "_").replace("\\", "_").replace(":", "_")

    @staticmethod
    def _append(path: Path, record: object) -> None:
        payload = record.model_dump(mode="json", exclude_none=False)  # type: ignore[attr-defined]
        content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        if path.exists():
            if path.read_text(encoding="utf-8") == content:
                return
            raise RetentionRecordConflict(f"immutable retention record conflict: {path.name}")
        path.write_text(content, encoding="utf-8")

    def append_policy(self, policy: RetentionPolicy) -> None:
        self._append(
            self._policies / f"{policy.policy_sha256.removeprefix('sha256:')}.json",
            policy,
        )

    def append_record(self, record: RetainedRecord) -> None:
        self._append(self._records / f"{self._token(record.record_id)}.json", record)

    def get_record(self, record_id: str) -> RetainedRecord | None:
        path = self._records / f"{self._token(record_id)}.json"
        if not path.exists():
            return None
        return RetainedRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def append_lifecycle(self, record: LifecycleRecord) -> None:
        self._append(
            self._lifecycle / f"{self._token(record.lifecycle_id)}.json",
            record,
        )

    def list_lifecycle(self, record_id: str) -> list[LifecycleRecord]:
        records = [
            LifecycleRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self._lifecycle.glob("*.json"))
        ]
        return sorted(
            [item for item in records if item.record_id == record_id],
            key=lambda item: (item.occurred_at, item.lifecycle_id),
        )

    def append_receipt(self, receipt: LifecycleReceipt) -> None:
        self._append(
            self._receipts / f"{self._token(receipt.transaction_id)}.json",
            receipt,
        )

    def get_receipt(self, transaction_id: str) -> LifecycleReceipt | None:
        path = self._receipts / f"{self._token(transaction_id)}.json"
        if not path.exists():
            return None
        return LifecycleReceipt.model_validate_json(path.read_text(encoding="utf-8"))

    def append_continuity_proof(self, proof: CryptographicContinuityProof) -> None:
        self._append(
            self._continuity / f"{self._token(proof.proof_id)}.json",
            proof,
        )
