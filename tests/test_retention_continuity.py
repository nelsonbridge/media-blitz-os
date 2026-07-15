from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from nks.adapters.retention_continuity import JsonRetentionRepository, RetentionRecordConflict
from nks.application.retention_continuity import (
    LifecycleAction,
    LifecycleAuthorization,
    LifecycleConflict,
    LifecycleState,
    RetainedRecord,
    RetentionLifecycleService,
    RetentionPolicy,
    create_continuity_proof,
    verify_continuity_proof,
)
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryContext


def _now() -> datetime:
    return datetime(2026, 7, 15, 6, 0, tzinfo=timezone.utc)


def _boundary(tenant: str = "TENANT-A") -> BoundaryContext:
    return BoundaryContext(
        namespace_id="NKS-TEST",
        tenant_id=tenant,
        subject_id="SUBJECT-1",
        domain="knowledge",
        audience="internal",
        execution_context=ExecutionContext.TEST,
    )


def _policy(
    *,
    actions: set[LifecycleAction] | None = None,
    archive_after: datetime | None = None,
    retain_until: datetime | None = None,
) -> RetentionPolicy:
    return RetentionPolicy.create(
        policy_id="RET-POL-1",
        version=1,
        boundary=_boundary(),
        purpose="continuity-test",
        authority_class="RETENTION-GOVERNOR",
        authored_by="TEST-GOVERNOR",
        authored_at=_now() - timedelta(days=30),
        retain_until=retain_until,
        archive_after=archive_after,
        permitted_actions=actions or set(LifecycleAction),
    )


def _record() -> RetainedRecord:
    return RetainedRecord.create(
        record_id="REC-1",
        boundary=_boundary(),
        purpose="continuity-test",
        payload={
            "classification": "SYNTHETIC/TEST",
            "statement": "synthetic governed knowledge",
            "sensitive_detail": "remove-on-redaction",
        },
        created_at=_now() - timedelta(days=20),
        authority_id="SOURCE-AUTH-1",
        lineage_hashes=["sha256:" + "1" * 64],
    )


def _authorization(
    record: RetainedRecord,
    policy: RetentionPolicy,
    action: LifecycleAction,
    *,
    boundary_sha256: str | None = None,
) -> LifecycleAuthorization:
    return LifecycleAuthorization(
        authorization_id=f"AUTH-{action.value}",
        policy_sha256=policy.policy_sha256,
        boundary_sha256=boundary_sha256 or record.boundary.boundary_sha256,
        record_sha256=record.record_sha256,
        action=action,
        authority_class=policy.authority_class,
        purpose=policy.purpose,
        issued_at=_now() - timedelta(minutes=1),
        expires_at=_now() + timedelta(hours=1),
    )


def _apply(service, record, policy, action, transaction_id, **kwargs):
    return service.apply(
        record=record,
        policy=policy,
        authorization=_authorization(record, policy, action),
        action=action,
        transaction_id=transaction_id,
        now=_now(),
        reason_code=f"TEST_{action.value}",
        **kwargs,
    )


def test_policy_is_versioned_purpose_authority_and_hash_bound() -> None:
    policy = _policy()
    assert policy.version == 1
    assert policy.purpose == "continuity-test"
    assert policy.authority_class == "RETENTION-GOVERNOR"
    assert policy.policy_sha256.startswith("sha256:")

    with pytest.raises(ValidationError, match="policy hash is invalid"):
        RetentionPolicy.model_validate(
            policy.model_dump(mode="python") | {"policy_sha256": "sha256:" + "0" * 64}
        )


def test_archival_preserves_original_hash_lineage_context_and_receipt(tmp_path) -> None:
    repository = JsonRetentionRepository(tmp_path)
    service = RetentionLifecycleService(repository)
    record = _record()
    policy = _policy(archive_after=_now() - timedelta(days=1))

    receipt = _apply(service, record, policy, LifecycleAction.ARCHIVE, "TX-ARCHIVE")
    lifecycle = repository.list_lifecycle(record.record_id)[0]

    assert lifecycle.state == LifecycleState.ARCHIVED
    assert lifecycle.original_record_sha256 == record.record_sha256
    assert lifecycle.boundary == record.boundary
    assert receipt.after_sha256 == lifecycle.lifecycle_sha256
    assert receipt.before_sha256 == record.record_sha256
    assert repository.get_record(record.record_id) == record
    assert not service.may_control_downstream(
        record.record_id,
        now=_now(),
        authorized_boundary=record.boundary,
    )


def test_restriction_redaction_tombstone_expiration_and_revocation_block_control(tmp_path) -> None:
    for action in (
        LifecycleAction.RESTRICT,
        LifecycleAction.REDACT,
        LifecycleAction.TOMBSTONE,
        LifecycleAction.EXPIRE,
        LifecycleAction.REVOKE,
    ):
        root = tmp_path / action.value.lower()
        repository = JsonRetentionRepository(root)
        service = RetentionLifecycleService(repository)
        record = _record()
        policy = _policy(retain_until=_now() - timedelta(days=1))
        kwargs = (
            {"redacted_payload": {"classification": "SYNTHETIC/TEST", "statement": "[REDACTED]"}}
            if action == LifecycleAction.REDACT
            else {}
        )
        _apply(service, record, policy, action, f"TX-{action.value}", **kwargs)
        assert not service.may_control_downstream(
            record.record_id,
            now=_now(),
            authorized_boundary=record.boundary,
        )
        lifecycle = repository.list_lifecycle(record.record_id)[0]
        assert lifecycle.original_record_sha256 == record.record_sha256
        if action == LifecycleAction.REDACT:
            assert lifecycle.redacted_payload is not None
            assert "sensitive_detail" not in lifecycle.redacted_payload
            assert repository.get_record(record.record_id) == record


def test_restore_is_limited_to_archived_or_restricted_records(tmp_path) -> None:
    repository = JsonRetentionRepository(tmp_path)
    service = RetentionLifecycleService(repository)
    record = _record()
    policy = _policy(archive_after=_now() - timedelta(days=1))

    _apply(service, record, policy, LifecycleAction.ARCHIVE, "TX-A")
    _apply(service, record, policy, LifecycleAction.RESTORE, "TX-R")
    assert service.current_state(record.record_id, now=_now()) == LifecycleState.ACTIVE
    assert service.may_control_downstream(
        record.record_id,
        now=_now(),
        authorized_boundary=record.boundary,
    )

    with pytest.raises(LifecycleConflict, match="only archived or restricted"):
        _apply(service, record, policy, LifecycleAction.RESTORE, "TX-R2")


def test_terminal_tombstone_or_revocation_cannot_be_rewritten(tmp_path) -> None:
    for action in (LifecycleAction.TOMBSTONE, LifecycleAction.REVOKE):
        repository = JsonRetentionRepository(tmp_path / action.value)
        service = RetentionLifecycleService(repository)
        record = _record()
        policy = _policy()
        _apply(service, record, policy, action, f"TX-{action.value}")
        with pytest.raises(LifecycleConflict, match="terminal lifecycle state"):
            _apply(service, record, policy, LifecycleAction.RESTORE, f"TX-{action.value}-R")


def test_authority_policy_purpose_boundary_timing_and_action_fail_closed(tmp_path) -> None:
    repository = JsonRetentionRepository(tmp_path)
    service = RetentionLifecycleService(repository)
    record = _record()
    policy = _policy(
        actions={LifecycleAction.ARCHIVE},
        archive_after=_now() + timedelta(days=1),
    )

    with pytest.raises(LifecycleConflict, match="premature"):
        _apply(service, record, policy, LifecycleAction.ARCHIVE, "TX-EARLY")

    with pytest.raises(LifecycleConflict, match="not permitted"):
        service.apply(
            record=record,
            policy=policy,
            authorization=_authorization(record, policy, LifecycleAction.REDACT),
            action=LifecycleAction.REDACT,
            transaction_id="TX-NOT-PERMITTED",
            now=_now(),
            reason_code="TEST",
            redacted_payload={"statement": "[REDACTED]"},
        )

    wrong_boundary = _boundary("TENANT-B").boundary_sha256
    with pytest.raises(LifecycleConflict, match="boundary mismatch"):
        service.apply(
            record=record,
            policy=policy,
            authorization=_authorization(
                record,
                policy,
                LifecycleAction.ARCHIVE,
                boundary_sha256=wrong_boundary,
            ),
            action=LifecycleAction.ARCHIVE,
            transaction_id="TX-WRONG-BOUNDARY",
            now=_now() + timedelta(days=2),
            reason_code="TEST",
        )


def test_exact_retry_returns_one_receipt_and_one_lifecycle_effect(tmp_path) -> None:
    repository = JsonRetentionRepository(tmp_path)
    service = RetentionLifecycleService(repository)
    record = _record()
    policy = _policy(archive_after=_now() - timedelta(days=1))
    authorization = _authorization(record, policy, LifecycleAction.ARCHIVE)
    arguments = dict(
        record=record,
        policy=policy,
        authorization=authorization,
        action=LifecycleAction.ARCHIVE,
        transaction_id="TX-RETRY",
        now=_now(),
        reason_code="TEST_ARCHIVE",
    )
    first = service.apply(**arguments)
    second = service.apply(**arguments)
    assert second == first
    assert len(repository.list_lifecycle(record.record_id)) == 1


def test_hash_algorithm_migration_preserves_old_and_new_verification(tmp_path) -> None:
    repository = JsonRetentionRepository(tmp_path)
    record = _record()
    payload_bytes = json.dumps(record.payload, sort_keys=True).encode("utf-8")
    proof = create_continuity_proof(
        record=record,
        payload_bytes=payload_bytes,
        old_algorithm="sha256",
        new_algorithm="sha3_256",
        authority_id="CRYPTO-GOVERNOR",
        transaction_id="TX-HASH-MIG",
        now=_now(),
    )
    repository.append_continuity_proof(proof)

    assert proof.old_digest != proof.new_digest
    assert verify_continuity_proof(proof, payload_bytes=payload_bytes)
    assert not verify_continuity_proof(proof, payload_bytes=payload_bytes + b"tamper")
    assert proof.record_sha256 == record.record_sha256

    with pytest.raises(ValueError, match="unsupported"):
        create_continuity_proof(
            record=record,
            payload_bytes=payload_bytes,
            old_algorithm="md5",
            new_algorithm="sha256",
            authority_id="CRYPTO-GOVERNOR",
            transaction_id="TX-BAD-HASH",
            now=_now(),
        )


def test_append_only_repository_rejects_divergent_record_identity(tmp_path) -> None:
    repository = JsonRetentionRepository(tmp_path)
    record = _record()
    repository.append_record(record)
    repository.append_record(record)
    path = next((tmp_path / "records" / "retained-records").glob("*.json"))
    path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(RetentionRecordConflict):
        repository.append_record(record)
