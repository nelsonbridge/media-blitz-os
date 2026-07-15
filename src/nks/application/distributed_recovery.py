"""Zero-cost concurrent authority, contention, and recovery proof.

The coordinator uses local TEST threads and deterministic in-memory state. It
models compare-and-swap writes, exclusive authority leases, duplicate and
out-of-order delivery, partition queues, interruption after durable mutation,
and exact recovery without split authority, duplicate effects, or lost receipts.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from threading import RLock
from typing import Callable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryContext


class DeliveryState(StrEnum):
    RECEIVED = "RECEIVED"
    DEFERRED = "DEFERRED"
    COMMITTED = "COMMITTED"
    DUPLICATE = "DUPLICATE"
    CONFLICT = "CONFLICT"
    INTERRUPTED = "INTERRUPTED"
    REJECTED = "REJECTED"


class ReconstructionState(StrEnum):
    COMPLETE = "COMPLETE"
    PENDING = "PENDING"
    CONFLICT = "CONFLICT"
    REPAIRABLE = "REPAIRABLE"


class VersionedValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str = Field(min_length=1)
    version: int = Field(ge=1)
    payload: dict[str, object]
    payload_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    boundary: BoundaryContext
    authority_epoch: int = Field(ge=1)
    committed_by: str = Field(min_length=1)
    value_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hashes(self) -> "VersionedValue":
        if self.boundary.execution_context != ExecutionContext.TEST:
            raise ValueError("Sprint 20 values are TEST-only")
        if self.payload_sha256 != canonical_sha256(self.payload):
            raise ValueError("versioned payload hash is invalid")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"value_sha256"}))
        if self.value_sha256 != expected:
            raise ValueError("versioned value hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "VersionedValue":
        payload = dict(values)
        payload["payload_sha256"] = canonical_sha256(payload["payload"])
        payload["value_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class AuthorityLease(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    lease_id: str = Field(min_length=1)
    key: str = Field(min_length=1)
    owner_id: str = Field(min_length=1)
    boundary: BoundaryContext
    epoch: int = Field(ge=1)
    acquired_at: datetime
    expires_at: datetime
    lease_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_lease(self) -> "AuthorityLease":
        if self.boundary.execution_context != ExecutionContext.TEST:
            raise ValueError("Sprint 20 leases are TEST-only")
        if self.expires_at <= self.acquired_at:
            raise ValueError("lease expiry must follow acquisition")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"lease_sha256"}))
        if self.lease_sha256 != expected:
            raise ValueError("authority lease hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "AuthorityLease":
        payload = dict(values)
        payload["lease_sha256"] = canonical_sha256(payload)
        return cls(**payload)

    def valid_at(self, now: datetime) -> bool:
        return self.acquired_at <= now < self.expires_at


class WriteIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent_id: str = Field(min_length=1)
    delivery_id: str = Field(min_length=1)
    key: str = Field(min_length=1)
    expected_version: int = Field(ge=0)
    payload: dict[str, object]
    payload_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    boundary: BoundaryContext
    lease_id: str = Field(min_length=1)
    authority_epoch: int = Field(ge=1)
    sequence: int = Field(ge=1)
    created_at: datetime
    intent_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_intent(self) -> "WriteIntent":
        if self.boundary.execution_context != ExecutionContext.TEST:
            raise ValueError("Sprint 20 intents are TEST-only")
        if self.payload_sha256 != canonical_sha256(self.payload):
            raise ValueError("write intent payload hash is invalid")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"intent_sha256"}))
        if self.intent_sha256 != expected:
            raise ValueError("write intent hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "WriteIntent":
        payload = dict(values)
        payload["payload_sha256"] = canonical_sha256(payload["payload"])
        payload["intent_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class DeliveryReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: str = Field(min_length=1)
    delivery_id: str = Field(min_length=1)
    intent_id: str = Field(min_length=1)
    intent_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    state: DeliveryState
    reason_code: str = Field(min_length=1)
    before_version: int = Field(ge=0)
    after_version: int = Field(ge=0)
    effect_sha256: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    recorded_at: datetime
    receipt_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_receipt(self) -> "DeliveryReceipt":
        if self.state == DeliveryState.COMMITTED and self.effect_sha256 is None:
            raise ValueError("committed delivery requires an effect hash")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"receipt_sha256"}))
        if self.receipt_sha256 != expected:
            raise ValueError("delivery receipt hash is invalid")
        return self


class RecoveryReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str
    state: ReconstructionState
    value_sha256: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    intent_hashes: list[str]
    receipt_hashes: list[str]
    unexplained_intent_ids: list[str]
    report_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_report(self) -> "RecoveryReport":
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"report_sha256"}))
        if self.report_sha256 != expected:
            raise ValueError("recovery report hash is invalid")
        return self


class ConcurrencyConflict(RuntimeError):
    pass


FailureHook = Callable[[str, WriteIntent], None]


class ConcurrentStateCoordinator:
    """Thread-safe TEST coordinator with deterministic recovery semantics."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._values: dict[str, VersionedValue] = {}
        self._leases: dict[str, AuthorityLease] = {}
        self._key_leases: dict[str, str] = {}
        self._intents: dict[str, WriteIntent] = {}
        self._delivery_to_intent: dict[str, str] = {}
        self._receipts: dict[str, DeliveryReceipt] = {}
        self._partitioned_keys: set[str] = set()
        self._deferred: dict[str, list[WriteIntent]] = {}
        self._interrupted_after_effect: set[str] = set()

    @property
    def values(self) -> dict[str, VersionedValue]:
        with self._lock:
            return dict(self._values)

    @property
    def receipts(self) -> dict[str, DeliveryReceipt]:
        with self._lock:
            return dict(self._receipts)

    def acquire_lease(self, lease: AuthorityLease, *, now: datetime) -> AuthorityLease:
        with self._lock:
            existing_id = self._key_leases.get(lease.key)
            if existing_id is not None:
                existing = self._leases[existing_id]
                if existing.valid_at(now) and existing.owner_id != lease.owner_id:
                    raise ConcurrencyConflict("split authority lease denied")
                if existing.valid_at(now) and existing.epoch >= lease.epoch:
                    if existing == lease:
                        return existing
                    raise ConcurrencyConflict("stale or competing authority epoch denied")
            self._leases[lease.lease_id] = lease
            self._key_leases[lease.key] = lease.lease_id
            return lease

    def partition(self, key: str) -> None:
        with self._lock:
            self._partitioned_keys.add(key)

    def heal_partition(self, key: str, *, now: datetime) -> list[DeliveryReceipt]:
        with self._lock:
            self._partitioned_keys.discard(key)
            pending = sorted(
                self._deferred.pop(key, []),
                key=lambda item: (item.sequence, item.created_at, item.delivery_id),
            )
            # A DEFERRED receipt documents queuing, not a terminal effect. Remove
            # it before replay so the exact intent resumes instead of being
            # misclassified as a duplicate delivery.
            for intent in pending:
                prior = self._receipts.get(intent.delivery_id)
                if prior is not None and prior.state == DeliveryState.DEFERRED:
                    self._receipts.pop(intent.delivery_id, None)
        return [self.deliver(intent, now=now) for intent in pending]

    def deliver(
        self,
        intent: WriteIntent,
        *,
        now: datetime,
        failure_hook: FailureHook | None = None,
    ) -> DeliveryReceipt:
        with self._lock:
            mapped_intent_id = self._delivery_to_intent.get(intent.delivery_id)
            if mapped_intent_id is not None:
                mapped = self._intents[mapped_intent_id]
                if mapped != intent:
                    return self._make_receipt(
                        intent,
                        state=DeliveryState.CONFLICT,
                        reason="DELIVERY_ID_CONFLICT",
                        before=self._current_version(intent.key),
                        after=self._current_version(intent.key),
                        now=now,
                    )
                prior_receipt = self._receipts.get(intent.delivery_id)
                if prior_receipt is not None:
                    if prior_receipt.state == DeliveryState.INTERRUPTED:
                        return self.recover(intent.delivery_id, now=now)
                    return self._duplicate_receipt(intent, prior_receipt, now=now)

            existing_intent = self._intents.get(intent.intent_id)
            if existing_intent is not None and existing_intent != intent:
                return self._make_receipt(
                    intent,
                    state=DeliveryState.CONFLICT,
                    reason="INTENT_ID_CONFLICT",
                    before=self._current_version(intent.key),
                    after=self._current_version(intent.key),
                    now=now,
                )

            self._intents[intent.intent_id] = intent
            self._delivery_to_intent[intent.delivery_id] = intent.intent_id

            if intent.key in self._partitioned_keys:
                if intent not in self._deferred.setdefault(intent.key, []):
                    self._deferred[intent.key].append(intent)
                receipt = self._make_receipt(
                    intent,
                    state=DeliveryState.DEFERRED,
                    reason="PARTITION_DEFERRED",
                    before=self._current_version(intent.key),
                    after=self._current_version(intent.key),
                    now=now,
                )
                self._receipts[intent.delivery_id] = receipt
                return receipt

            lease = self._leases.get(intent.lease_id)
            if (
                lease is None
                or lease.key != intent.key
                or lease.boundary != intent.boundary
                or lease.epoch != intent.authority_epoch
                or not lease.valid_at(now)
                or self._key_leases.get(intent.key) != lease.lease_id
            ):
                receipt = self._make_receipt(
                    intent,
                    state=DeliveryState.REJECTED,
                    reason="AUTHORITY_LEASE_INVALID",
                    before=self._current_version(intent.key),
                    after=self._current_version(intent.key),
                    now=now,
                )
                self._receipts[intent.delivery_id] = receipt
                return receipt

            before = self._current_version(intent.key)
            if before != intent.expected_version:
                receipt = self._make_receipt(
                    intent,
                    state=DeliveryState.CONFLICT,
                    reason="COMPARE_AND_SWAP_CONFLICT",
                    before=before,
                    after=before,
                    now=now,
                )
                self._receipts[intent.delivery_id] = receipt
                return receipt

            if failure_hook is not None:
                failure_hook("before-effect", intent)

            value = VersionedValue.create(
                key=intent.key,
                version=before + 1,
                payload=intent.payload,
                boundary=intent.boundary,
                authority_epoch=intent.authority_epoch,
                committed_by=intent.intent_id,
            )
            self._values[intent.key] = value

            if failure_hook is not None:
                try:
                    failure_hook("after-effect-before-receipt", intent)
                except Exception:
                    self._interrupted_after_effect.add(intent.delivery_id)
                    interrupted = self._make_receipt(
                        intent,
                        state=DeliveryState.INTERRUPTED,
                        reason="INTERRUPTED_AFTER_EFFECT",
                        before=before,
                        after=value.version,
                        now=now,
                        effect=value.value_sha256,
                    )
                    self._receipts[intent.delivery_id] = interrupted
                    raise

            committed = self._make_receipt(
                intent,
                state=DeliveryState.COMMITTED,
                reason="COMMITTED",
                before=before,
                after=value.version,
                now=now,
                effect=value.value_sha256,
            )
            self._receipts[intent.delivery_id] = committed
            return committed

    def recover(self, delivery_id: str, *, now: datetime) -> DeliveryReceipt:
        with self._lock:
            intent_id = self._delivery_to_intent.get(delivery_id)
            if intent_id is None:
                raise KeyError(delivery_id)
            intent = self._intents[intent_id]
            prior = self._receipts.get(delivery_id)
            value = self._values.get(intent.key)
            if (
                delivery_id in self._interrupted_after_effect
                and prior is not None
                and value is not None
                and value.committed_by == intent.intent_id
                and value.payload_sha256 == intent.payload_sha256
            ):
                recovered = self._make_receipt(
                    intent,
                    state=DeliveryState.COMMITTED,
                    reason="RECOVERED_AFTER_EFFECT",
                    before=prior.before_version,
                    after=value.version,
                    now=now,
                    effect=value.value_sha256,
                )
                self._receipts[delivery_id] = recovered
                self._interrupted_after_effect.discard(delivery_id)
                return recovered
            if prior is not None:
                return prior
            raise ConcurrencyConflict("delivery cannot be reconstructed")

    def reconstruct(self, key: str) -> RecoveryReport:
        with self._lock:
            intents = sorted(
                (item for item in self._intents.values() if item.key == key),
                key=lambda item: (item.sequence, item.intent_id),
            )
            receipts = [
                self._receipts[item.delivery_id]
                for item in intents
                if item.delivery_id in self._receipts
            ]
            unexplained = [
                item.intent_id for item in intents if item.delivery_id not in self._receipts
            ]
            value = self._values.get(key)
            if unexplained:
                state = ReconstructionState.REPAIRABLE
            elif any(item.state == DeliveryState.DEFERRED for item in receipts):
                state = ReconstructionState.PENDING
            elif any(item.state == DeliveryState.CONFLICT for item in receipts):
                state = ReconstructionState.CONFLICT
            else:
                state = ReconstructionState.COMPLETE
            payload = {
                "key": key,
                "state": state,
                "value_sha256": value.value_sha256 if value else None,
                "intent_hashes": [item.intent_sha256 for item in intents],
                "receipt_hashes": [item.receipt_sha256 for item in receipts],
                "unexplained_intent_ids": unexplained,
            }
            return RecoveryReport(**payload, report_sha256=canonical_sha256(payload))

    def _current_version(self, key: str) -> int:
        value = self._values.get(key)
        return value.version if value else 0

    @staticmethod
    def _make_receipt(
        intent: WriteIntent,
        *,
        state: DeliveryState,
        reason: str,
        before: int,
        after: int,
        now: datetime,
        effect: str | None = None,
    ) -> DeliveryReceipt:
        payload = {
            "receipt_id": f"DELIVERY-RCPT-{intent.delivery_id}-{state.value}",
            "delivery_id": intent.delivery_id,
            "intent_id": intent.intent_id,
            "intent_sha256": intent.intent_sha256,
            "state": state,
            "reason_code": reason,
            "before_version": before,
            "after_version": after,
            "effect_sha256": effect,
            "recorded_at": now,
        }
        return DeliveryReceipt(**payload, receipt_sha256=canonical_sha256(payload))

    @classmethod
    def _duplicate_receipt(
        cls,
        intent: WriteIntent,
        prior: DeliveryReceipt,
        *,
        now: datetime,
    ) -> DeliveryReceipt:
        return cls._make_receipt(
            intent,
            state=DeliveryState.DUPLICATE,
            reason="EXACT_DUPLICATE_NO_EFFECT",
            before=prior.after_version,
            after=prior.after_version,
            now=now,
            effect=prior.effect_sha256,
        )
