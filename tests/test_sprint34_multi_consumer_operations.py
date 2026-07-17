from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from nks.application.downstream_products import (
    EXPECTED_AUDIENCE,
    ProductBoundaryRegistry,
    ProductConsumerContract,
    ProductSuite,
)
from nks.application.governed_transactions import canonical_sha256
from nks.application.hosted_downstream_integration import (
    ConsumerIntent,
    HumanContinuityControl,
)
from nks.application.multi_consumer_operations import (
    MultiConsumerPlatformCoordinator,
    MultiConsumerWorkItem,
    PlatformIncidentKind,
    PlatformTerminalState,
    PortableMultiConsumerBundle,
    WorkFailureMode,
    reconstruct_multi_consumer_bundle,
)
from nks.application.privacy_observability import assert_telemetry_safe_serialization
from nks.application.sprint34_path_manifest import sprint34_multi_consumer_path_manifest
from nks.enki.governed_retrieval import (
    GovernedKnowledgeRecord,
    GovernedRetrievalRequest,
    PrivacyClass,
    RetrievalMode,
    RetrievalView,
)
from nks.enki.temporal_authority import TemporalAuthorityEnvelope
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryContext, HumanBoundaryPolicy


NOW = datetime(2026, 7, 17, 7, 0, tzinfo=timezone.utc)
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)

DOMAINS = {
    ProductSuite.MEDIA_BLITZ: "content",
    ProductSuite.CAREER_INTELLIGENCE_PLACEMENT: "professional",
    ProductSuite.PERSONAL_COGNITIVE_CONTINUITY: "personal",
}
PURPOSES = {
    ProductSuite.MEDIA_BLITZ: "governed-media-production",
    ProductSuite.CAREER_INTELLIGENCE_PLACEMENT: "career-assistance",
    ProductSuite.PERSONAL_COGNITIVE_CONTINUITY: "cognitive-continuity",
}
OUTPUTS = {
    ProductSuite.MEDIA_BLITZ: {"publication-package", "distribution-plan"},
    ProductSuite.CAREER_INTELLIGENCE_PLACEMENT: {"opportunity-view", "application-package"},
    ProductSuite.PERSONAL_COGNITIVE_CONTINUITY: {"continuity-view", "reflection-package"},
}
INTENTS = {
    ProductSuite.MEDIA_BLITZ: ConsumerIntent.MEDIA_PUBLICATION_PROOF,
    ProductSuite.CAREER_INTELLIGENCE_PLACEMENT: ConsumerIntent.CAREER_OPPORTUNITY_VIEW,
    ProductSuite.PERSONAL_COGNITIVE_CONTINUITY: ConsumerIntent.COGNITIVE_CONTINUITY_VIEW,
}


def make_boundary(
    suite: ProductSuite,
    *,
    namespace_id: str = "enki",
    tenant_id: str = "tenant-1",
    subject_id: str = "subject-1",
    domain: str | None = None,
    audience: str | None = None,
    execution_context: ExecutionContext = ExecutionContext.TEST,
) -> BoundaryContext:
    return BoundaryContext(
        namespace_id=namespace_id,
        tenant_id=tenant_id,
        subject_id=subject_id,
        domain=domain or DOMAINS[suite],
        audience=audience or EXPECTED_AUDIENCE[suite],
        execution_context=execution_context,
    )


def make_contract(suite: ProductSuite) -> ProductConsumerContract:
    return ProductConsumerContract.create(
        contract_id=f"SPRINT34-{suite.value}",
        suite=suite,
        consumer_contract_version="1.0",
        boundary=make_boundary(suite),
        authorization_id=f"AUTH-SPRINT34-{suite.value}",
        purpose=PURPOSES[suite],
        permitted_output_kinds=OUTPUTS[suite],
    )


def make_registry() -> tuple[ProductBoundaryRegistry, dict[ProductSuite, ProductConsumerContract]]:
    contracts = {suite: make_contract(suite) for suite in ProductSuite}
    return ProductBoundaryRegistry(list(contracts.values())), contracts


def make_record(
    contract: ProductConsumerContract,
    *,
    record_id: str,
    content: str,
) -> GovernedKnowledgeRecord:
    envelope = TemporalAuthorityEnvelope(
        record_id=record_id,
        subject_id=contract.boundary.subject_id,
        domain=contract.boundary.domain,
        authority_class=f"authority-{record_id}",
        content_hash=canonical_sha256(content),
        schema_version="1",
        recorded_at=T0,
        effective_from=T0,
        authority_valid_from=T0,
    )
    return GovernedKnowledgeRecord(
        envelope=envelope,
        tenant_id=contract.boundary.tenant_id,
        content=content,
        allowed_audiences=frozenset({contract.boundary.audience}),
        allowed_purposes=frozenset({contract.purpose}),
        privacy_class=(
            PrivacyClass.PRIVATE
            if contract.suite == ProductSuite.PERSONAL_COGNITIVE_CONTINUITY
            else PrivacyClass.INTERNAL
        ),
        provenance_ids=(f"PROV-{record_id}",),
    )


def make_request(
    contract: ProductConsumerContract,
    *,
    boundary: BoundaryContext | None = None,
    purpose: str | None = None,
) -> GovernedRetrievalRequest:
    selected = boundary or contract.boundary
    return GovernedRetrievalRequest(
        tenant_id=selected.tenant_id,
        subject_id=selected.subject_id,
        domain=selected.domain,
        audience=selected.audience,
        purpose=purpose or contract.purpose,
        query="",
        mode=RetrievalMode.STRUCTURED,
        view=RetrievalView.CURRENT,
        effective_at=NOW,
        authority_at=NOW,
        page_size=50,
    )


def human_control(intent: ConsumerIntent) -> HumanContinuityControl:
    return HumanContinuityControl(
        policy=HumanBoundaryPolicy(
            consent_granted=True,
            purpose_allowed=True,
            revoked=False,
            correction_or_retraction_blocked=False,
        ),
        explicit_human_authority=True,
        privacy_acknowledged=True,
        temporal_authority_acknowledged=True,
        requested_intent=intent,
    )


def make_work(
    contract: ProductConsumerContract,
    *,
    work_id: str,
    boundary: BoundaryContext | None = None,
    request: GovernedRetrievalRequest | None = None,
    record: GovernedKnowledgeRecord | None = None,
    failure_mode: WorkFailureMode = WorkFailureMode.NONE,
    contention_key: str | None = None,
    delay_ms: int = 0,
) -> MultiConsumerWorkItem:
    selected_boundary = boundary or contract.boundary
    selected_record = record or make_record(
        contract,
        record_id=f"RECORD-{work_id}",
        content=f"synthetic governed TEST content for {work_id}",
    )
    intent = INTENTS[contract.suite]
    return MultiConsumerWorkItem(
        work_id=work_id,
        suite=contract.suite,
        intent=intent,
        boundary=selected_boundary,
        records=(selected_record,),
        retrieval_request=request or make_request(contract, boundary=selected_boundary),
        submitted_at=NOW,
        simulated_feedback=("synthetic-zero-response",)
        if contract.suite == ProductSuite.MEDIA_BLITZ
        else (),
        human_control=(
            human_control(intent)
            if contract.suite == ProductSuite.PERSONAL_COGNITIVE_CONTINUITY
            else None
        ),
        contention_key=contention_key,
        delay_ms=delay_ms,
        failure_mode=failure_mode,
    )


def basic_three_suite_items(
    contracts: dict[ProductSuite, ProductConsumerContract],
) -> list[MultiConsumerWorkItem]:
    return [
        make_work(contracts[ProductSuite.MEDIA_BLITZ], work_id="MEDIA-1", delay_ms=10),
        make_work(
            contracts[ProductSuite.CAREER_INTELLIGENCE_PLACEMENT],
            work_id="CAREER-1",
            delay_ms=5,
        ),
        make_work(
            contracts[ProductSuite.PERSONAL_COGNITIVE_CONTINUITY],
            work_id="PCC-1",
        ),
    ]


def test_three_suites_execute_concurrently_without_cross_product_effects() -> None:
    registry, contracts = make_registry()
    coordinator = MultiConsumerPlatformCoordinator(registry=registry, max_workers=3)

    manifest, results, incidents = coordinator.execute_run(
        run_id="RUN-THREE-SUITES",
        items=basic_three_suite_items(contracts),
        now=NOW,
    )

    assert {result.suite for result in results} == set(ProductSuite)
    assert {result.terminal_state for result in results} == {PlatformTerminalState.COMMITTED}
    assert len(set(result.product_receipt_sha256 for result in results)) == 3
    assert manifest.canonical_input_sha256 == manifest.canonical_output_sha256
    assert manifest.no_canonical_mutation is True
    assert manifest.no_external_effect is True
    assert incidents == ()
    assert_telemetry_safe_serialization(list(coordinator.telemetry.events))


def test_queue_pressure_contention_duplicate_receipt_and_transient_recovery() -> None:
    registry, contracts = make_registry()
    coordinator = MultiConsumerPlatformCoordinator(registry=registry, max_workers=2)
    media_contract = contracts[ProductSuite.MEDIA_BLITZ]
    shared_record = make_record(
        media_contract,
        record_id="MEDIA-SHARED",
        content="shared synthetic publication source",
    )
    duplicate_request = make_request(media_contract)
    items = [
        make_work(
            media_contract,
            work_id="MEDIA-DUP-A",
            record=shared_record,
            request=duplicate_request,
            contention_key="publication-shared",
        ),
        make_work(
            media_contract,
            work_id="MEDIA-DUP-B",
            record=shared_record,
            request=duplicate_request,
            contention_key="publication-shared",
        ),
        make_work(
            contracts[ProductSuite.CAREER_INTELLIGENCE_PLACEMENT],
            work_id="CAREER-RETRY",
            failure_mode=WorkFailureMode.ONCE,
        ),
        make_work(
            contracts[ProductSuite.PERSONAL_COGNITIVE_CONTINUITY],
            work_id="PCC-DELAYED",
            delay_ms=15,
        ),
    ]

    manifest, results, incidents = coordinator.execute_run(
        run_id="RUN-PRESSURE",
        items=items,
        now=NOW,
    )

    by_id = {result.work_id: result for result in results}
    assert by_id["MEDIA-DUP-A"].product_receipt_sha256 == by_id["MEDIA-DUP-B"].product_receipt_sha256
    assert by_id["CAREER-RETRY"].terminal_state == PlatformTerminalState.RECOVERED
    assert by_id["CAREER-RETRY"].exact_retry is True
    assert len(by_id["CAREER-RETRY"].attempts) == 2
    kinds = {incident.kind for incident in incidents}
    assert PlatformIncidentKind.QUEUE_PRESSURE in kinds
    assert PlatformIncidentKind.CONTENTION in kinds
    assert PlatformIncidentKind.RETRY_RECOVERY in kinds
    assert manifest.canonical_input_sha256 == manifest.canonical_output_sha256


def test_persistent_consumer_failure_rolls_back_without_affecting_peer_consumers() -> None:
    registry, contracts = make_registry()
    coordinator = MultiConsumerPlatformCoordinator(registry=registry, max_workers=3)
    items = [
        make_work(
            contracts[ProductSuite.MEDIA_BLITZ],
            work_id="MEDIA-FAIL",
            failure_mode=WorkFailureMode.ALWAYS,
        ),
        make_work(
            contracts[ProductSuite.CAREER_INTELLIGENCE_PLACEMENT],
            work_id="CAREER-SAFE",
        ),
        make_work(
            contracts[ProductSuite.PERSONAL_COGNITIVE_CONTINUITY],
            work_id="PCC-SAFE",
        ),
    ]

    manifest, results, incidents = coordinator.execute_run(
        run_id="RUN-FAILURE-ISOLATION",
        items=items,
        now=NOW,
    )

    by_id = {result.work_id: result for result in results}
    assert by_id["MEDIA-FAIL"].terminal_state == PlatformTerminalState.ROLLED_BACK
    assert by_id["MEDIA-FAIL"].product_receipt_sha256 is None
    assert by_id["CAREER-SAFE"].terminal_state == PlatformTerminalState.COMMITTED
    assert by_id["PCC-SAFE"].terminal_state == PlatformTerminalState.COMMITTED
    assert PlatformIncidentKind.CONSUMER_FAILURE in {incident.kind for incident in incidents}
    assert manifest.canonical_input_sha256 == manifest.canonical_output_sha256
    assert manifest.no_canonical_mutation is True
    assert manifest.no_external_effect is True


@pytest.mark.parametrize(
    "dimension",
    ["namespace", "tenant", "subject", "domain", "audience", "purpose"],
)
def test_boundary_and_purpose_escape_fail_closed_without_stopping_peer_workloads(
    dimension: str,
) -> None:
    registry, contracts = make_registry()
    coordinator = MultiConsumerPlatformCoordinator(registry=registry, max_workers=2)
    media = contracts[ProductSuite.MEDIA_BLITZ]
    career = contracts[ProductSuite.CAREER_INTELLIGENCE_PLACEMENT]

    if dimension == "purpose":
        invalid_boundary = media.boundary
        invalid_request = make_request(media, purpose="unauthorized-purpose")
    else:
        kwargs: dict[str, str] = {}
        if dimension == "namespace":
            kwargs["namespace_id"] = "other-namespace"
        elif dimension == "tenant":
            kwargs["tenant_id"] = "other-tenant"
        elif dimension == "subject":
            kwargs["subject_id"] = "other-subject"
        elif dimension == "domain":
            kwargs["domain"] = "other-domain"
        elif dimension == "audience":
            kwargs["audience"] = "other-audience"
        invalid_boundary = make_boundary(ProductSuite.MEDIA_BLITZ, **kwargs)
        invalid_request = make_request(media, boundary=invalid_boundary)

    invalid = make_work(
        media,
        work_id=f"MEDIA-INVALID-{dimension}",
        boundary=invalid_boundary,
        request=invalid_request,
    )
    peer = make_work(career, work_id=f"CAREER-PEER-{dimension}")

    manifest, results, incidents = coordinator.execute_run(
        run_id=f"RUN-ISOLATION-{dimension}",
        items=[invalid, peer],
        now=NOW,
    )

    by_id = {result.work_id: result for result in results}
    assert by_id[invalid.work_id].terminal_state == PlatformTerminalState.ROLLED_BACK
    assert by_id[peer.work_id].terminal_state == PlatformTerminalState.COMMITTED
    assert PlatformIncidentKind.CONSUMER_FAILURE in {incident.kind for incident in incidents}
    assert manifest.canonical_input_sha256 == manifest.canonical_output_sha256


def test_production_execution_context_is_rejected_before_multi_consumer_execution() -> None:
    _, contracts = make_registry()
    contract = contracts[ProductSuite.MEDIA_BLITZ]
    production_boundary = make_boundary(
        ProductSuite.MEDIA_BLITZ,
        execution_context=ExecutionContext.PRODUCTION,
    )
    request = make_request(contract, boundary=production_boundary)

    with pytest.raises(ValidationError, match="TEST-only"):
        make_work(
            contract,
            work_id="MEDIA-PRODUCTION-DENIED",
            boundary=production_boundary,
            request=request,
        )


def test_privacy_safe_telemetry_and_incidents_never_include_protected_payload() -> None:
    registry, contracts = make_registry()
    coordinator = MultiConsumerPlatformCoordinator(registry=registry, max_workers=1)
    media = contracts[ProductSuite.MEDIA_BLITZ]
    career = contracts[ProductSuite.CAREER_INTELLIGENCE_PLACEMENT]
    sensitive = make_record(
        media,
        record_id="MEDIA-SENSITIVE",
        content="private.person@example.com password=never-log-this sk-testsecret123456",
    )
    items = [
        make_work(
            media,
            work_id="MEDIA-SENSITIVE-WORK",
            record=sensitive,
            contention_key="shared-pressure",
        ),
        make_work(
            career,
            work_id="CAREER-PRESSURE-WORK",
            contention_key="shared-pressure",
            failure_mode=WorkFailureMode.ALWAYS,
        ),
    ]

    _, _, incidents = coordinator.execute_run(
        run_id="RUN-PRIVACY-TELEMETRY",
        items=items,
        now=NOW,
    )

    events = list(coordinator.telemetry.events)
    assert_telemetry_safe_serialization(events)
    rendered_events = "\n".join(event.model_dump_json() for event in events)
    rendered_incidents = "\n".join(incident.model_dump_json() for incident in incidents)
    for protected in ("private.person@example.com", "never-log-this", "sk-testsecret123456"):
        assert protected not in rendered_events
        assert protected not in rendered_incidents
    assert all(incident.protected_payload_included is False for incident in incidents)


def test_portable_bundle_is_deterministic_and_reconstructs_exact_manifest() -> None:
    registry_a, contracts_a = make_registry()
    coordinator_a = MultiConsumerPlatformCoordinator(registry=registry_a, max_workers=2)
    items_a = basic_three_suite_items(contracts_a)
    manifest_a, results_a, incidents_a = coordinator_a.execute_run(
        run_id="RUN-PORTABLE",
        items=items_a,
        now=NOW,
    )
    bundle_a = coordinator_a.portable_bundle(
        manifest=manifest_a,
        results=results_a,
        incidents=incidents_a,
    )

    registry_b, contracts_b = make_registry()
    coordinator_b = MultiConsumerPlatformCoordinator(registry=registry_b, max_workers=2)
    items_b = basic_three_suite_items(contracts_b)
    manifest_b, results_b, incidents_b = coordinator_b.execute_run(
        run_id="RUN-PORTABLE",
        items=items_b,
        now=NOW,
    )
    bundle_b = coordinator_b.portable_bundle(
        manifest=manifest_b,
        results=results_b,
        incidents=incidents_b,
    )

    assert manifest_b == manifest_a
    assert bundle_b.bundle_sha256 == bundle_a.bundle_sha256
    assert reconstruct_multi_consumer_bundle(bundle_a) == manifest_a


def test_tampered_portable_bundle_fails_closed() -> None:
    registry, contracts = make_registry()
    coordinator = MultiConsumerPlatformCoordinator(registry=registry, max_workers=3)
    manifest, results, incidents = coordinator.execute_run(
        run_id="RUN-TAMPER",
        items=basic_three_suite_items(contracts),
        now=NOW,
    )
    bundle = coordinator.portable_bundle(
        manifest=manifest,
        results=results,
        incidents=incidents,
    )
    tampered = bundle.model_dump(mode="python")
    tampered["telemetry_event_sha256"] = tuple(
        ["sha256:" + "0" * 64, *tampered["telemetry_event_sha256"][1:]]
    )

    with pytest.raises(ValidationError):
        PortableMultiConsumerBundle.model_validate(tampered)


SPRINT34_TESTED_PATHS = {
    "three-suite-concurrent-success",
    "tenant-isolation-under-concurrency",
    "namespace-isolation-under-concurrency",
    "subject-isolation-under-concurrency",
    "domain-isolation-under-concurrency",
    "audience-isolation-under-concurrency",
    "purpose-isolation-under-concurrency",
    "execution-context-isolation-under-concurrency",
    "queue-pressure-detected",
    "contention-detected",
    "duplicate-work-reuses-exact-product-receipt",
    "transient-failure-exact-retry-recovers",
    "persistent-consumer-failure-rolls-back-no-effect",
    "consumer-failure-does-not-widen-peer-authority",
    "consumer-failure-does-not-change-canonical-fingerprint",
    "privacy-safe-queue-telemetry",
    "privacy-safe-incident-evidence",
    "portable-bundle-deterministic",
    "portable-bundle-reconstruction-exact",
    "tampered-portable-bundle-denied",
    "production-boundary-denied",
}


def test_every_declared_sprint34_path_has_automated_coverage() -> None:
    sprint34_multi_consumer_path_manifest().assert_complete_coverage(SPRINT34_TESTED_PATHS)


def test_sprint34_paths_are_test_only_and_prohibit_boundary_escape() -> None:
    manifest = sprint34_multi_consumer_path_manifest()
    assert manifest.execution_context == ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "direct-canonical-write" in path.prohibited_effects
        assert "cross-product-authority-widening" in path.prohibited_effects
        assert "cross-tenant-leakage" in path.prohibited_effects
        assert "cross-subject-leakage" in path.prohibited_effects
        assert "protected-payload-telemetry" in path.prohibited_effects
