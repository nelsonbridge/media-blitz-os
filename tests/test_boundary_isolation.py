from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from nks.adapters.boundary_store import (
    SeparatedLocalBoundaryStore,
    SharedLogicalBoundaryStore,
)
from nks.application.boundary_isolation import (
    BoundaryConflict,
    BoundaryIsolationError,
    BoundaryIsolationService,
    BoundaryPackage,
    BoundaryRecord,
)
from nks.application.boundary_probe import run_local_process_denial_probe
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import (
    BoundaryAction,
    BoundaryAuthorization,
    BoundaryContext,
    HumanBoundaryPolicy,
    TestBoundarySigner,
)


def _now() -> datetime:
    return datetime(2026, 7, 15, 3, 0, tzinfo=timezone.utc)


def _boundary(
    tenant: str = "TENANT-A",
    *,
    subject: str = "SUBJECT-1",
    domain: str = "operations",
    audience: str = "internal",
    context: ExecutionContext = ExecutionContext.TEST,
) -> BoundaryContext:
    return BoundaryContext(
        namespace_id="NKS-TEST",
        tenant_id=tenant,
        subject_id=subject,
        domain=domain,
        audience=audience,
        execution_context=context,
    )


def _authorization(
    boundary: BoundaryContext,
    *,
    actions: set[BoundaryAction] | None = None,
) -> BoundaryAuthorization:
    return BoundaryAuthorization(
        authorization_id=f"AUTH-{boundary.tenant_id}-{boundary.subject_id}",
        boundary=boundary,
        permitted_actions=actions or set(BoundaryAction),
        authority_class="TEST-HARNESS",
        issued_at=_now() - timedelta(minutes=1),
        expires_at=_now() + timedelta(hours=1),
    )


def _record(
    boundary: BoundaryContext,
    *,
    record_id: str = "REC-1",
    subject_type: str = "ORGANIZATION",
    marker: str = "synthetic-a",
) -> BoundaryRecord:
    return BoundaryRecord.create(
        record_id=record_id,
        subject_type=subject_type,
        boundary=boundary,
        payload={"classification": "SYNTHETIC/TEST", "marker": marker},
    )


@pytest.mark.parametrize("store_type", [SharedLogicalBoundaryStore, SeparatedLocalBoundaryStore])
def test_test_data_round_trip_succeeds_in_both_zero_cost_stores(tmp_path, store_type) -> None:
    boundary = _boundary()
    service = BoundaryIsolationService(store_type(tmp_path))
    record = _record(boundary)
    authorization = _authorization(boundary)

    assert service.write(record, authorization=authorization, now=_now()) == record
    assert (
        service.read(
            boundary=boundary,
            record_id=record.record_id,
            authorization=authorization,
            now=_now(),
        )
        == record
    )
    assert service.count(boundary) == 1


@pytest.mark.parametrize("store_type", [SharedLogicalBoundaryStore, SeparatedLocalBoundaryStore])
def test_same_record_id_is_isolated_between_tenants(tmp_path, store_type) -> None:
    service = BoundaryIsolationService(store_type(tmp_path))
    first = _record(_boundary("TENANT-A"), marker="tenant-a")
    second = _record(_boundary("TENANT-B"), marker="tenant-b")

    service.write(first, authorization=_authorization(first.boundary), now=_now())
    service.write(second, authorization=_authorization(second.boundary), now=_now())

    assert service.count(first.boundary) == 1
    assert service.count(second.boundary) == 1
    assert service.read(
        boundary=first.boundary,
        record_id="REC-1",
        authorization=_authorization(first.boundary),
        now=_now(),
    ).payload["marker"] == "tenant-a"
    assert service.read(
        boundary=second.boundary,
        record_id="REC-1",
        authorization=_authorization(second.boundary),
        now=_now(),
    ).payload["marker"] == "tenant-b"


@pytest.mark.parametrize(
    "requested",
    [
        _boundary("TENANT-B"),
        _boundary(subject="SUBJECT-2"),
        _boundary(domain="finance"),
        _boundary(audience="public"),
    ],
)
def test_complete_boundary_mismatch_fails_closed(tmp_path, requested: BoundaryContext) -> None:
    authorized_boundary = _boundary()
    service = BoundaryIsolationService(SharedLogicalBoundaryStore(tmp_path))
    with pytest.raises(BoundaryIsolationError) as caught:
        service.read(
            boundary=requested,
            record_id="REC-1",
            authorization=_authorization(authorized_boundary),
            now=_now(),
        )
    assert caught.value.reason_code == "BOUNDARY_MISMATCH"
    assert str(caught.value) == "boundary operation denied"


def test_test_proof_cannot_authorize_production_context(tmp_path) -> None:
    production = _boundary(context=ExecutionContext.PRODUCTION)
    service = BoundaryIsolationService(SharedLogicalBoundaryStore(tmp_path))
    with pytest.raises(BoundaryIsolationError) as caught:
        service.write(
            _record(production),
            authorization=_authorization(production),
            now=_now(),
        )
    assert caught.value.reason_code == "TEST_PROOF_CANNOT_AUTHORIZE_PRODUCTION"


def test_export_import_replay_and_recovery_preserve_exact_boundary(tmp_path) -> None:
    boundary = _boundary()
    authorization = _authorization(boundary)
    source = BoundaryIsolationService(SharedLogicalBoundaryStore(tmp_path / "source"))
    target = BoundaryIsolationService(SeparatedLocalBoundaryStore(tmp_path / "target"))
    record = _record(boundary)
    source.write(record, authorization=authorization, now=_now())
    package = source.export(
        boundary=boundary,
        record_id=record.record_id,
        authorization=authorization,
        now=_now(),
    )

    assert target.import_package(
        package,
        target_boundary=boundary,
        authorization=authorization,
        now=_now(),
    ) == record
    assert target.replay(
        package,
        expected_boundary=boundary,
        authorization=authorization,
        now=_now(),
    ) == record
    assert target.recover(
        package,
        expected_boundary=boundary,
        authorization=authorization,
        now=_now(),
    ) == record
    assert target.count(boundary) == 1


def test_recovery_into_another_tenant_is_denied(tmp_path) -> None:
    source_boundary = _boundary("TENANT-A")
    target_boundary = _boundary("TENANT-B")
    record = _record(source_boundary)
    package = BoundaryPackage.create(record)
    service = BoundaryIsolationService(SeparatedLocalBoundaryStore(tmp_path))

    with pytest.raises(BoundaryIsolationError) as caught:
        service.recover(
            package,
            expected_boundary=target_boundary,
            authorization=_authorization(target_boundary),
            now=_now(),
        )
    assert caught.value.reason_code == "PACKAGE_BOUNDARY_MISMATCH"
    assert service.count(target_boundary) == 0


def test_exact_duplicate_is_idempotent_and_divergent_duplicate_fails(tmp_path) -> None:
    boundary = _boundary()
    authorization = _authorization(boundary)
    service = BoundaryIsolationService(SharedLogicalBoundaryStore(tmp_path))
    original = _record(boundary)
    service.write(original, authorization=authorization, now=_now())
    assert service.write(original, authorization=authorization, now=_now()) == original
    assert service.count(boundary) == 1

    with pytest.raises(BoundaryConflict):
        service.write(
            _record(boundary, marker="conflicting-payload"),
            authorization=authorization,
            now=_now(),
        )
    assert service.count(boundary) == 1


def test_hash_tampering_and_path_traversal_are_rejected() -> None:
    record = _record(_boundary())
    with pytest.raises(ValidationError, match="record hash is invalid"):
        record.model_copy(update={"record_sha256": "sha256:" + "0" * 64}).model_validate(
            record.model_copy(update={"record_sha256": "sha256:" + "0" * 64})
        )

    package = BoundaryPackage.create(record)
    with pytest.raises(ValidationError, match="package hash is invalid"):
        BoundaryPackage.model_validate(
            package.model_dump(mode="python") | {"package_sha256": "sha256:" + "0" * 64}
        )

    with pytest.raises(ValidationError):
        _boundary("../TENANT-B")
    with pytest.raises(ValidationError):
        _record(_boundary(), record_id="../REC-1")


def test_forged_envelope_and_wrong_tenant_key_are_rejected() -> None:
    signer = TestBoundarySigner({"TENANT-A": b"test-key-a", "TENANT-B": b"test-key-b"})
    record = _record(_boundary("TENANT-A"))
    envelope = signer.sign(record.boundary, record.payload_sha256)
    assert signer.verify(envelope)

    forged = envelope.model_copy(update={"boundary": _boundary("TENANT-B")})
    assert not signer.verify(forged)


def test_human_protection_remains_stricter_than_tenant_authorization(tmp_path) -> None:
    boundary = _boundary()
    record = _record(boundary, subject_type="PERSON")
    service = BoundaryIsolationService(SharedLogicalBoundaryStore(tmp_path))
    authorization = _authorization(boundary)

    with pytest.raises(BoundaryIsolationError) as caught:
        service.write(record, authorization=authorization, now=_now())
    assert caught.value.reason_code == "HUMAN_POLICY_DENIED"

    policy = HumanBoundaryPolicy(consent_granted=True, purpose_allowed=True)
    assert service.write(
        record,
        authorization=authorization,
        human_policy=policy,
        now=_now(),
    ) == record

    revoked = HumanBoundaryPolicy(
        consent_granted=True,
        purpose_allowed=True,
        revoked=True,
    )
    with pytest.raises(BoundaryIsolationError, match="boundary operation denied"):
        service.read(
            boundary=boundary,
            record_id=record.record_id,
            authorization=authorization,
            human_policy=revoked,
            now=_now(),
        )


def test_diagnostics_are_reconstructable_without_protected_content(tmp_path) -> None:
    authorized = _boundary("TENANT-A")
    requested = _boundary("TENANT-B")
    service = BoundaryIsolationService(SharedLogicalBoundaryStore(tmp_path))

    with pytest.raises(BoundaryIsolationError):
        service.read(
            boundary=requested,
            record_id="SECRET-RECORD-NAME",
            authorization=_authorization(authorized),
            now=_now(),
        )

    serialized = "\n".join(event.model_dump_json() for event in service.audit_events)
    assert "TENANT-A" not in serialized
    assert "TENANT-B" not in serialized
    assert "SECRET-RECORD-NAME" not in serialized
    assert "BOUNDARY_MISMATCH" in serialized


def test_cross_tenant_request_is_denied_in_a_distinct_local_process(tmp_path) -> None:
    result = run_local_process_denial_probe(tmp_path)
    assert result.returncode == 0, result.stderr or result.stdout
