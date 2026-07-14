"""Deterministic parity proof for declared forensic adapter capabilities."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from nks.application.forensic_reconstruction import ForensicEvidenceStore, ForensicRecord
from nks.application.governed_transactions import canonical_sha256


class AdapterParityResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    capabilities: list[str]
    record_ids: list[str]
    left_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    right_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    equivalent: bool


def prove_adapter_parity(
    left: ForensicEvidenceStore,
    right: ForensicEvidenceStore,
    records: list[ForensicRecord],
) -> AdapterParityResult:
    if left.capabilities != right.capabilities:
        raise RuntimeError("adapter capability declarations differ")
    for record in records:
        left.append(record)
        right.append(record)
    left_records = left.list_records()
    right_records = right.list_records()
    left_payload = [record.model_dump(mode="python") for record in left_records]
    right_payload = [record.model_dump(mode="python") for record in right_records]
    left_hash = canonical_sha256(left_payload)
    right_hash = canonical_sha256(right_payload)
    return AdapterParityResult(
        capabilities=sorted(left.capabilities),
        record_ids=[record.record_id for record in left_records],
        left_sha256=left_hash,
        right_sha256=right_hash,
        equivalent=left_payload == right_payload and left_hash == right_hash,
    )
