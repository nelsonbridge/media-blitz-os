"""Governed zero-cost boundary isolation using synthetic TEST data.

This module proves Enki software isolation semantics. It does not claim that a
future production cloud, network, database, or key-management deployment has
been configured or independently certified.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import (
    BoundaryAction,
    BoundaryAuthorization,
    BoundaryContext,
    BoundaryOutcome,
    HumanBoundaryPolicy,
    evaluate_boundary_authorization,
)


class BoundaryIsolationError(RuntimeError):
    """Generic fail-closed error that never embeds protected identifiers."""

    def __init__(self, reason_code: str) -> None:
        super().__init__("boundary operation denied")
        self.reason_code = reason_code


class BoundaryConflict(BoundaryIsolationError):
    pass


class BoundaryStore(Protocol):
    def put(self, record: "BoundaryRecord") -> "BoundaryRecord": ...
    def get(self, boundary: BoundaryContext, record_id: str) -> "BoundaryRecord | None": ...
    def count(self, boundary: BoundaryContext) -> int: ...


class BoundaryRecord(BaseModel):
    """Immutable record whose payload and complete boundary are hash-bound."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
    subject_type: str = Field(pattern=r"^[A-Z][A-Z0-9_-]{0,63}$")
    boundary: BoundaryContext
    payload: dict[str, object]
    payload_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    record_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hashes(self) -> "BoundaryRecord":
        if ".." in self.record_id or "/" in self.record_id or "\\" in self.record_id:
            raise ValueError("record_id cannot contain path traversal")
        expected_payload = canonical_sha256(self.payload)
        if self.payload_sha256 != expected_payload:
            raise ValueError("payload hash is invalid")
        expected_record = canonical_sha256(
            {
                "record_id": self.record_id,
                "subject_type": self.subject_type,
                "boundary": self.boundary,
                "payload_sha256": self.payload_sha256,
            }
        )
        if self.record_sha256 != expected_record:
            raise ValueError("record hash is invalid")
        return self

    @classmethod
    def create(
        cls,
        *,
        record_id: str,
        subject_type: str,
        boundary: BoundaryContext,
        payload: dict[str, object],
    ) -> "BoundaryRecord":
        payload_sha256 = canonical_sha256(payload)
        record_sha256 = canonical_sha256(
            {
                "record_id": record_id,
                "subject_type": subject_type,
                "boundary": boundary,
                "payload_sha256": payload_sha256,
            }
        )
        return cls(
            record_id=record_id,
            subject_type=subject_type,
            boundary=boundary,
            payload=payload,
            payload_sha256=payload_sha256,
            record_sha256=record_sha256,
        )


class BoundaryPackage(BaseModel):
    """Portable exact-boundary package for export, import, replay, and recovery."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    package_id: str = Field(min_length=1)
    record: BoundaryRecord
    source_boundary_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    package_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_package(self) -> "BoundaryPackage":
        if self.source_boundary_sha256 != self.record.boundary.boundary_sha256:
            raise ValueError("package source boundary is invalid")
        expected = canonical_sha256(
            {
                "package_id": self.package_id,
                "record": self.record,
                "source_boundary_sha256": self.source_boundary_sha256,
            }
        )
        if self.package_sha256 != expected:
            raise ValueError("package hash is invalid")
        return self

    @classmethod
    def create(cls, record: BoundaryRecord) -> "BoundaryPackage":
        package_id = f"PKG-{record.record_sha256.removeprefix('sha256:')[:24]}"
        source = record.boundary.boundary_sha256
        payload = {
            "package_id": package_id,
            "record": record,
            "source_boundary_sha256": source,
        }
        return cls(
            **payload,
            package_sha256=canonical_sha256(payload),
        )


class BoundaryAuditEvent(BaseModel):
    """Privacy-preserving diagnostic evidence for an isolation decision."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(min_length=1)
    action: BoundaryAction
    outcome: BoundaryOutcome
    boundary_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    record_id_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    reason_code: str = Field(min_length=1)
    occurred_at: datetime
    event_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_event_hash(self) -> "BoundaryAuditEvent":
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"event_sha256"}))
        if self.event_sha256 != expected:
            raise ValueError("audit event hash is invalid")
        return self


class BoundaryIsolationService:
    """Apply exact-boundary authorization to a local TEST-only store."""

    def __init__(self, store: BoundaryStore) -> None:
        self._store = store
        self._events: list[BoundaryAuditEvent] = []

    @property
    def audit_events(self) -> tuple[BoundaryAuditEvent, ...]:
        return tuple(self._events)

    def _audit(
        self,
        *,
        action: BoundaryAction,
        outcome: BoundaryOutcome,
        boundary: BoundaryContext,
        record_id: str,
        reason_code: str,
        now: datetime,
    ) -> None:
        payload = {
            "event_id": f"BND-EVT-{len(self._events) + 1:06d}",
            "action": action,
            "outcome": outcome,
            "boundary_sha256": boundary.boundary_sha256,
            "record_id_sha256": canonical_sha256(record_id),
            "reason_code": reason_code,
            "occurred_at": now,
        }
        self._events.append(
            BoundaryAuditEvent(**payload, event_sha256=canonical_sha256(payload))
        )

    def _authorize(
        self,
        authorization: BoundaryAuthorization,
        *,
        action: BoundaryAction,
        boundary: BoundaryContext,
        record_id: str,
        now: datetime,
    ) -> None:
        decision = evaluate_boundary_authorization(
            authorization,
            action=action,
            requested_boundary=boundary,
            evaluated_at=now,
        )
        self._audit(
            action=action,
            outcome=decision.outcome,
            boundary=boundary,
            record_id=record_id,
            reason_code=decision.reason_code,
            now=now,
        )
        if decision.outcome != BoundaryOutcome.ALLOWED:
            raise BoundaryIsolationError(decision.reason_code)

    @staticmethod
    def _human_policy(
        record: BoundaryRecord,
        human_policy: HumanBoundaryPolicy | None,
    ) -> None:
        if record.subject_type != "PERSON":
            return
        if human_policy is None or not human_policy.permits_use:
            raise BoundaryIsolationError("HUMAN_POLICY_DENIED")

    def write(
        self,
        record: BoundaryRecord,
        *,
        authorization: BoundaryAuthorization,
        now: datetime,
        human_policy: HumanBoundaryPolicy | None = None,
    ) -> BoundaryRecord:
        self._authorize(
            authorization,
            action=BoundaryAction.WRITE,
            boundary=record.boundary,
            record_id=record.record_id,
            now=now,
        )
        try:
            self._human_policy(record, human_policy)
            return self._store.put(record)
        except BoundaryIsolationError as error:
            self._audit(
                action=BoundaryAction.WRITE,
                outcome=BoundaryOutcome.DENIED,
                boundary=record.boundary,
                record_id=record.record_id,
                reason_code=error.reason_code,
                now=now,
            )
            raise

    def read(
        self,
        *,
        boundary: BoundaryContext,
        record_id: str,
        authorization: BoundaryAuthorization,
        now: datetime,
        human_policy: HumanBoundaryPolicy | None = None,
    ) -> BoundaryRecord:
        self._authorize(
            authorization,
            action=BoundaryAction.READ,
            boundary=boundary,
            record_id=record_id,
            now=now,
        )
        record = self._store.get(boundary, record_id)
        if record is None:
            raise BoundaryIsolationError("RECORD_NOT_AVAILABLE_IN_BOUNDARY")
        self._human_policy(record, human_policy)
        return record

    def export(
        self,
        *,
        boundary: BoundaryContext,
        record_id: str,
        authorization: BoundaryAuthorization,
        now: datetime,
        human_policy: HumanBoundaryPolicy | None = None,
    ) -> BoundaryPackage:
        self._authorize(
            authorization,
            action=BoundaryAction.EXPORT,
            boundary=boundary,
            record_id=record_id,
            now=now,
        )
        record = self._store.get(boundary, record_id)
        if record is None:
            raise BoundaryIsolationError("RECORD_NOT_AVAILABLE_IN_BOUNDARY")
        self._human_policy(record, human_policy)
        return BoundaryPackage.create(record)

    def import_package(
        self,
        package: BoundaryPackage,
        *,
        target_boundary: BoundaryContext,
        authorization: BoundaryAuthorization,
        now: datetime,
        action: BoundaryAction = BoundaryAction.IMPORT,
        human_policy: HumanBoundaryPolicy | None = None,
    ) -> BoundaryRecord:
        self._authorize(
            authorization,
            action=action,
            boundary=target_boundary,
            record_id=package.record.record_id,
            now=now,
        )
        if package.record.boundary != target_boundary:
            self._audit(
                action=action,
                outcome=BoundaryOutcome.DENIED,
                boundary=target_boundary,
                record_id=package.record.record_id,
                reason_code="PACKAGE_BOUNDARY_MISMATCH",
                now=now,
            )
            raise BoundaryIsolationError("PACKAGE_BOUNDARY_MISMATCH")
        self._human_policy(package.record, human_policy)
        return self._store.put(package.record)

    def recover(
        self,
        package: BoundaryPackage,
        *,
        expected_boundary: BoundaryContext,
        authorization: BoundaryAuthorization,
        now: datetime,
        human_policy: HumanBoundaryPolicy | None = None,
    ) -> BoundaryRecord:
        return self.import_package(
            package,
            target_boundary=expected_boundary,
            authorization=authorization,
            now=now,
            action=BoundaryAction.RECOVER,
            human_policy=human_policy,
        )

    def replay(
        self,
        package: BoundaryPackage,
        *,
        expected_boundary: BoundaryContext,
        authorization: BoundaryAuthorization,
        now: datetime,
        human_policy: HumanBoundaryPolicy | None = None,
    ) -> BoundaryRecord:
        return self.import_package(
            package,
            target_boundary=expected_boundary,
            authorization=authorization,
            now=now,
            action=BoundaryAction.REPLAY,
            human_policy=human_policy,
        )

    def count(self, boundary: BoundaryContext) -> int:
        if boundary.execution_context != ExecutionContext.TEST:
            raise BoundaryIsolationError("TEST_PROOF_CANNOT_INSPECT_PRODUCTION")
        return self._store.count(boundary)
