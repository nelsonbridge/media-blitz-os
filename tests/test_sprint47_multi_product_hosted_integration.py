from __future__ import annotations

from datetime import datetime, timezone

import pytest

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
    MultiConsumerWorkItem,
    PlatformIncidentKind,
    PlatformTerminalState,
    WorkFailureMode,
)
from nks.application.multi_product_hosted_integration import (
    MultiProductHostedIntegration,
    MultiProductIntegrationError,
)
from nks.application.privacy_observability import assert_telemetry_safe_serialization
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


NOW = datetime(2026, 7, 18, 2, 0, tzinfo=timezone.utc)
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
TENANTS = {
    ProductSuite.MEDIA_BLITZ: "TENANT-MEDIA",
    ProductSuite.CAREER_INTELLIGENCE_PLACEMENT: "TENANT-CAREER",
    ProductSuite.PERSONAL_COGNITIVE_CONTINUITY: "TENANT-PERSONAL",
}
SUBJECTS = {
    ProductSuite.MEDIA_BLITZ: "SUBJECT-PUBLICATION",
    ProductSuite.CAREER_INTELLIGENCE_PLACEMENT: "SUBJECT-CAREER",
    ProductSuite.PERSONAL_COGNITIVE_CONTINUITY: "SUBJECT-PERSON",
}


def make_boundary(suite: ProductSuite) -> BoundaryContext:
    return BoundaryContext(
        namespace_id="enki",
        tenant_id=TENANTS[suite],
        subject_id=SUBJECTS[suite],
        domain=DOMAINS[suite],
        audience=EXPECTED_AUDIENCE[suite],
        execution_context=ExecutionContext.TEST,
    )


def make_contract(suite: ProductSuite) -> ProductConsumerContract:
    return ProductConsumerContract.create(
        contract_id=f"SPRINT47-{suite.value}",
        suite=suite,
        consumer_contract_version="1.0",
        boundary=make_boundary(suite),
        authorization_id=f"AUTH-SPRINT47-{suite.value}",
        purpose=PURPOSES[suite],
        permitted_output_kinds=OUTPUTS[suite],
    )


def make_registry() -> tuple[ProductBoundaryRegistry, dict[ProductSuite, ProductConsumerContract]]:
    contracts = {suite: make_contract(suite) for suite in ProductSuite}
    return ProductBoundaryRegistry(list(contracts.values())), contracts


def make_record(contract: ProductConsumerContract, work_id: str) -> GovernedKnowledgeRecord:
    content = f"synthetic governed TEST knowledge for {work_id}"
    envelope = TemporalAuthorityEnvelope(
        record_id=f"RECORD-{work_id}",
        subject_id=contract.boundary.subject_id,
        domain=contract.boundary.domain,
        authority_class=f"authority-{work_id}",
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
        provenance_ids=(f"PROV-{work_id}",),
    )


def make_request(contract: ProductConsumerContract) -> GovernedRetrievalRequest:
    boundary = contract.boundary
    return GovernedRetrievalRequest(
        tenant_id=boundary.tenant_id,
        subject_id=boundary.subject_id,
        domain=boundary.domain,
        audience=boundary.audience,
        purpose=contract.purpose,
        query="",
        mode=RetrievalMode.STRUCTURED,
        view=RetrievalView.CURRENT,
        effective_at=NOW,
        authority_at=NOW,
        page_size=50,
    )


def human_control() -> HumanContinuityControl:
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
        requested_intent=ConsumerIntent.COGNITIVE_CONTINUITY_VIEW,
    )


def make_work(
    contract: ProductConsumerContract,
    *,
    work_id: str,
    failure_mode: WorkFailureMode = WorkFailureMode.NONE,
    contention_key: str | None = None,
    delay_ms: int = 0,
    human: HumanContinuityControl | None = None,
) -> MultiConsumerWorkItem:
    record = make_record(contract, work_id)
    return MultiConsumerWorkItem(
        work_id=work_id,
        suite=contract.suite,
        intent=INTENTS[contract.suite],
        boundary=contract.boundary,
        records=(record,),
        retrieval_request=make_request(contract),
        submitted_at=NOW,
        simulated_feedback=("synthetic-zero-response",)
        if contract.suite == ProductSuite.MEDIA_BLITZ
        else (),
        human_control=(
            human or human_control()
            if contract.suite == ProductSuite.PERSONAL_COGNITIVE_CONTINUITY
            else None
        ),
        contention_key=contention_key,
        delay_ms=delay_ms,
        failure_mode=failure_mode,
    )


def three_product_items(
    contracts: dict[ProductSuite, ProductConsumerContract],
    *,
    career_failure: WorkFailureMode = WorkFailureMode.NONE,
) -> list[MultiConsumerWorkItem]:
    return [
        make_work(
            contracts[ProductSuite.MEDIA_BLITZ],
            work_id="MEDIA-47",
            contention_key="SHARED-PLATFORM",
            delay_ms=10,
        ),
        make_work(
            contracts[ProductSuite.CAREER_INTELLIGENCE_PLACEMENT],
            work_id="CAREER-47",
            failure_mode=career_failure,
            contention_key="SHARED-PLATFORM",
            delay_ms=5,
        ),
        make_work(
            contracts[ProductSuite.PERSONAL_COGNITIVE_CONTINUITY],
            work_id="PCC-47",
        ),
    ]


def test_all_three_products_execute_through_one_governed_test_surface() -> None:
    registry, contracts = make_registry()
    integration = MultiProductHostedIntegration(registry=registry, max_workers=3)

    report, manifest, results, incidents, bundle = integration.execute(
        run_id="SPRINT47-THREE-PRODUCTS",
        items=three_product_items(contracts),
        now=NOW,
    )

    assert set(report.suites) == set(ProductSuite)
    assert {result.suite for result in results} == set(ProductSuite)
    assert all(result.terminal_state == PlatformTerminalState.COMMITTED for result in results)
    assert manifest.execution_context == ExecutionContext.TEST
    assert report.no_canonical_mutation is True
    assert report.no_external_effect is True
    assert report.provider_effects == 0
    assert report.manifest_sha256 == manifest.manifest_sha256
    assert report.portable_bundle_sha256 == bundle.bundle_sha256
    assert report.reconstructed_manifest_sha256 == manifest.manifest_sha256
    assert any(incident.kind == PlatformIncidentKind.CONTENTION for incident in incidents)
    assert_telemetry_safe_serialization(list(integration.coordinator.telemetry.events))


def test_one_product_failure_does_not_widen_or_fail_other_product_authority() -> None:
    registry, contracts = make_registry()
    integration = MultiProductHostedIntegration(registry=registry, max_workers=2)

    report, manifest, results, incidents, _ = integration.execute(
        run_id="SPRINT47-ISOLATED-FAILURE",
        items=three_product_items(contracts, career_failure=WorkFailureMode.ALWAYS),
        now=NOW,
    )

    by_suite = {result.suite: result for result in results}
    assert by_suite[ProductSuite.CAREER_INTELLIGENCE_PLACEMENT].terminal_state == PlatformTerminalState.ROLLED_BACK
    assert by_suite[ProductSuite.MEDIA_BLITZ].terminal_state == PlatformTerminalState.COMMITTED
    assert by_suite[ProductSuite.PERSONAL_COGNITIVE_CONTINUITY].terminal_state == PlatformTerminalState.COMMITTED
    assert manifest.no_canonical_mutation is True
    assert manifest.no_external_effect is True
    assert report.provider_effects == 0
    assert any(incident.kind == PlatformIncidentKind.CONSUMER_FAILURE for incident in incidents)
    assert any(incident.kind == PlatformIncidentKind.QUEUE_PRESSURE for incident in incidents)


def test_personal_cognitive_continuity_requires_stricter_human_controls() -> None:
    registry, contracts = make_registry()
    integration = MultiProductHostedIntegration(registry=registry, max_workers=3)
    denied_human = HumanContinuityControl(
        policy=HumanBoundaryPolicy(
            consent_granted=False,
            purpose_allowed=True,
            revoked=False,
            correction_or_retraction_blocked=False,
        ),
        explicit_human_authority=True,
        privacy_acknowledged=True,
        temporal_authority_acknowledged=True,
        requested_intent=ConsumerIntent.COGNITIVE_CONTINUITY_VIEW,
    )
    items = three_product_items(contracts)
    items[2] = make_work(
        contracts[ProductSuite.PERSONAL_COGNITIVE_CONTINUITY],
        work_id="PCC-DENIED",
        human=denied_human,
    )

    _, manifest, results, incidents, _ = integration.execute(
        run_id="SPRINT47-HUMAN-CONTROL",
        items=items,
        now=NOW,
    )

    by_suite = {result.suite: result for result in results}
    assert by_suite[ProductSuite.PERSONAL_COGNITIVE_CONTINUITY].terminal_state == PlatformTerminalState.ROLLED_BACK
    assert by_suite[ProductSuite.MEDIA_BLITZ].terminal_state == PlatformTerminalState.COMMITTED
    assert by_suite[ProductSuite.CAREER_INTELLIGENCE_PLACEMENT].terminal_state == PlatformTerminalState.COMMITTED
    assert manifest.no_canonical_mutation is True
    assert any(incident.kind == PlatformIncidentKind.CONSUMER_FAILURE for incident in incidents)


def test_missing_product_suite_fails_before_execution() -> None:
    registry, contracts = make_registry()
    integration = MultiProductHostedIntegration(registry=registry)
    items = three_product_items(contracts)[:2]

    with pytest.raises(MultiProductIntegrationError, match="exactly the three governed product suites"):
        integration.execute(run_id="SPRINT47-MISSING-SUITE", items=items, now=NOW)


def test_report_is_deterministic_for_equivalent_three_product_runs() -> None:
    registry_a, contracts_a = make_registry()
    registry_b, contracts_b = make_registry()
    first = MultiProductHostedIntegration(registry=registry_a, max_workers=3)
    second = MultiProductHostedIntegration(registry=registry_b, max_workers=3)

    first_report, first_manifest, first_results, _, _ = first.execute(
        run_id="SPRINT47-DETERMINISTIC",
        items=three_product_items(contracts_a),
        now=NOW,
    )
    second_report, second_manifest, second_results, _, _ = second.execute(
        run_id="SPRINT47-DETERMINISTIC",
        items=list(reversed(three_product_items(contracts_b))),
        now=NOW,
    )

    assert first_manifest.manifest_sha256 == second_manifest.manifest_sha256
    assert tuple(sorted(item.result_sha256 for item in first_results)) == tuple(
        sorted(item.result_sha256 for item in second_results)
    )
    assert first_report.report_sha256 == second_report.report_sha256


def test_product_contract_boundary_mismatch_rolls_back_only_that_work_item() -> None:
    registry, contracts = make_registry()
    integration = MultiProductHostedIntegration(registry=registry)
    media = contracts[ProductSuite.MEDIA_BLITZ]
    wrong_boundary = BoundaryContext(
        namespace_id=media.boundary.namespace_id,
        tenant_id="TENANT-WRONG",
        subject_id=media.boundary.subject_id,
        domain=media.boundary.domain,
        audience=media.boundary.audience,
        execution_context=ExecutionContext.TEST,
    )
    bad_media = MultiConsumerWorkItem(
        work_id="MEDIA-WRONG-TENANT",
        suite=ProductSuite.MEDIA_BLITZ,
        intent=ConsumerIntent.MEDIA_PUBLICATION_PROOF,
        boundary=wrong_boundary,
        records=(make_record(media, "MEDIA-WRONG-TENANT"),),
        retrieval_request=GovernedRetrievalRequest(
            tenant_id=wrong_boundary.tenant_id,
            subject_id=wrong_boundary.subject_id,
            domain=wrong_boundary.domain,
            audience=wrong_boundary.audience,
            purpose=media.purpose,
            query="",
            mode=RetrievalMode.STRUCTURED,
            view=RetrievalView.CURRENT,
            effective_at=NOW,
            authority_at=NOW,
            page_size=50,
        ),
        submitted_at=NOW,
    )
    items = [
        bad_media,
        make_work(contracts[ProductSuite.CAREER_INTELLIGENCE_PLACEMENT], work_id="CAREER-GOOD"),
        make_work(contracts[ProductSuite.PERSONAL_COGNITIVE_CONTINUITY], work_id="PCC-GOOD"),
    ]

    _, manifest, results, incidents, _ = integration.execute(
        run_id="SPRINT47-CROSS-TENANT-DENIAL",
        items=items,
        now=NOW,
    )

    by_suite = {result.suite: result for result in results}
    assert by_suite[ProductSuite.MEDIA_BLITZ].terminal_state == PlatformTerminalState.ROLLED_BACK
    assert by_suite[ProductSuite.CAREER_INTELLIGENCE_PLACEMENT].terminal_state == PlatformTerminalState.COMMITTED
    assert by_suite[ProductSuite.PERSONAL_COGNITIVE_CONTINUITY].terminal_state == PlatformTerminalState.COMMITTED
    assert manifest.no_canonical_mutation is True
    assert manifest.no_external_effect is True
    assert any(incident.kind == PlatformIncidentKind.CONSUMER_FAILURE for incident in incidents)
