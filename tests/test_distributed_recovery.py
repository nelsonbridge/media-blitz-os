from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from nks.application.distributed_recovery import (
    AuthorityLease,
    ConcurrencyConflict,
    ConcurrentStateCoordinator,
    DeliveryState,
    ReconstructionState,
    WriteIntent,
)
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryContext


def _now() -> datetime:
    return datetime(2026, 7, 15, 7, 0, tzinfo=timezone.utc)


def _boundary(tenant: str = "TENANT-A") -> BoundaryContext:
    return BoundaryContext(
        namespace_id="NKS-TEST",
        tenant_id=tenant,
        subject_id="SUBJECT-1",
        domain="operations",
        audience="internal",
        execution_context=ExecutionContext.TEST,
    )


def _lease(
    *,
    lease_id: str = "LEASE-1",
    owner: str = "WRITER-1",
    epoch: int = 1,
    key: str = "KEY-1",
) -> AuthorityLease:
    return AuthorityLease.create(
        lease_id=lease_id,
        key=key,
        owner_id=owner,
        boundary=_boundary(),
        epoch=epoch,
        acquired_at=_now() - timedelta(minutes=1),
        expires_at=_now() + timedelta(hours=1),
    )


def _intent(
    index: int,
    *,
    expected_version: int = 0,
    lease_id: str = "LEASE-1",
    epoch: int = 1,
    key: str = "KEY-1",
    delivery_id: str | None = None,
    intent_id: str | None = None,
    sequence: int | None = None,
    marker: str | None = None,
) -> WriteIntent:
    return WriteIntent.create(
        intent_id=intent_id or f"INTENT-{index}",
        delivery_id=delivery_id or f"DELIVERY-{index}",
        key=key,
        expected_version=expected_version,
        payload={"classification": "SYNTHETIC/TEST", "marker": marker or f"value-{index}"},
        boundary=_boundary(),
        lease_id=lease_id,
        authority_epoch=epoch,
        sequence=sequence or index,
        created_at=_now() + timedelta(seconds=index),
    )


def test_concurrent_competing_compare_and_swap_writes_produce_one_effect() -> None:
    coordinator = ConcurrentStateCoordinator()
    coordinator.acquire_lease(_lease(), now=_now())
    intents = [_intent(index) for index in range(1, 33)]

    with ThreadPoolExecutor(max_workers=16) as pool:
        receipts = list(pool.map(lambda intent: coordinator.deliver(intent, now=_now()), intents))

    assert sum(item.state == DeliveryState.COMMITTED for item in receipts) == 1
    assert sum(item.state == DeliveryState.CONFLICT for item in receipts) == 31
    assert coordinator.values["KEY-1"].version == 1
    assert len({item.effect_sha256 for item in receipts if item.effect_sha256}) == 1
    assert len(coordinator.receipts) == 32


def test_competing_authority_lease_is_denied_without_split_authority() -> None:
    coordinator = ConcurrentStateCoordinator()
    first = coordinator.acquire_lease(_lease(), now=_now())
    assert first.owner_id == "WRITER-1"

    with pytest.raises(ConcurrencyConflict, match="split authority"):
        coordinator.acquire_lease(
            _lease(lease_id="LEASE-2", owner="WRITER-2", epoch=2),
            now=_now(),
        )

    assert coordinator.acquire_lease(first, now=_now()) == first


def test_expired_or_wrong_epoch_lease_rejects_write() -> None:
    coordinator = ConcurrentStateCoordinator()
    expired = AuthorityLease.create(
        lease_id="LEASE-X",
        key="KEY-1",
        owner_id="WRITER-X",
        boundary=_boundary(),
        epoch=1,
        acquired_at=_now() - timedelta(hours=2),
        expires_at=_now() - timedelta(hours=1),
    )
    coordinator.acquire_lease(expired, now=_now())
    receipt = coordinator.deliver(
        _intent(1, lease_id="LEASE-X"),
        now=_now(),
    )
    assert receipt.state == DeliveryState.REJECTED
    assert receipt.reason_code == "AUTHORITY_LEASE_INVALID"


def test_exact_duplicate_delivery_is_idempotent_and_conflicting_delivery_is_receipted() -> None:
    coordinator = ConcurrentStateCoordinator()
    coordinator.acquire_lease(_lease(), now=_now())
    intent = _intent(1)
    committed = coordinator.deliver(intent, now=_now())
    duplicate = coordinator.deliver(intent, now=_now() + timedelta(seconds=1))

    assert committed.state == DeliveryState.COMMITTED
    assert duplicate.state == DeliveryState.DUPLICATE
    assert duplicate.after_version == committed.after_version == 1
    assert coordinator.values["KEY-1"].version == 1

    conflict = coordinator.deliver(
        _intent(
            2,
            delivery_id=intent.delivery_id,
            intent_id="INTENT-CONFLICT",
            marker="different",
        ),
        now=_now() + timedelta(seconds=2),
    )
    assert conflict.state == DeliveryState.CONFLICT
    assert conflict.reason_code == "DELIVERY_ID_CONFLICT"
    assert coordinator.values["KEY-1"].version == 1


def test_out_of_order_partition_delivery_is_deferred_then_deterministically_resolved() -> None:
    coordinator = ConcurrentStateCoordinator()
    coordinator.acquire_lease(_lease(), now=_now())
    coordinator.partition("KEY-1")
    later = _intent(2, expected_version=1, sequence=2)
    earlier = _intent(1, expected_version=0, sequence=1)

    assert coordinator.deliver(later, now=_now()).state == DeliveryState.DEFERRED
    assert coordinator.deliver(earlier, now=_now()).state == DeliveryState.DEFERRED
    assert "KEY-1" not in coordinator.values
    assert coordinator.reconstruct("KEY-1").state == ReconstructionState.PENDING

    healed = coordinator.heal_partition("KEY-1", now=_now() + timedelta(minutes=1))
    assert [item.state for item in healed] == [
        DeliveryState.COMMITTED,
        DeliveryState.COMMITTED,
    ]
    assert coordinator.values["KEY-1"].version == 2
    assert coordinator.values["KEY-1"].payload["marker"] == "value-2"
    assert coordinator.reconstruct("KEY-1").state == ReconstructionState.COMPLETE


def test_partition_with_competing_same_version_writes_records_one_commit_and_one_conflict() -> None:
    coordinator = ConcurrentStateCoordinator()
    coordinator.acquire_lease(_lease(), now=_now())
    coordinator.partition("KEY-1")
    coordinator.deliver(_intent(2, sequence=2), now=_now())
    coordinator.deliver(_intent(1, sequence=1), now=_now())

    healed = coordinator.heal_partition("KEY-1", now=_now() + timedelta(minutes=1))
    assert [item.state for item in healed] == [
        DeliveryState.COMMITTED,
        DeliveryState.CONFLICT,
    ]
    report = coordinator.reconstruct("KEY-1")
    assert report.state == ReconstructionState.CONFLICT
    assert report.unexplained_intent_ids == []


def test_interruption_after_effect_recovers_one_receipt_without_duplicate_effect() -> None:
    coordinator = ConcurrentStateCoordinator()
    coordinator.acquire_lease(_lease(), now=_now())
    intent = _intent(1)

    def fail(boundary: str, current: WriteIntent) -> None:
        if boundary == "after-effect-before-receipt":
            raise OSError("synthetic adapter interruption")

    with pytest.raises(OSError, match="adapter interruption"):
        coordinator.deliver(intent, now=_now(), failure_hook=fail)

    assert coordinator.values["KEY-1"].version == 1
    assert coordinator.receipts[intent.delivery_id].state == DeliveryState.INTERRUPTED

    recovered = coordinator.recover(intent.delivery_id, now=_now() + timedelta(seconds=1))
    assert recovered.state == DeliveryState.COMMITTED
    assert recovered.reason_code == "RECOVERED_AFTER_EFFECT"
    assert coordinator.values["KEY-1"].version == 1
    assert coordinator.reconstruct("KEY-1").state == ReconstructionState.COMPLETE


def test_missing_receipt_is_identified_as_repairable_not_silently_complete() -> None:
    coordinator = ConcurrentStateCoordinator()
    intent = _intent(1)
    coordinator._intents[intent.intent_id] = intent  # deliberate forensic fixture
    coordinator._delivery_to_intent[intent.delivery_id] = intent.intent_id

    report = coordinator.reconstruct("KEY-1")
    assert report.state == ReconstructionState.REPAIRABLE
    assert report.unexplained_intent_ids == [intent.intent_id]


def test_hash_tampering_and_production_context_fail_closed() -> None:
    intent = _intent(1)
    with pytest.raises(ValidationError, match="intent hash is invalid"):
        WriteIntent.model_validate(
            intent.model_dump(mode="python") | {"intent_sha256": "sha256:" + "0" * 64}
        )

    production = BoundaryContext(
        namespace_id="NKS-PROD",
        tenant_id="TENANT-A",
        subject_id="SUBJECT-1",
        domain="operations",
        audience="internal",
        execution_context=ExecutionContext.PRODUCTION,
    )
    payload = intent.model_dump(mode="python")
    payload["boundary"] = production
    with pytest.raises(ValidationError, match="TEST-only"):
        WriteIntent.model_validate(payload)
