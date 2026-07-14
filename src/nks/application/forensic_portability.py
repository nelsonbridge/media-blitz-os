"""Portable, hash-bound evidence packages and exact clean-room recovery."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.forensic_contracts import ForensicEvidenceStore, ForensicRecord, evidence_hash
from nks.application.governed_transactions import canonical_sha256
from nks.governance.approvals import ExecutionContext


class PortableEvidencePackage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    package_id: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    execution_context: ExecutionContext
    exported_at: datetime
    records: list[ForensicRecord] = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_unique_records(self) -> "PortableEvidencePackage":
        ids = [record.record_id for record in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("portable package record ids must be unique")
        return self


def _manifest_payload(
    *,
    package_id: str,
    schema_version: str,
    execution_context: ExecutionContext,
    exported_at: datetime,
    records: list[ForensicRecord],
) -> dict[str, object]:
    return {
        "package_id": package_id,
        "schema_version": schema_version,
        "execution_context": execution_context,
        "exported_at": exported_at,
        "record_hashes": [
            {
                "record_id": record.record_id,
                "content_sha256": record.content_sha256,
                "record_sha256": canonical_sha256(record),
            }
            for record in sorted(records, key=lambda item: item.record_id)
        ],
    }


def build_portable_package(
    *,
    package_id: str,
    execution_context: ExecutionContext,
    records: list[ForensicRecord],
    exported_at: datetime,
    schema_version: str = "enki-portable-evidence/v1",
) -> PortableEvidencePackage:
    if not records:
        raise ValueError("portable evidence package requires records")
    for record in records:
        if record.execution_context != execution_context:
            raise ValueError("portable package cannot mix execution contexts")
        if record.content_sha256 != canonical_sha256(record.payload):
            raise ValueError(f"record payload hash mismatch: {record.record_id}")
    payload = _manifest_payload(
        package_id=package_id,
        schema_version=schema_version,
        execution_context=execution_context,
        exported_at=exported_at,
        records=records,
    )
    return PortableEvidencePackage(
        package_id=package_id,
        schema_version=schema_version,
        execution_context=execution_context,
        exported_at=exported_at,
        records=sorted(records, key=lambda item: item.record_id),
        manifest_sha256=canonical_sha256(payload),
    )


def assert_portable_package_integrity(package: PortableEvidencePackage) -> None:
    for record in package.records:
        if record.execution_context != package.execution_context:
            raise ValueError("portable package contains a cross-context record")
        if record.content_sha256 != canonical_sha256(record.payload):
            raise ValueError(f"record payload hash mismatch: {record.record_id}")
    expected = canonical_sha256(_manifest_payload(
        package_id=package.package_id,
        schema_version=package.schema_version,
        execution_context=package.execution_context,
        exported_at=package.exported_at,
        records=package.records,
    ))
    if package.manifest_sha256 != expected:
        raise ValueError("portable package manifest hash mismatch")


class RecoveryReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    recovery_id: str
    package_id: str
    execution_context: ExecutionContext
    record_count: int = Field(ge=1)
    manifest_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    destination_evidence_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    exact_retry: bool
    recovered_at: datetime


def recover_portable_package(
    package: PortableEvidencePackage,
    *,
    destination: ForensicEvidenceStore,
    destination_context: ExecutionContext,
    recovered_at: datetime,
) -> RecoveryReceipt:
    assert_portable_package_integrity(package)
    if destination_context != package.execution_context:
        raise PermissionError("portable recovery cannot change execution context")
    existing = {record.record_id for record in destination.list_records()}
    for record in package.records:
        destination.append(record)
    by_id = {record.record_id: record for record in destination.list_records()}
    for expected in package.records:
        if by_id.get(expected.record_id) != expected:
            raise RuntimeError(f"recovery did not reproduce exact record: {expected.record_id}")
    return RecoveryReceipt(
        recovery_id=f"RECOVERY-{package.package_id}",
        package_id=package.package_id,
        execution_context=destination_context,
        record_count=len(package.records),
        manifest_sha256=package.manifest_sha256,
        destination_evidence_sha256=evidence_hash([
            by_id[record.record_id] for record in package.records
        ]),
        exact_retry=all(record.record_id in existing for record in package.records),
        recovered_at=recovered_at,
    )
