"""Governed retention, archival, restriction, and cryptographic continuity.

The implementation is TEST-first and append-only. Lifecycle actions create new
receipted records that reference prior hashes; they never overwrite historical
records. Hash migration proves continuity between approved algorithms without
invalidating the original digest.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryContext


_APPROVED_HASH_ALGORITHMS = {"sha256", "sha3_256", "sha512"}


class LifecycleState(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    RESTRICTED = "RESTRICTED"
    REDACTED = "REDACTED"
    TOMBSTONED = "TOMBSTONED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class LifecycleAction(StrEnum):
    ARCHIVE = "ARCHIVE"
    RESTRICT = "RESTRICT"
    REDACT = "REDACT"
    TOMBSTONE = "TOMBSTONE"
    EXPIRE = "EXPIRE"
    REVOKE = "REVOKE"
    RESTORE = "RESTORE"


class RetentionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    boundary: BoundaryContext
    purpose: str = Field(min_length=1)
    authority_class: str = Field(min_length=1)
    authored_by: str = Field(min_length=1)
    authored_at: datetime
    retain_until: datetime | None = None
    archive_after: datetime | None = None
    permitted_actions: set[LifecycleAction] = Field(min_length=1)
    policy_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_policy(self) -> "RetentionPolicy":
        if self.boundary.execution_context != ExecutionContext.TEST:
            raise ValueError("Sprint 19 retention policies are TEST-only")
        if self.retain_until is not None and self.retain_until <= self.authored_at:
            raise ValueError("retain_until must follow authored_at")
        if self.archive_after is not None and self.archive_after <= self.authored_at:
            raise ValueError("archive_after must follow authored_at")
        if (
            self.retain_until is not None
            and self.archive_after is not None
            and self.archive_after > self.retain_until
        ):
            raise ValueError("archive_after cannot follow retain_until")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"policy_sha256"}))
        if self.policy_sha256 != expected:
            raise ValueError("retention policy hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "RetentionPolicy":
        payload = dict(values)
        payload["policy_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class RetainedRecord(BaseModel):
    """Immutable content-bearing record used by lifecycle proof."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(min_length=1)
    boundary: BoundaryContext
    purpose: str = Field(min_length=1)
    payload: dict[str, object]
    payload_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    created_at: datetime
    authority_id: str = Field(min_length=1)
    lineage_hashes: list[str] = Field(default_factory=list)
    record_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_record(self) -> "RetainedRecord":
        if self.boundary.execution_context != ExecutionContext.TEST:
            raise ValueError("Sprint 19 records are TEST-only")
        if self.payload_sha256 != canonical_sha256(self.payload):
            raise ValueError("retained payload hash is invalid")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"record_sha256"}))
        if self.record_sha256 != expected:
            raise ValueError("retained record hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "RetainedRecord":
        payload = dict(values)
        payload.setdefault("lineage_hashes", [])
        payload["payload_sha256"] = canonical_sha256(payload["payload"])
        payload["record_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class LifecycleAuthorization(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_id: str = Field(min_length=1)
    policy_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    boundary_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    record_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    action: LifecycleAction
    authority_class: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    issued_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None

    def valid_at(self, now: datetime) -> bool:
        return (
            (self.expires_at is None or now < self.expires_at)
            and (self.revoked_at is None or now < self.revoked_at)
        )


class LifecycleRecord(BaseModel):
    """Append-only state transition preserving the historical source hash."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    lifecycle_id: str = Field(min_length=1)
    record_id: str = Field(min_length=1)
    original_record_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    previous_lifecycle_sha256: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
    )
    state: LifecycleState
    action: LifecycleAction
    boundary: BoundaryContext
    policy_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    authorization_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    redacted_payload: dict[str, object] | None = None
    occurred_at: datetime
    lifecycle_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_lifecycle(self) -> "LifecycleRecord":
        if self.boundary.execution_context != ExecutionContext.TEST:
            raise ValueError("Sprint 19 lifecycle records are TEST-only")
        if self.state == LifecycleState.REDACTED and self.redacted_payload is None:
            raise ValueError("redacted lifecycle requires a redacted payload")
        if self.state != LifecycleState.REDACTED and self.redacted_payload is not None:
            raise ValueError("only redacted lifecycle records may carry replacement payload")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"lifecycle_sha256"})
        )
        if self.lifecycle_sha256 != expected:
            raise ValueError("lifecycle record hash is invalid")
        return self


class LifecycleReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    authorization_id: str = Field(min_length=1)
    policy_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    before_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    after_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    execution_context: ExecutionContext
    committed_at: datetime
    receipt_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_receipt(self) -> "LifecycleReceipt":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("Sprint 19 receipts are TEST-only")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"receipt_sha256"}))
        if self.receipt_sha256 != expected:
            raise ValueError("lifecycle receipt hash is invalid")
        return self


class CryptographicContinuityProof(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    proof_id: str = Field(min_length=1)
    record_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    old_algorithm: str
    old_digest: str
    new_algorithm: str
    new_digest: str
    payload_length: int = Field(ge=0)
    authority_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    created_at: datetime
    proof_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_algorithms_and_hash(self) -> "CryptographicContinuityProof":
        if self.old_algorithm not in _APPROVED_HASH_ALGORITHMS:
            raise ValueError("old hash algorithm is not approved")
        if self.new_algorithm not in _APPROVED_HASH_ALGORITHMS:
            raise ValueError("new hash algorithm is not approved")
        if self.old_algorithm == self.new_algorithm:
            raise ValueError("hash migration requires a different algorithm")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"proof_sha256"}))
        if self.proof_sha256 != expected:
            raise ValueError("cryptographic continuity proof hash is invalid")
        return self


class LifecycleRepository(Protocol):
    def append_policy(self, policy: RetentionPolicy) -> None: ...
    def append_record(self, record: RetainedRecord) -> None: ...
    def get_record(self, record_id: str) -> RetainedRecord | None: ...
    def append_lifecycle(self, record: LifecycleRecord) -> None: ...
    def list_lifecycle(self, record_id: str) -> list[LifecycleRecord]: ...
    def append_receipt(self, receipt: LifecycleReceipt) -> None: ...
    def get_receipt(self, transaction_id: str) -> LifecycleReceipt | None: ...
    def append_continuity_proof(self, proof: CryptographicContinuityProof) -> None: ...


class LifecycleConflict(RuntimeError):
    pass


def _state_for_action(action: LifecycleAction) -> LifecycleState:
    return {
        LifecycleAction.ARCHIVE: LifecycleState.ARCHIVED,
        LifecycleAction.RESTRICT: LifecycleState.RESTRICTED,
        LifecycleAction.REDACT: LifecycleState.REDACTED,
        LifecycleAction.TOMBSTONE: LifecycleState.TOMBSTONED,
        LifecycleAction.EXPIRE: LifecycleState.EXPIRED,
        LifecycleAction.REVOKE: LifecycleState.REVOKED,
        LifecycleAction.RESTORE: LifecycleState.ACTIVE,
    }[action]


class RetentionLifecycleService:
    def __init__(self, repository: LifecycleRepository) -> None:
        self._repository = repository

    def apply(
        self,
        *,
        record: RetainedRecord,
        policy: RetentionPolicy,
        authorization: LifecycleAuthorization,
        action: LifecycleAction,
        transaction_id: str,
        now: datetime,
        reason_code: str,
        redacted_payload: dict[str, object] | None = None,
    ) -> LifecycleReceipt:
        existing_receipt = self._repository.get_receipt(transaction_id)
        if existing_receipt is not None:
            return existing_receipt
        if record.boundary != policy.boundary:
            raise LifecycleConflict("record and policy boundaries do not match")
        if record.purpose != policy.purpose or authorization.purpose != policy.purpose:
            raise LifecycleConflict("retention purpose mismatch")
        if authorization.action != action:
            raise LifecycleConflict("lifecycle authorization action mismatch")
        if authorization.policy_sha256 != policy.policy_sha256:
            raise LifecycleConflict("lifecycle authorization policy mismatch")
        if authorization.record_sha256 != record.record_sha256:
            raise LifecycleConflict("lifecycle authorization record mismatch")
        if authorization.boundary_sha256 != record.boundary.boundary_sha256:
            raise LifecycleConflict("lifecycle authorization boundary mismatch")
        if authorization.authority_class != policy.authority_class:
            raise LifecycleConflict("lifecycle authority class mismatch")
        if action not in policy.permitted_actions:
            raise LifecycleConflict("lifecycle action is not permitted by policy")
        if not authorization.valid_at(now):
            raise LifecycleConflict("lifecycle authorization is expired or revoked")
        if action == LifecycleAction.ARCHIVE and policy.archive_after is not None and now < policy.archive_after:
            raise LifecycleConflict("archive action is premature")
        if action == LifecycleAction.EXPIRE and policy.retain_until is not None and now < policy.retain_until:
            raise LifecycleConflict("expiration action is premature")

        history = self._repository.list_lifecycle(record.record_id)
        previous = history[-1] if history else None
        previous_state = previous.state if previous else LifecycleState.ACTIVE
        if previous_state in {LifecycleState.TOMBSTONED, LifecycleState.REVOKED}:
            raise LifecycleConflict("terminal lifecycle state cannot be changed")
        if action == LifecycleAction.RESTORE and previous_state not in {
            LifecycleState.ARCHIVED,
            LifecycleState.RESTRICTED,
        }:
            raise LifecycleConflict("only archived or restricted records may be restored")

        lifecycle_payload = {
            "lifecycle_id": f"LIFE-{transaction_id}",
            "record_id": record.record_id,
            "original_record_sha256": record.record_sha256,
            "previous_lifecycle_sha256": previous.lifecycle_sha256 if previous else None,
            "state": _state_for_action(action),
            "action": action,
            "boundary": record.boundary,
            "policy_sha256": policy.policy_sha256,
            "authorization_id": authorization.authorization_id,
            "transaction_id": transaction_id,
            "reason_code": reason_code,
            "redacted_payload": redacted_payload,
            "occurred_at": now,
        }
        lifecycle = LifecycleRecord(
            **lifecycle_payload,
            lifecycle_sha256=canonical_sha256(lifecycle_payload),
        )
        self._repository.append_policy(policy)
        self._repository.append_record(record)
        self._repository.append_lifecycle(lifecycle)

        before_sha = previous.lifecycle_sha256 if previous else record.record_sha256
        receipt_payload = {
            "receipt_id": f"LIFE-RCPT-{transaction_id}",
            "transaction_id": transaction_id,
            "authorization_id": authorization.authorization_id,
            "policy_sha256": policy.policy_sha256,
            "before_sha256": before_sha,
            "after_sha256": lifecycle.lifecycle_sha256,
            "execution_context": ExecutionContext.TEST,
            "committed_at": now,
        }
        receipt = LifecycleReceipt(
            **receipt_payload,
            receipt_sha256=canonical_sha256(receipt_payload),
        )
        self._repository.append_receipt(receipt)
        return receipt

    def current_state(self, record_id: str, *, now: datetime) -> LifecycleState:
        record = self._repository.get_record(record_id)
        if record is None:
            raise KeyError(record_id)
        history = self._repository.list_lifecycle(record_id)
        return history[-1].state if history else LifecycleState.ACTIVE

    def may_control_downstream(
        self,
        record_id: str,
        *,
        now: datetime,
        authorized_boundary: BoundaryContext,
    ) -> bool:
        record = self._repository.get_record(record_id)
        if record is None or record.boundary != authorized_boundary:
            return False
        state = self.current_state(record_id, now=now)
        return state == LifecycleState.ACTIVE


def create_continuity_proof(
    *,
    record: RetainedRecord,
    payload_bytes: bytes,
    old_algorithm: str,
    new_algorithm: str,
    authority_id: str,
    transaction_id: str,
    now: datetime,
) -> CryptographicContinuityProof:
    if old_algorithm not in _APPROVED_HASH_ALGORITHMS or new_algorithm not in _APPROVED_HASH_ALGORITHMS:
        raise ValueError("unsupported hash algorithm")
    old_digest = hashlib.new(old_algorithm, payload_bytes).hexdigest()
    new_digest = hashlib.new(new_algorithm, payload_bytes).hexdigest()
    payload = {
        "proof_id": f"HASH-MIG-{transaction_id}",
        "record_sha256": record.record_sha256,
        "old_algorithm": old_algorithm,
        "old_digest": old_digest,
        "new_algorithm": new_algorithm,
        "new_digest": new_digest,
        "payload_length": len(payload_bytes),
        "authority_id": authority_id,
        "transaction_id": transaction_id,
        "created_at": now,
    }
    return CryptographicContinuityProof(
        **payload,
        proof_sha256=canonical_sha256(payload),
    )


def verify_continuity_proof(
    proof: CryptographicContinuityProof,
    *,
    payload_bytes: bytes,
) -> bool:
    return (
        len(payload_bytes) == proof.payload_length
        and hashlib.new(proof.old_algorithm, payload_bytes).hexdigest() == proof.old_digest
        and hashlib.new(proof.new_algorithm, payload_bytes).hexdigest() == proof.new_digest
    )
