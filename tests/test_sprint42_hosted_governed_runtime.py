from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from nks.application.governed_transactions import canonical_sha256
from nks.application.hosted_governed_runtime import (
    HostedGovernedExecutionRuntime,
    HostedMutationPolicy,
    HostedMutationRequest,
    HostedRuntimeError,
    HostedRuntimeFailurePoint,
    HostedRuntimeInterruption,
    HostedRuntimeStatus,
    MutationProvenance,
    ProvenanceKind,
)
from nks.application.hosted_identity import (
    HostedBoundaryContext,
    HostedIdentityService,
    TestHostedIdentityAuthority,
)
from nks.application.physical_canonical_persistence import (
    PhysicalConflictError,
    SQLiteCanonicalPersistence,
)
from nks.enki.temporal_authority import TemporalAuthorityEnvelope
from nks.governance.approvals import (
    ApprovalDecision,
    ApprovalGrant,
    ExecutionContext,
)
from nks.governance.boundaries import BoundaryAction, HumanBoundaryPolicy


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "security/enki-hosted-1.0-rc2/hosted-mutation-policy.json"
NOW = datetime(2026, 7, 18, 1, 0, tzinfo=timezone.utc)


def policy() -> HostedMutationPolicy:
    return HostedMutationPolicy(**json.loads(POLICY_PATH.read_text(encoding="utf-8")))


def persistence() -> SQLiteCanonicalPersistence:
    store = SQLiteCanonicalPersistence.memory()
    store.initialize_v1(applied_at=NOW - timedelta(hours=1))
    return store


def signer() -> TestHostedIdentityAuthority:
    return TestHostedIdentityAuthority(
        key_id="TEST-RUNTIME-KEY-1",
        key=b"sprint42-test-only-signing-key",
    )


def context(
    *,
    tenant_id: str = "TENANT-A",
    subject_id: str = "SUBJECT-1",
    domain: str = "operations",
    purpose: str = "reconciliation",
    principal_id: str = "PRINCIPAL-A",
    execution_context: ExecutionContext = ExecutionContext.TEST,
) -> HostedBoundaryContext:
    return HostedBoundaryContext(
        namespace_id="NKS-HOSTED-TEST",
        tenant_id=tenant_id,
        subject_id=subject_id,
        domain=domain,
        audience="internal",
        purpose=purpose,
        principal_id=principal_id,
        execution_context=execution_context,
    )


def envelope(
    record_id: str = "REC-1",
    *,
    subject_id: str = "SUBJECT-1",
    domain: str = "operations",
    marker: str = "alpha",
) -> TemporalAuthorityEnvelope:
    return TemporalAuthorityEnvelope(
        record_id=record_id,
        subject_id=subject_id,
        domain=domain,
        authority_class="GOVERNED",
        content_hash=canonical_sha256({"marker": marker}),
        schema_version="temporal-v1",
        recorded_at=NOW,
        effective_from=NOW,
        authority_valid_from=NOW,
    )


def provenance(record: TemporalAuthorityEnvelope) -> MutationProvenance:
    return MutationProvenance.create(
        provenance_id=f"PROV-{record.record_id}",
        subject_id=record.subject_id,
        content_sha256=record.content_hash,
        kind=ProvenanceKind.SYNTHETIC,
        source_sha256=canonical_sha256({"fixture": record.record_id}),
        lineage_sha256=(),
        execution_context=ExecutionContext.TEST,
    )


def request(
    record: TemporalAuthorityEnvelope | None = None,
    *,
    request_id: str = "REQ-1",
    transaction_id: str = "TX-1",
    request_context: HostedBoundaryContext | None = None,
    selected_policy: HostedMutationPolicy | None = None,
    selected_provenance: MutationProvenance | None = None,
    subject_type: str = "ORGANIZATION",
    human_policy: HumanBoundaryPolicy | None = None,
) -> HostedMutationRequest:
    record = record or envelope()
    selected_policy = selected_policy or policy()
    selected_provenance = selected_provenance or provenance(record)
    return HostedMutationRequest.create(
        request_id=request_id,
        transaction_id=transaction_id,
        context=request_context or context(subject_id=record.subject_id, domain=record.domain),
        envelope=record,
        provenance=selected_provenance,
        policy_sha256=selected_policy.policy_sha256,
        subject_type=subject_type,
        human_policy=human_policy,
        requested_at=NOW,
    )


def credential(identity_authority: TestHostedIdentityAuthority, req: HostedMutationRequest):
    return identity_authority.issue(
        credential_id=f"CRED-{req.request_id}",
        principal_id=req.context.principal_id,
        tenant_id=req.context.tenant_id,
        permitted_subjects=(req.context.subject_id,),
        permitted_domains=(req.context.domain,),
        permitted_audiences=(req.context.audience,),
        permitted_purposes=(req.context.purpose,),
        permitted_actions=(BoundaryAction.WRITE,),
        issued_at=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(hours=1),
    )


def approval(
    req: HostedMutationRequest,
    *,
    approval_id: str = "APPROVAL-1",
    expires_at: datetime | None = None,
    authority_class: str = "HUMAN",
) -> ApprovalGrant:
    return ApprovalGrant(
        approval_id=approval_id,
        decision=ApprovalDecision.APPROVED,
        execution_context=ExecutionContext.TEST,
        permitted_actions={"canonical.write"},
        subject_id=req.envelope.subject_id,
        content_sha256=req.envelope.content_hash,
        authorized_by="sprint42-test-authority",
        authority_class=authority_class,
        issued_at=NOW - timedelta(minutes=10),
        expires_at=expires_at or (NOW + timedelta(hours=1)),
    )


def runtime():
    store = persistence()
    identity_authority = signer()
    service = HostedIdentityService(identity_authority)
    return HostedGovernedExecutionRuntime(store, service), store, identity_authority, service


def test_persisted_policy_is_hash_bound_and_production_disabled():
    selected = policy()

    assert selected.policy_id == "HOSTED-MUTATION-POLICY-enki-hosted-1.0-rc2"
    assert selected.production_execution_authorized is False
    assert selected.policy_sha256 == (
        "sha256:3b35fd1ce81e5dc3c98e49a1a0341cc3818bc83460e38ddfe218fc40600e85b3"
    )
    assert set(selected.allowed_provenance_kinds) == {
        ProvenanceKind.SYNTHETIC,
        ProvenanceKind.REPLAY,
        ProvenanceKind.REAL_TEST,
    }


def test_complete_governed_mutation_path_binds_every_control_and_receipt():
    hosted, store, identity_authority, identity_service = runtime()
    req = request()
    selected_policy = policy()

    receipt = hosted.execute(
        req,
        credential=credential(identity_authority, req),
        approval=approval(req),
        policy=selected_policy,
        now=NOW,
    )
    reconstruction = hosted.reconstruct(req.request_id)
    physical = store.reconstruct(req.context.tenant_id)

    assert reconstruction.status == HostedRuntimeStatus.COMMITTED
    assert reconstruction.request_sha256 == req.request_sha256
    assert reconstruction.provenance_sha256 == req.provenance.provenance_sha256
    assert reconstruction.policy_sha256 == selected_policy.policy_sha256
    assert reconstruction.physical_receipt_sha256 == receipt.physical_receipt_sha256
    assert reconstruction.runtime_receipt_sha256 == receipt.runtime_receipt_sha256
    assert len(physical.timeline) == 1
    assert physical.timeline[0] == req.envelope
    assert len(physical.transaction_ids) == 1
    assert len(physical.reservation_ids) == 1
    assert len(physical.receipt_ids) == 1
    assert len(identity_service.decisions) == 1
    assert receipt.identity_decision_sha256 == identity_service.decisions[0].event_sha256


def test_exact_retry_returns_same_runtime_receipt_without_duplicate_effect_or_consumption():
    hosted, store, identity_authority, _ = runtime()
    req = request()
    cred = credential(identity_authority, req)
    grant = approval(req)
    selected_policy = policy()

    first = hosted.execute(req, credential=cred, approval=grant, policy=selected_policy, now=NOW)
    second = hosted.execute(
        req,
        credential=cred,
        approval=grant,
        policy=selected_policy,
        now=NOW + timedelta(hours=2),
    )

    assert first == second
    assert store.connection.execute(
        "SELECT COUNT(*) AS count FROM canonical_records"
    ).fetchone()["count"] == 1
    assert store.connection.execute(
        "SELECT COUNT(*) AS count FROM hosted_runtime_authority_consumptions"
    ).fetchone()["count"] == 1
    consumption = store.connection.execute(
        "SELECT status FROM hosted_runtime_authority_consumptions"
    ).fetchone()
    assert consumption["status"] == HostedRuntimeStatus.COMMITTED.value


def test_interruption_before_physical_write_retries_to_one_effect():
    hosted, store, identity_authority, _ = runtime()
    req = request()
    cred = credential(identity_authority, req)
    grant = approval(req)

    with pytest.raises(HostedRuntimeInterruption, match="before physical write"):
        hosted.execute(
            req,
            credential=cred,
            approval=grant,
            policy=policy(),
            now=NOW,
            failure_point=HostedRuntimeFailurePoint.BEFORE_PHYSICAL_WRITE,
        )

    assert hosted.reconstruct(req.request_id).status == HostedRuntimeStatus.RESERVED
    assert store.connection.execute(
        "SELECT COUNT(*) AS count FROM canonical_records"
    ).fetchone()["count"] == 0

    recovered = hosted.execute(
        req,
        credential=cred,
        approval=grant,
        policy=policy(),
        now=NOW + timedelta(minutes=1),
    )

    assert hosted.reconstruct(req.request_id).status == HostedRuntimeStatus.COMMITTED
    assert recovered.runtime_receipt_sha256.startswith("sha256:")
    assert store.connection.execute(
        "SELECT COUNT(*) AS count FROM canonical_records"
    ).fetchone()["count"] == 1


def test_interruption_after_physical_commit_recovers_without_replaying_effect():
    hosted, store, identity_authority, _ = runtime()
    req = request()
    cred = credential(identity_authority, req)
    grant = approval(req)

    with pytest.raises(HostedRuntimeInterruption, match="after physical commit"):
        hosted.execute(
            req,
            credential=cred,
            approval=grant,
            policy=policy(),
            now=NOW,
            failure_point=HostedRuntimeFailurePoint.AFTER_PHYSICAL_COMMIT,
        )

    assert store.connection.execute(
        "SELECT COUNT(*) AS count FROM canonical_records"
    ).fetchone()["count"] == 1
    assert hosted.reconstruct(req.request_id).status == HostedRuntimeStatus.RESERVED

    recovered = hosted.execute(
        req,
        credential=cred,
        approval=grant,
        policy=policy(),
        now=NOW + timedelta(hours=2),
    )

    assert hosted.reconstruct(req.request_id).status == HostedRuntimeStatus.COMMITTED
    assert store.connection.execute(
        "SELECT COUNT(*) AS count FROM canonical_records"
    ).fetchone()["count"] == 1
    assert recovered.physical_receipt_sha256.startswith("sha256:")


def test_interruption_after_runtime_commit_is_an_exact_receipt_replay():
    hosted, store, identity_authority, _ = runtime()
    req = request()
    cred = credential(identity_authority, req)
    grant = approval(req)

    with pytest.raises(HostedRuntimeInterruption, match="after runtime commit"):
        hosted.execute(
            req,
            credential=cred,
            approval=grant,
            policy=policy(),
            now=NOW,
            failure_point=HostedRuntimeFailurePoint.AFTER_RUNTIME_COMMIT,
        )

    before = hosted.reconstruct(req.request_id)
    replay = hosted.execute(
        req,
        credential=cred,
        approval=grant,
        policy=policy(),
        now=NOW + timedelta(hours=3),
    )

    assert before.status == HostedRuntimeStatus.COMMITTED
    assert replay.runtime_receipt_sha256 == before.runtime_receipt_sha256
    assert store.connection.execute(
        "SELECT COUNT(*) AS count FROM canonical_records"
    ).fetchone()["count"] == 1


def test_same_approval_cannot_authorize_a_different_transaction_or_request():
    hosted, store, identity_authority, _ = runtime()
    first_req = request()
    grant = approval(first_req)
    hosted.execute(
        first_req,
        credential=credential(identity_authority, first_req),
        approval=grant,
        policy=policy(),
        now=NOW,
    )
    second_record = envelope("REC-2", marker="alpha")
    second_req = request(
        second_record,
        request_id="REQ-2",
        transaction_id="TX-2",
    )

    with pytest.raises(
        HostedRuntimeError,
        match="hosted governed mutation denied",
    ) as caught:
        hosted.execute(
            second_req,
            credential=credential(identity_authority, second_req),
            approval=grant,
            policy=policy(),
            now=NOW,
        )

    assert caught.value.reason_code == "APPROVAL_ALREADY_CONSUMED_BY_OTHER_REQUEST"
    assert store.connection.execute(
        "SELECT COUNT(*) AS count FROM canonical_records"
    ).fetchone()["count"] == 1


def test_expired_approval_denies_before_runtime_reservation_or_physical_effect():
    hosted, store, identity_authority, _ = runtime()
    req = request()

    with pytest.raises(HostedRuntimeError) as caught:
        hosted.execute(
            req,
            credential=credential(identity_authority, req),
            approval=approval(req, expires_at=NOW - timedelta(seconds=1)),
            policy=policy(),
            now=NOW,
        )

    assert caught.value.reason_code == "APPROVAL_DENIED"
    assert store.connection.execute(
        "SELECT COUNT(*) AS count FROM hosted_runtime_requests"
    ).fetchone()["count"] == 0
    assert store.connection.execute(
        "SELECT COUNT(*) AS count FROM canonical_records"
    ).fetchone()["count"] == 0


def test_policy_purpose_and_provenance_fail_closed_before_mutation():
    hosted, store, identity_authority, _ = runtime()
    bad_purpose_req = request(
        request_context=context(purpose="marketing"),
    )

    with pytest.raises(HostedRuntimeError) as purpose_error:
        hosted.execute(
            bad_purpose_req,
            credential=credential(identity_authority, bad_purpose_req),
            approval=approval(bad_purpose_req),
            policy=policy(),
            now=NOW,
        )
    assert purpose_error.value.reason_code == "PURPOSE_NOT_ALLOWED_BY_POLICY"

    replay_only = HostedMutationPolicy.create(
        policy_id="REPLAY-ONLY",
        allowed_purposes=("reconciliation",),
        allowed_provenance_kinds=(ProvenanceKind.REPLAY,),
        acceptable_approval_authority_classes=("HUMAN",),
        production_execution_authorized=False,
    )
    provenance_req = request(selected_policy=replay_only)
    with pytest.raises(HostedRuntimeError) as provenance_error:
        hosted.execute(
            provenance_req,
            credential=credential(identity_authority, provenance_req),
            approval=approval(provenance_req),
            policy=replay_only,
            now=NOW,
        )
    assert provenance_error.value.reason_code == "PROVENANCE_NOT_ALLOWED_BY_POLICY"
    assert store.connection.execute(
        "SELECT COUNT(*) AS count FROM canonical_records"
    ).fetchone()["count"] == 0


def test_cross_tenant_identity_fails_before_authority_consumption():
    hosted, store, identity_authority, _ = runtime()
    req = request(request_context=context(tenant_id="TENANT-B"))
    wrong_credential = identity_authority.issue(
        credential_id="CRED-WRONG-TENANT",
        principal_id=req.context.principal_id,
        tenant_id="TENANT-A",
        permitted_subjects=(req.context.subject_id,),
        permitted_domains=(req.context.domain,),
        permitted_audiences=(req.context.audience,),
        permitted_purposes=(req.context.purpose,),
        permitted_actions=(BoundaryAction.WRITE,),
        issued_at=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(hours=1),
    )

    with pytest.raises(HostedRuntimeError) as caught:
        hosted.execute(
            req,
            credential=wrong_credential,
            approval=approval(req),
            policy=policy(),
            now=NOW,
        )

    assert caught.value.reason_code == "IDENTITY_TENANT_MISMATCH"
    assert store.connection.execute(
        "SELECT COUNT(*) AS count FROM hosted_runtime_authority_consumptions"
    ).fetchone()["count"] == 0


def test_human_state_requires_stricter_policy_before_runtime_mutation():
    hosted, store, identity_authority, _ = runtime()
    person_req = request(subject_type="PERSON", human_policy=None)

    with pytest.raises(HostedRuntimeError) as caught:
        hosted.execute(
            person_req,
            credential=credential(identity_authority, person_req),
            approval=approval(person_req),
            policy=policy(),
            now=NOW,
        )
    assert caught.value.reason_code == "IDENTITY_HUMAN_POLICY_DENIED"
    assert store.connection.execute(
        "SELECT COUNT(*) AS count FROM canonical_records"
    ).fetchone()["count"] == 0

    permitted_req = request(
        request_id="REQ-PERSON-OK",
        transaction_id="TX-PERSON-OK",
        subject_type="PERSON",
        human_policy=HumanBoundaryPolicy(
            consent_granted=True,
            purpose_allowed=True,
        ),
    )
    result = hosted.execute(
        permitted_req,
        credential=credential(identity_authority, permitted_req),
        approval=approval(permitted_req, approval_id="APPROVAL-PERSON-OK"),
        policy=policy(),
        now=NOW,
    )
    assert result.runtime_receipt_sha256.startswith("sha256:")


def test_conflicting_canonical_operation_fails_closed_without_duplicate_current_authority():
    hosted, store, identity_authority, _ = runtime()
    first_req = request()
    hosted.execute(
        first_req,
        credential=credential(identity_authority, first_req),
        approval=approval(first_req),
        policy=policy(),
        now=NOW,
    )
    conflicting_record = envelope("REC-CONFLICT", marker="beta")
    conflicting_req = request(
        conflicting_record,
        request_id="REQ-CONFLICT",
        transaction_id="TX-CONFLICT",
    )

    with pytest.raises(PhysicalConflictError):
        hosted.execute(
            conflicting_req,
            credential=credential(identity_authority, conflicting_req),
            approval=approval(conflicting_req, approval_id="APPROVAL-CONFLICT"),
            policy=policy(),
            now=NOW,
        )

    assert store.current_authority_record_ids("TENANT-A") == ("REC-1",)
    assert len(store.reconstruct("TENANT-A").conflict_ids) == 1
    assert store.connection.execute(
        "SELECT COUNT(*) AS count FROM canonical_records"
    ).fetchone()["count"] == 1


def test_request_model_rejects_context_envelope_or_provenance_mismatch():
    record = envelope()
    selected_policy = policy()

    with pytest.raises(ValidationError, match="request subject"):
        request(
            record,
            request_context=context(subject_id="OTHER-SUBJECT"),
            selected_policy=selected_policy,
        )

    wrong_provenance = MutationProvenance.create(
        provenance_id="PROV-WRONG",
        subject_id=record.subject_id,
        content_sha256=canonical_sha256({"wrong": True}),
        kind=ProvenanceKind.SYNTHETIC,
        source_sha256=canonical_sha256({"source": "wrong"}),
        lineage_sha256=(),
        execution_context=ExecutionContext.TEST,
    )
    with pytest.raises(ValidationError, match="provenance content"):
        request(
            record,
            selected_policy=selected_policy,
            selected_provenance=wrong_provenance,
        )


def test_production_context_request_is_rejected_at_model_boundary():
    record = envelope()
    with pytest.raises(ValidationError, match="TEST-scoped"):
        request(
            record,
            request_context=context(execution_context=ExecutionContext.PRODUCTION),
        )
