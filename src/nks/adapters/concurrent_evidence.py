"""Append-only filesystem and GitHub-content adapters for Sprint 20 evidence.

Both adapters expose the same immutable append/get/list surface used to persist
write intents, effects, and terminal receipts for deterministic reconstruction.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.governance.approvals import ExecutionContext


SHARED_CONCURRENCY_CAPABILITIES = frozenset(
    {"append", "get", "list", "exact-retry", "conflict-denial", "reconstruct"}
)


class ConcurrentEvidenceConflict(RuntimeError):
    pass


class ConcurrentEvidenceKind(str):
    INTENT = "INTENT"
    EFFECT = "EFFECT"
    RECEIPT = "RECEIPT"


class ConcurrentEvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(min_length=1)
    key: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    kind: str = Field(pattern=r"^(INTENT|EFFECT|RECEIPT)$")
    payload: dict[str, object]
    payload_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    execution_context: ExecutionContext = ExecutionContext.TEST
    record_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_record(self) -> "ConcurrentEvidenceRecord":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("Sprint 20 adapter evidence is TEST-only")
        if self.payload_sha256 != canonical_sha256(self.payload):
            raise ValueError("concurrency evidence payload hash is invalid")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"record_sha256"}))
        if self.record_sha256 != expected:
            raise ValueError("concurrency evidence record hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "ConcurrentEvidenceRecord":
        payload = dict(values)
        payload.setdefault("execution_context", ExecutionContext.TEST)
        payload["payload_sha256"] = canonical_sha256(payload["payload"])
        payload["record_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class ConcurrentEvidenceStore(Protocol):
    capabilities: frozenset[str]

    def append(self, record: ConcurrentEvidenceRecord) -> None: ...
    def get(self, record_id: str) -> ConcurrentEvidenceRecord | None: ...
    def list_records(self) -> list[ConcurrentEvidenceRecord]: ...


class JsonConcurrentEvidenceStore:
    capabilities = SHARED_CONCURRENCY_CAPABILITIES

    def __init__(self, root: Path) -> None:
        self._directory = root / "concurrent-evidence"
        self._directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _serialize(record: ConcurrentEvidenceRecord) -> str:
        return json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"

    def append(self, record: ConcurrentEvidenceRecord) -> None:
        path = self._directory / f"{record.record_id}.json"
        content = self._serialize(record)
        if path.exists():
            if path.read_text(encoding="utf-8") == content:
                return
            raise ConcurrentEvidenceConflict(
                f"immutable concurrency evidence already exists: {record.record_id}"
            )
        path.write_text(content, encoding="utf-8")

    def get(self, record_id: str) -> ConcurrentEvidenceRecord | None:
        path = self._directory / f"{record_id}.json"
        if not path.exists():
            return None
        return ConcurrentEvidenceRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def list_records(self) -> list[ConcurrentEvidenceRecord]:
        return [
            ConcurrentEvidenceRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self._directory.glob("*.json"))
        ]


class GitHubContentsClient(Protocol):
    def read_file(self, path: str) -> str | None: ...
    def create_file(self, path: str, content: str) -> None: ...
    def list_files(self, prefix: str) -> list[str]: ...


class GitHubConcurrentEvidenceStore:
    capabilities = SHARED_CONCURRENCY_CAPABILITIES

    def __init__(
        self,
        client: GitHubContentsClient,
        prefix: str = "concurrent-evidence",
    ) -> None:
        self._client = client
        self._prefix = prefix.rstrip("/")

    @staticmethod
    def _serialize(record: ConcurrentEvidenceRecord) -> str:
        return json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"

    def _path(self, record_id: str) -> str:
        return f"{self._prefix}/{record_id}.json"

    def append(self, record: ConcurrentEvidenceRecord) -> None:
        path = self._path(record.record_id)
        content = self._serialize(record)
        existing = self._client.read_file(path)
        if existing is not None:
            if existing == content:
                return
            raise ConcurrentEvidenceConflict(
                f"immutable concurrency evidence already exists: {record.record_id}"
            )
        self._client.create_file(path, content)

    def get(self, record_id: str) -> ConcurrentEvidenceRecord | None:
        content = self._client.read_file(self._path(record_id))
        if content is None:
            return None
        return ConcurrentEvidenceRecord.model_validate_json(content)

    def list_records(self) -> list[ConcurrentEvidenceRecord]:
        return [
            ConcurrentEvidenceRecord.model_validate_json(content)
            for path in sorted(self._client.list_files(self._prefix))
            if (content := self._client.read_file(path)) is not None
        ]


class ConcurrentReconstruction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str
    ordered_record_ids: list[str]
    intent_count: int
    effect_count: int
    receipt_count: int
    complete: bool
    reconstruction_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "ConcurrentReconstruction":
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"reconstruction_sha256"})
        )
        if self.reconstruction_sha256 != expected:
            raise ValueError("concurrent reconstruction hash is invalid")
        return self


def reconstruct_concurrent_evidence(
    store: ConcurrentEvidenceStore,
    *,
    key: str,
) -> ConcurrentReconstruction:
    records = sorted(
        [record for record in store.list_records() if record.key == key],
        key=lambda record: (record.sequence, record.kind, record.record_id),
    )
    intent_count = sum(record.kind == ConcurrentEvidenceKind.INTENT for record in records)
    effect_count = sum(record.kind == ConcurrentEvidenceKind.EFFECT for record in records)
    receipt_count = sum(record.kind == ConcurrentEvidenceKind.RECEIPT for record in records)
    payload = {
        "key": key,
        "ordered_record_ids": [record.record_id for record in records],
        "intent_count": intent_count,
        "effect_count": effect_count,
        "receipt_count": receipt_count,
        "complete": intent_count == effect_count == receipt_count and intent_count > 0,
    }
    return ConcurrentReconstruction(
        **payload,
        reconstruction_sha256=canonical_sha256(payload),
    )


class ConcurrentAdapterParityResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    capabilities: list[str]
    left_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    right_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    left_reconstruction_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    right_reconstruction_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    equivalent: bool


def prove_concurrent_adapter_parity(
    left: ConcurrentEvidenceStore,
    right: ConcurrentEvidenceStore,
    records: list[ConcurrentEvidenceRecord],
    *,
    key: str,
) -> ConcurrentAdapterParityResult:
    if left.capabilities != right.capabilities:
        raise RuntimeError("concurrency adapter capability declarations differ")
    for record in records:
        left.append(record)
        right.append(record)
        # Exact retry must be idempotent on both implementations.
        left.append(record)
        right.append(record)
    left_records = left.list_records()
    right_records = right.list_records()
    left_payload = [record.model_dump(mode="python") for record in left_records]
    right_payload = [record.model_dump(mode="python") for record in right_records]
    left_hash = canonical_sha256(left_payload)
    right_hash = canonical_sha256(right_payload)
    left_reconstruction = reconstruct_concurrent_evidence(left, key=key)
    right_reconstruction = reconstruct_concurrent_evidence(right, key=key)
    return ConcurrentAdapterParityResult(
        capabilities=sorted(left.capabilities),
        left_sha256=left_hash,
        right_sha256=right_hash,
        left_reconstruction_sha256=left_reconstruction.reconstruction_sha256,
        right_reconstruction_sha256=right_reconstruction.reconstruction_sha256,
        equivalent=(
            left_payload == right_payload
            and left_hash == right_hash
            and left_reconstruction == right_reconstruction
        ),
    )
