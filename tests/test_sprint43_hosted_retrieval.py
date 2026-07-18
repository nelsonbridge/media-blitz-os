from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from nks.application.governed_transactions import canonical_sha256
from nks.application.hosted_identity import (
    HostedBoundaryContext,
    HostedIdentityService,
    TestHostedIdentityAuthority,
)
from nks.application.hosted_retrieval import (
    HostedCatalogEntry,
    HostedKnowledgeCatalog,
    HostedModelGatewayHandoff,
    HostedRetrievalError,
    HostedRetrievalRequest,
    HostedRetrievalService,
    HostedRetrievalView,
    build_model_gateway_handoff,
)
from nks.application.physical_canonical_persistence import (
    PhysicalMutationAuthorization,
    SQLiteCanonicalPersistence,
)
from nks.enki.governed_retrieval import (
    PrivacyClass,
    RetrievalMode,
    StaleKnowledgeStateError,
)
from nks.enki.model_gateway import (
    DeterministicNoEffectModelProvider,
    ModelGatewayReplayStore,
    execute_model_gateway,
)
from nks.enki.temporal_authority import (
    TemporalAuthorityDisposition,
    TemporalAuthorityEnvelope,
)
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryAction, HumanBoundaryPolicy


T0 = datetime(2026, 7, 18, 0, 0, tzinfo=timezone.utc)
T1 = T0 + timedelta(hours=1)
T2 = T1 + timedelta(hours=1)


def persistence() -> SQLiteCanonicalPersistence:
    store = SQLiteCanonicalPersistence.memory()
    store.initialize_v1(applied_at=T0 - timedelta(hours=1))
    return store


def envelope(
    record_id: str,
    content: str,
    *,
    subject_id: str = "SUBJECT-1",
    domain: str = "career",
    authority_class: str | None = None,
    disposition: TemporalAuthorityDisposition = TemporalAuthorityDisposition.ACTIVE,
    recorded_at: datetime = T0,
    effective_from: datetime = T0,
    authority_valid_from: datetime = T0,
    authority_valid_to: datetime | None = None,
    superseded_at: datetime | None = None,
    supersedes_record_id: str | None = None,
) -> TemporalAuthorityEnvelope:
    return TemporalAuthorityEnvelope(
        record_id=record_id,
        subject_id=subject_id,
        domain=domain,
        authority_class=authority_class or f"AUTH-{record_id}",
        content_hash=canonical_sha256(content),
        schema_version="temporal-v1",
        recorded_at=recorded_at,
        effective_from=effective_from,
        authority_valid_from=authority_valid_from,
        authority_valid_to=authority_valid_to,
        superseded_at=superseded_at,
        supersedes_record_id=supersedes_record_id,
        disposition=disposition,
    )


def persist(
    store: SQLiteCanonicalPersistence,
    tenant_id: str,
    record: TemporalAuthorityEnvelope,
    *,
    transaction_id: str,
) -> None:
    store.write_canonical(
        tenant_id,
        record,
        authorization=PhysicalMutationAuthorization(
            authorization_id=f"AUTHZ-{tenant_id}-{record.record_id}",
            tenant_id=tenant_id,
            record_id=record.record_id,
            content_hash=record.content_hash,
            issued_at=T0 - timedelta(minutes=1),
            expires_at=T2 + timedelta(hours=1),
        ),
        transaction_id=transaction_id,
        now=T2,
    )


def catalog_entry(
    tenant_id: str,
    record_id: str,
    content: str,
    *,
    audiences: tuple[str, ...] = ("assistant",),
    purposes: tuple[str, ...] = ("career-assistance",),
    privacy: PrivacyClass = PrivacyClass.INTERNAL,
    provenance_ids: tuple[str, ...] | None = None,
) -> HostedCatalogEntry:
    return HostedCatalogEntry.create(
        tenant_id=tenant_id,
        record_id=record_id,
        content=content,
        allowed_audiences=audiences,
        allowed_purposes=purposes,
        privacy_class=privacy,
        provenance_ids=provenance_ids or (f"PROV-{record_id}",),
    )


def identity_authority() -> TestHostedIdentityAuthority:
    return TestHostedIdentityAuthority(
        key_id="TEST-RETRIEVAL-KEY-1",
        key=b"sprint43-test-only-key",
    )


def context(
    *,
    tenant_id: str = "TENANT-A",
    subject_id: str = "SUBJECT-1",
    domain: str = "career",
    audience: str = "assistant",
    purpose: str = "career-assistance",
    principal_id: str = "PRINCIPAL-A",
) -> HostedBoundaryContext:
    return HostedBoundaryContext(
        namespace_id="NKS-HOSTED-TEST",
        tenant_id=tenant_id,
        subject_id=subject_id,
        domain=domain,
        audience=audience,
        purpose=purpose,
        principal_id=principal_id,
        execution_context=ExecutionContext.TEST,
    )


def credential(authority: TestHostedIdentityAuthority, ctx: HostedBoundaryContext):
    return authority.issue(
        credential_id=f"CRED-{ctx.tenant_id}-{ctx.subject_id}",
        principal_id=ctx.principal_id,
        tenant_id=ctx.tenant_id,
        permitted_subjects=(ctx.subject_id,),
        permitted_domains=(ctx.domain,),
        permitted_audiences=(ctx.audience,),
        permitted_purposes=(ctx.purpose,),
        permitted_actions=(BoundaryAction.READ,),
        issued_at=T0 - timedelta(minutes=5),
        expires_at=T2 + timedelta(hours=1),
    )


def retrieval_request(
    *,
    request_id: str = "RET-1",
    ctx: HostedBoundaryContext | None = None,
    view: HostedRetrievalView = HostedRetrievalView.CURRENT_AUTHORITY,
    mode: RetrievalMode = RetrievalMode.STRUCTURED,
    query: str = "",
    effective_at: datetime | None = T2,
    authority_at: datetime | None = T2,
    as_of: datetime | None = None,
    page_size: int = 50,
    cursor: str | None = None,
    expected_timeline_hash: str | None = None,
) -> HostedRetrievalRequest:
    if view == HostedRetrievalView.AS_OF:
        effective_at = None
        authority_at = None
    return HostedRetrievalRequest(
        request_id=request_id,
        context=ctx or context(),
        view=view,
        mode=mode,
        query=query,
        effective_at=effective_at,
        authority_at=authority_at,
        as_of=as_of,
        page_size=page_size,
        cursor=cursor,
        expected_timeline_hash=expected_timeline_hash,
        requested_at=T2,
    )


def service_with_authority():
    store = persistence()
    authority = identity_authority()
    identity = HostedIdentityService(authority)
    service = HostedRetrievalService(store, identity)
    return service, store, authority, identity


def add_record(
    service: HostedRetrievalService,
    store: SQLiteCanonicalPersistence,
    tenant_id: str,
    record: TemporalAuthorityEnvelope,
    content: str,
    *,
    transaction_id: str,
    **catalog_changes,
) -> None:
    persist(store, tenant_id, record, transaction_id=transaction_id)
    service.catalog.register(
        catalog_entry(tenant_id, record.record_id, content, **catalog_changes)
    )


def test_current_historical_and_as_of_views_are_explicit_and_distinguishable():
    service, store, authority, _ = service_with_authority()
    old_content = "Previous governed career operating model"
    new_content = "Current governed career operating model"
    old = envelope(
        "R1",
        old_content,
        authority_class="operating-model",
        disposition=TemporalAuthorityDisposition.SUPERSEDED,
        authority_valid_to=T1,
        superseded_at=T1,
    )
    new = envelope(
        "R2",
        new_content,
        authority_class="operating-model",
        recorded_at=T1,
        effective_from=T1,
        authority_valid_from=T1,
        supersedes_record_id="R1",
    )
    add_record(service, store, "TENANT-A", old, old_content, transaction_id="TX-R1")
    add_record(service, store, "TENANT-A", new, new_content, transaction_id="TX-R2")
    ctx = context()
    cred = credential(authority, ctx)

    current = service.retrieve(
        retrieval_request(ctx=ctx, view=HostedRetrievalView.CURRENT_AUTHORITY),
        credential=cred,
    )
    historical = service.retrieve(
        retrieval_request(
            request_id="RET-HIST",
            ctx=ctx,
            view=HostedRetrievalView.HISTORICAL,
        ),
        credential=cred,
    )
    as_of = service.retrieve(
        retrieval_request(
            request_id="RET-ASOF",
            ctx=ctx,
            view=HostedRetrievalView.AS_OF,
            as_of=T0 + timedelta(minutes=30),
        ),
        credential=cred,
    )

    assert [hit.record_id for hit in current.projection.hits] == ["R2"]
    assert [hit.record_id for hit in historical.projection.hits] == ["R1"]
    assert [hit.record_id for hit in as_of.projection.hits] == ["R1"]
    assert current.projection.canonical is False
    assert historical.projection.canonical is False
    assert as_of.projection.canonical is False


def test_tenant_subject_and_domain_are_filtered_before_timeline_construction():
    service, store, authority, _ = service_with_authority()
    allowed = envelope("R1", "Allowed content")
    other_tenant = envelope("R2", "Secret other tenant content")
    other_subject = envelope("R3", "Secret other subject", subject_id="SUBJECT-2")
    other_domain = envelope("R4", "Secret other domain", domain="finance")
    add_record(service, store, "TENANT-A", allowed, "Allowed content", transaction_id="TX-A")
    add_record(service, store, "TENANT-B", other_tenant, "Secret other tenant content", transaction_id="TX-B")
    add_record(service, store, "TENANT-A", other_subject, "Secret other subject", transaction_id="TX-S")
    add_record(service, store, "TENANT-A", other_domain, "Secret other domain", transaction_id="TX-D")
    ctx = context()

    result = service.retrieve(retrieval_request(ctx=ctx), credential=credential(authority, ctx))

    assert [hit.record_id for hit in result.projection.hits] == ["R1"]
    assert "R2" not in result.catalog_scope_sha256
    scoped = service.catalog.scoped_records(
        tenant_id="TENANT-A", subject_id="SUBJECT-1", domain="career"
    )
    assert [record.envelope.record_id for record in scoped] == ["R1"]


def test_audience_purpose_privacy_and_provenance_are_enforced_server_side():
    service, store, authority, _ = service_with_authority()
    entries = [
        ("A", "Audience denied", {"audiences": ("other",)}),
        ("P", "Purpose denied", {"purposes": ("other",)}),
        ("X", "Restricted secret", {"privacy": PrivacyClass.RESTRICTED}),
        ("OK", "Allowed content", {"provenance_ids": ("PROV-1", "PROV-2")}),
    ]
    for index, (record_id, content, changes) in enumerate(entries):
        record = envelope(record_id, content, authority_class=f"AUTH-{record_id}")
        add_record(
            service,
            store,
            "TENANT-A",
            record,
            content,
            transaction_id=f"TX-{index}",
            **changes,
        )
    ctx = context()

    result = service.retrieve(
        retrieval_request(ctx=ctx, view=HostedRetrievalView.CURRENT_AUTHORITY),
        credential=credential(authority, ctx),
    )

    assert [hit.record_id for hit in result.projection.hits] == ["OK"]
    assert result.projection.withheld_count == 3
    assert result.projection.hits[0].provenance_ids == ("PROV-1", "PROV-2")


def test_structured_and_semantic_retrieval_are_deterministic():
    service, store, authority, _ = service_with_authority()
    records = [
        ("R-A", "Enterprise architecture and governed knowledge"),
        ("R-B", "Career profile and opportunity intelligence"),
    ]
    for record_id, content in records:
        record = envelope(record_id, content, authority_class=f"AUTH-{record_id}")
        add_record(service, store, "TENANT-A", record, content, transaction_id=f"TX-{record_id}")
    ctx = context()
    cred = credential(authority, ctx)

    structured = service.retrieve(
        retrieval_request(ctx=ctx, query="opportunity", mode=RetrievalMode.STRUCTURED),
        credential=cred,
    )
    semantic_first = service.retrieve(
        retrieval_request(
            request_id="RET-SEM-1",
            ctx=ctx,
            query="governed architecture",
            mode=RetrievalMode.SEMANTIC,
        ),
        credential=cred,
    )
    semantic_second = service.retrieve(
        retrieval_request(
            request_id="RET-SEM-2",
            ctx=ctx,
            query="governed architecture",
            mode=RetrievalMode.SEMANTIC,
        ),
        credential=cred,
    )

    assert [hit.record_id for hit in structured.projection.hits] == ["R-B"]
    assert [hit.record_id for hit in semantic_first.projection.hits] == ["R-A"]
    assert semantic_first.projection == semantic_second.projection


def test_pagination_is_stable_and_stale_cursor_or_expected_hash_fails_closed():
    service, store, authority, _ = service_with_authority()
    for record_id in ("R1", "R2", "R3"):
        content = f"content {record_id}"
        record = envelope(record_id, content, authority_class=f"AUTH-{record_id}")
        add_record(service, store, "TENANT-A", record, content, transaction_id=f"TX-{record_id}")
    ctx = context()
    cred = credential(authority, ctx)

    first = service.retrieve(
        retrieval_request(ctx=ctx, page_size=1),
        credential=cred,
    )
    assert first.projection.next_cursor is not None
    second = service.retrieve(
        retrieval_request(
            request_id="RET-PAGE-2",
            ctx=ctx,
            page_size=1,
            cursor=first.projection.next_cursor,
        ),
        credential=cred,
    )
    assert [hit.record_id for hit in first.projection.hits] == ["R1"]
    assert [hit.record_id for hit in second.projection.hits] == ["R2"]

    new_record = envelope("R4", "content R4", authority_class="AUTH-R4")
    add_record(service, store, "TENANT-A", new_record, "content R4", transaction_id="TX-R4")
    with pytest.raises(StaleKnowledgeStateError):
        service.retrieve(
            retrieval_request(
                request_id="RET-STALE-CURSOR",
                ctx=ctx,
                cursor=first.projection.next_cursor,
            ),
            credential=cred,
        )
    with pytest.raises(StaleKnowledgeStateError):
        service.retrieve(
            retrieval_request(
                request_id="RET-STALE-HASH",
                ctx=ctx,
                expected_timeline_hash=first.projection.timeline_hash,
            ),
            credential=cred,
        )


def test_cross_tenant_identity_is_denied_before_catalog_scope_is_returned():
    service, store, authority, _ = service_with_authority()
    record = envelope("R1", "tenant A")
    add_record(service, store, "TENANT-A", record, "tenant A", transaction_id="TX-A")
    requested = context(tenant_id="TENANT-B")
    wrong = authority.issue(
        credential_id="CRED-A",
        principal_id=requested.principal_id,
        tenant_id="TENANT-A",
        permitted_subjects=(requested.subject_id,),
        permitted_domains=(requested.domain,),
        permitted_audiences=(requested.audience,),
        permitted_purposes=(requested.purpose,),
        permitted_actions=(BoundaryAction.READ,),
        issued_at=T0,
        expires_at=T2 + timedelta(hours=1),
    )

    with pytest.raises(HostedRetrievalError) as caught:
        service.retrieve(retrieval_request(ctx=requested), credential=wrong)

    assert caught.value.reason_code == "IDENTITY_TENANT_MISMATCH"
    assert str(caught.value) == "hosted retrieval denied"


def test_human_state_requires_stricter_policy_for_retrieval():
    service, store, authority, _ = service_with_authority()
    record = envelope("R1", "personal content")
    add_record(service, store, "TENANT-A", record, "personal content", transaction_id="TX-P")
    ctx = context()
    cred = credential(authority, ctx)

    with pytest.raises(HostedRetrievalError) as caught:
        service.retrieve(
            retrieval_request(ctx=ctx),
            credential=cred,
            subject_type="PERSON",
        )
    assert caught.value.reason_code == "IDENTITY_HUMAN_POLICY_DENIED"

    result = service.retrieve(
        retrieval_request(request_id="RET-PERSON-OK", ctx=ctx),
        credential=cred,
        subject_type="PERSON",
        human_policy=HumanBoundaryPolicy(consent_granted=True, purpose_allowed=True),
    )
    assert [hit.record_id for hit in result.projection.hits] == ["R1"]


def test_catalog_registration_requires_matching_tenant_record_and_content_hash():
    service, store, _, _ = service_with_authority()
    record = envelope("R1", "correct content")
    persist(store, "TENANT-A", record, transaction_id="TX-1")

    with pytest.raises(HostedRetrievalError) as missing:
        service.catalog.register(catalog_entry("TENANT-B", "R1", "correct content"))
    assert missing.value.reason_code == "CANONICAL_RECORD_NOT_FOUND"

    with pytest.raises(HostedRetrievalError) as mismatch:
        service.catalog.register(catalog_entry("TENANT-A", "R1", "tampered content"))
    assert mismatch.value.reason_code == "CATALOG_CONTENT_HASH_MISMATCH"


def test_replay_same_exact_retrieval_produces_same_noncanonical_projection_hash():
    service, store, authority, _ = service_with_authority()
    record = envelope("R1", "deterministic content")
    add_record(service, store, "TENANT-A", record, "deterministic content", transaction_id="TX-1")
    ctx = context()
    req = retrieval_request(ctx=ctx)
    cred = credential(authority, ctx)

    first = service.retrieve(req, credential=cred)
    second = service.retrieve(req, credential=cred)

    assert first.projection == second.projection
    assert first.result_sha256 == second.result_sha256
    assert first.projection.canonical is False


def test_filtered_projection_can_reach_model_only_through_provider_neutral_gateway():
    service, store, authority, _ = service_with_authority()
    record = envelope("R1", "governed model context")
    add_record(
        service,
        store,
        "TENANT-A",
        record,
        "governed model context",
        transaction_id="TX-MODEL",
        provenance_ids=("EVIDENCE-1",),
    )
    ctx = context()
    req = retrieval_request(ctx=ctx)
    result = service.retrieve(req, credential=credential(authority, ctx))

    handoff = build_model_gateway_handoff(
        result,
        req,
        subject_type="ORGANIZATION",
        issued_by="PRINCIPAL-A",
        authority_class="HOSTED-TEST-IDENTITY",
    )
    provider = DeterministicNoEffectModelProvider()
    replay_store = ModelGatewayReplayStore()
    first = execute_model_gateway(
        handoff.gateway_request,
        provider=provider,
        replay_store=replay_store,
    )
    second = execute_model_gateway(
        handoff.gateway_request,
        provider=provider,
        replay_store=replay_store,
    )

    assert handoff.projection_sha256 == result.projection.projection_hash
    assert handoff.canonical_mutation_authorized is False
    assert handoff.direct_provider_dispatch_authorized is False
    assert first.output.canonical is False
    assert first.receipt.canonical_mutation is False
    assert first.receipt.external_effect is False
    assert second.replayed is True
    assert second.receipt == first.receipt
    assert store.connection.execute(
        "SELECT COUNT(*) AS count FROM canonical_records"
    ).fetchone()["count"] == 1


def test_model_handoff_cannot_claim_canonical_mutation_or_direct_dispatch():
    service, store, authority, _ = service_with_authority()
    record = envelope("R1", "content")
    add_record(service, store, "TENANT-A", record, "content", transaction_id="TX-1")
    ctx = context()
    req = retrieval_request(ctx=ctx)
    result = service.retrieve(req, credential=credential(authority, ctx))
    valid = build_model_gateway_handoff(
        result,
        req,
        subject_type="ORGANIZATION",
        issued_by="PRINCIPAL-A",
        authority_class="HOSTED-TEST-IDENTITY",
    )
    payload = valid.model_dump(mode="python")
    payload["canonical_mutation_authorized"] = True

    with pytest.raises(ValidationError):
        HostedModelGatewayHandoff(**payload)
