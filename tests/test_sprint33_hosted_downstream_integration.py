from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from nks.application.downstream_products import (
    EXPECTED_AUDIENCE,
    NoEffectProductAdapter,
    ProductBoundaryFailure,
    ProductBoundaryRegistry,
    ProductConsumerContract,
    ProductPackage,
    ProductSuite,
)
from nks.application.governed_transactions import canonical_sha256
from nks.application.hosted_downstream_integration import (
    ConsumerIntent,
    ExternalActionAuthorization,
    HostedDownstreamConsumerService,
    HumanContinuityControl,
)
from nks.application.sprint33_path_manifest import sprint33_hosted_downstream_path_manifest
from nks.enki.governed_retrieval import (
    GovernedKnowledgeRecord,
    GovernedRetrievalRequest,
    PrivacyClass,
    RetrievalMode,
    RetrievalView,
    retrieve_governed_knowledge,
)
from nks.enki.temporal_authority import (
    TemporalAuthorityDisposition,
    TemporalAuthorityEnvelope,
)
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryContext, HumanBoundaryPolicy


NOW = datetime(2026, 7, 17, 6, 0, tzinfo=timezone.utc)
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
T1 = datetime(2026, 2, 1, tzinfo=timezone.utc)


PURPOSES = {
    ProductSuite.MEDIA_BLITZ: "governed-media-production",
    ProductSuite.CAREER_INTELLIGENCE_PLACEMENT: "career-assistance",
    ProductSuite.PERSONAL_COGNITIVE_CONTINUITY: "cognitive-continuity",
}

DOMAINS = {
    ProductSuite.MEDIA_BLITZ: "content",
    ProductSuite.CAREER_INTELLIGENCE_PLACEMENT: "professional",
    ProductSuite.PERSONAL_COGNITIVE_CONTINUITY: "personal",
}

OUTPUTS = {
    ProductSuite.MEDIA_BLITZ: {"publication-package", "distribution-plan"},
    ProductSuite.CAREER_INTELLIGENCE_PLACEMENT: {"opportunity-view", "application-package"},
    ProductSuite.PERSONAL_COGNITIVE_CONTINUITY: {"continuity-view", "reflection-package"},
}


def _boundary(
    suite: ProductSuite,
    *,
    tenant_id: str = "TENANT-1",
    subject_id: str = "PERSON-1",
    execution_context: ExecutionContext = ExecutionContext.TEST,
) -> BoundaryContext:
    return BoundaryContext(
        namespace_id="enki",
        tenant_id=tenant_id,
        subject_id=subject_id,
        domain=DOMAINS[suite],
        audience=EXPECTED_AUDIENCE[suite],
        execution_context=execution_context,
    )


def _contract(suite: ProductSuite) -> ProductConsumerContract:
    return ProductConsumerContract.create(
        contract_id=f"HOSTED-CONTRACT-{suite.value}",
        suite=suite,
        consumer_contract_version="1.0",
        boundary=_boundary(suite),
        authorization_id=f"AUTH-{suite.value}",
        purpose=PURPOSES[suite],
        permitted_output_kinds=OUTPUTS[suite],
    )


def _service() -> tuple[HostedDownstreamConsumerService, NoEffectProductAdapter, dict[ProductSuite, ProductConsumerContract]]:
    contracts = {suite: _contract(suite) for suite in ProductSuite}
    adapter = NoEffectProductAdapter()
    return (
        HostedDownstreamConsumerService(
            registry=ProductBoundaryRegistry(list(contracts.values())),
            delivery_adapter=adapter,
        ),
        adapter,
        contracts,
    )


def _knowledge(
    contract: ProductConsumerContract,
    record_id: str,
    content: str,
    *,
    authority_class: str | None = None,
    disposition: TemporalAuthorityDisposition = TemporalAuthorityDisposition.ACTIVE,
    recorded_at: datetime = T0,
    effective_from: datetime = T0,
    authority_valid_from: datetime = T0,
    authority_valid_to: datetime | None = None,
    superseded_at: datetime | None = None,
    supersedes_record_id: str | None = None,
) -> GovernedKnowledgeRecord:
    envelope = TemporalAuthorityEnvelope(
        record_id=record_id,
        subject_id=contract.boundary.subject_id,
        domain=contract.boundary.domain,
        authority_class=authority_class or f"authority-{record_id}",
        content_hash=canonical_sha256(content),
        schema_version="1",
        recorded_at=recorded_at,
        effective_from=effective_from,
        authority_valid_from=authority_valid_from,
        authority_valid_to=authority_valid_to,
        superseded_at=superseded_at,
        supersedes_record_id=supersedes_record_id,
        disposition=disposition,
    )
    return GovernedKnowledgeRecord(
        envelope=envelope,
        tenant_id=contract.boundary.tenant_id,
        content=content,
        allowed_audiences=frozenset({contract.boundary.audience}),
        allowed_purposes=frozenset({contract.purpose}),
        privacy_class=PrivacyClass.PRIVATE
        if contract.suite == ProductSuite.PERSONAL_COGNITIVE_CONTINUITY
        else PrivacyClass.INTERNAL,
        provenance_ids=(f"PROV-{record_id}",),
    )


def _retrieval(
    contract: ProductConsumerContract,
    *,
    view: RetrievalView = RetrievalView.CURRENT,
    **updates: object,
) -> GovernedRetrievalRequest:
    values: dict[str, object] = {
        "tenant_id": contract.boundary.tenant_id,
        "subject_id": contract.boundary.subject_id,
        "domain": contract.boundary.domain,
        "audience": contract.boundary.audience,
        "purpose": contract.purpose,
        "query": "",
        "mode": RetrievalMode.STRUCTURED,
        "view": view,
        "effective_at": NOW,
        "authority_at": NOW,
        "page_size": 50,
    }
    values.update(updates)
    return GovernedRetrievalRequest(**values)


def _human_control(intent: ConsumerIntent, **policy_updates: bool) -> HumanContinuityControl:
    policy_values = {
        "consent_granted": True,
        "purpose_allowed": True,
        "revoked": False,
        "correction_or_retraction_blocked": False,
    }
    policy_values.update(policy_updates)
    return HumanContinuityControl(
        policy=HumanBoundaryPolicy(**policy_values),
        explicit_human_authority=True,
        privacy_acknowledged=True,
        temporal_authority_acknowledged=True,
        requested_intent=intent,
    )


def test_media_blitz_consumes_governed_projection_and_calibrates_no_effect_feedback() -> None:
    service, _, contracts = _service()
    contract = contracts[ProductSuite.MEDIA_BLITZ]
    record = _knowledge(contract, "MEDIA-1", "Governed article source material")

    execution = service.run(
        suite=ProductSuite.MEDIA_BLITZ,
        intent=ConsumerIntent.MEDIA_PUBLICATION_PROOF,
        records=[record],
        retrieval_request=_retrieval(contract),
        simulated_feedback=("synthetic-click", "synthetic-zero-response"),
        now=NOW,
    )

    assert execution.projection.hits[0].record_id == "MEDIA-1"
    assert execution.package.output_kind == "publication-package"
    assert execution.package.canonical_effect is False
    assert execution.package.external_effect is False
    assert execution.receipt.outcome == "TEST_NO_EFFECT"
    assert execution.calibration_sha256 is not None
    assert execution.package.payload["simulated_feedback"] == [
        "synthetic-click",
        "synthetic-zero-response",
    ]


def test_career_opportunity_view_requires_no_external_effect() -> None:
    service, _, contracts = _service()
    contract = contracts[ProductSuite.CAREER_INTELLIGENCE_PLACEMENT]
    record = _knowledge(contract, "CAREER-1", "Program leadership experience evidence")

    execution = service.run(
        suite=contract.suite,
        intent=ConsumerIntent.CAREER_OPPORTUNITY_VIEW,
        records=[record],
        retrieval_request=_retrieval(contract),
        now=NOW,
    )

    assert execution.package.output_kind == "opportunity-view"
    assert execution.external_action_authorization_id is None
    assert execution.receipt.external_effect is False


def test_career_application_prep_requires_exact_external_action_authority() -> None:
    service, _, contracts = _service()
    contract = contracts[ProductSuite.CAREER_INTELLIGENCE_PLACEMENT]
    record = _knowledge(contract, "CAREER-2", "Role fit evidence")
    request = _retrieval(contract)
    projection = retrieve_governed_knowledge([record], request)
    authorization = ExternalActionAuthorization.create(
        authorization_id="CAREER-ACTION-AUTH-1",
        suite=contract.suite,
        action="prepare-external-application",
        boundary_sha256=contract.boundary.boundary_sha256,
        projection_sha256=projection.projection_hash,
        execution_context=ExecutionContext.TEST,
        authorized_by="HUMAN-TEST-AUTHORITY",
        authorized_at=NOW,
        allowed=True,
    )

    execution = service.run(
        suite=contract.suite,
        intent=ConsumerIntent.CAREER_APPLICATION_PREP,
        records=[record],
        retrieval_request=request,
        external_action_authorization=authorization,
        now=NOW,
    )

    assert execution.external_action_authorization_id == authorization.authorization_id
    assert execution.package.output_kind == "application-package"
    assert execution.receipt.external_effect is False


def test_career_missing_or_mismatched_external_action_authority_fails_closed() -> None:
    service, _, contracts = _service()
    contract = contracts[ProductSuite.CAREER_INTELLIGENCE_PLACEMENT]
    record = _knowledge(contract, "CAREER-3", "Application preparation evidence")
    request = _retrieval(contract)

    with pytest.raises(ProductBoundaryFailure, match="approval is required"):
        service.run(
            suite=contract.suite,
            intent=ConsumerIntent.CAREER_APPLICATION_PREP,
            records=[record],
            retrieval_request=request,
            now=NOW,
        )

    projection = retrieve_governed_knowledge([record], request)
    wrong = ExternalActionAuthorization.create(
        authorization_id="CAREER-ACTION-WRONG",
        suite=contract.suite,
        action="prepare-external-application",
        boundary_sha256=contract.boundary.boundary_sha256,
        projection_sha256="sha256:" + "0" * 64,
        execution_context=ExecutionContext.TEST,
        authorized_by="HUMAN-TEST-AUTHORITY",
        authorized_at=NOW,
        allowed=True,
    )
    assert wrong.projection_sha256 != projection.projection_hash

    with pytest.raises(ProductBoundaryFailure, match="projection mismatch"):
        service.run(
            suite=contract.suite,
            intent=ConsumerIntent.CAREER_APPLICATION_PREP,
            records=[record],
            retrieval_request=request,
            external_action_authorization=wrong,
            now=NOW,
        )


def test_cognitive_continuity_preserves_history_and_stricter_human_controls() -> None:
    service, _, contracts = _service()
    contract = contracts[ProductSuite.PERSONAL_COGNITIVE_CONTINUITY]
    historical = _knowledge(
        contract,
        "PCC-OLD",
        "Historical preference",
        authority_class="preference",
        disposition=TemporalAuthorityDisposition.SUPERSEDED,
        authority_valid_to=T1,
        superseded_at=T1,
    )
    current = _knowledge(
        contract,
        "PCC-NEW",
        "Current preference",
        authority_class="preference",
        recorded_at=T1,
        effective_from=T1,
        authority_valid_from=T1,
        supersedes_record_id="PCC-OLD",
    )

    execution = service.run(
        suite=contract.suite,
        intent=ConsumerIntent.COGNITIVE_CONTINUITY_VIEW,
        records=[historical, current],
        retrieval_request=_retrieval(contract, view=RetrievalView.ALL),
        human_control=_human_control(ConsumerIntent.COGNITIVE_CONTINUITY_VIEW),
        now=NOW,
    )

    assert {hit.record_id for hit in execution.projection.hits} == {"PCC-OLD", "PCC-NEW"}
    assert execution.human_control_applied is True
    assert execution.package.canonical_effect is False


def test_cognitive_correction_and_retraction_are_governed_requests_not_direct_mutations() -> None:
    service, _, contracts = _service()
    contract = contracts[ProductSuite.PERSONAL_COGNITIVE_CONTINUITY]
    record = _knowledge(contract, "PCC-1", "Decision history")

    for intent in (
        ConsumerIntent.COGNITIVE_CORRECTION_REQUEST,
        ConsumerIntent.COGNITIVE_RETRACTION_REQUEST,
    ):
        execution = service.run(
            suite=contract.suite,
            intent=intent,
            records=[record],
            retrieval_request=_retrieval(contract),
            human_control=_human_control(intent),
            now=NOW,
        )
        assert execution.package.output_kind == "reflection-package"
        assert execution.package.payload["intent"] == intent.value
        assert execution.package.canonical_effect is False
        assert execution.receipt.canonical_mutation is False


def test_human_consent_and_revocation_override_generic_tenant_boundary() -> None:
    service, _, contracts = _service()
    contract = contracts[ProductSuite.PERSONAL_COGNITIVE_CONTINUITY]
    record = _knowledge(contract, "PCC-2", "Private continuity state")

    with pytest.raises(ProductBoundaryFailure, match="human continuity controls deny use"):
        service.run(
            suite=contract.suite,
            intent=ConsumerIntent.COGNITIVE_CONTINUITY_VIEW,
            records=[record],
            retrieval_request=_retrieval(contract),
            human_control=_human_control(
                ConsumerIntent.COGNITIVE_CONTINUITY_VIEW,
                consent_granted=False,
            ),
            now=NOW,
        )

    with pytest.raises(ProductBoundaryFailure, match="human continuity controls deny use"):
        service.run(
            suite=contract.suite,
            intent=ConsumerIntent.COGNITIVE_CONTINUITY_VIEW,
            records=[record],
            retrieval_request=_retrieval(contract),
            human_control=_human_control(
                ConsumerIntent.COGNITIVE_CONTINUITY_VIEW,
                revoked=True,
            ),
            now=NOW,
        )


def test_cross_product_scope_and_intent_leakage_fail_closed() -> None:
    service, _, contracts = _service()
    media = contracts[ProductSuite.MEDIA_BLITZ]
    record = _knowledge(media, "MEDIA-2", "Media source")

    for field, value in (
        ("purpose", PURPOSES[ProductSuite.CAREER_INTELLIGENCE_PLACEMENT]),
        ("audience", EXPECTED_AUDIENCE[ProductSuite.CAREER_INTELLIGENCE_PLACEMENT]),
        ("subject_id", "PERSON-OTHER"),
        ("tenant_id", "TENANT-OTHER"),
    ):
        with pytest.raises(ProductBoundaryFailure, match="boundary leakage denied"):
            service.run(
                suite=media.suite,
                intent=ConsumerIntent.MEDIA_PUBLICATION_PROOF,
                records=[record],
                retrieval_request=_retrieval(media, **{field: value}),
                now=NOW,
            )

    with pytest.raises(ProductBoundaryFailure, match="different product suite"):
        service.run(
            suite=media.suite,
            intent=ConsumerIntent.CAREER_OPPORTUNITY_VIEW,
            records=[record],
            retrieval_request=_retrieval(media),
            now=NOW,
        )


def test_exact_product_retry_reuses_no_effect_receipt() -> None:
    service, adapter, contracts = _service()
    contract = contracts[ProductSuite.MEDIA_BLITZ]
    record = _knowledge(contract, "MEDIA-3", "Repeatable source")
    kwargs = {
        "suite": contract.suite,
        "intent": ConsumerIntent.MEDIA_PUBLICATION_PROOF,
        "records": [record],
        "retrieval_request": _retrieval(contract),
        "simulated_feedback": ("zero-response",),
        "now": NOW,
    }

    first = service.run(**kwargs)
    second = service.run(**kwargs)

    assert first.package == second.package
    assert first.receipt == second.receipt
    assert len(adapter.receipts) == 1


def test_product_package_cannot_claim_canonical_or_production_effects() -> None:
    service, _, contracts = _service()
    contract = contracts[ProductSuite.MEDIA_BLITZ]
    execution = service.run(
        suite=contract.suite,
        intent=ConsumerIntent.MEDIA_PUBLICATION_PROOF,
        records=[_knowledge(contract, "MEDIA-4", "No effect")],
        retrieval_request=_retrieval(contract),
        now=NOW,
    )
    payload = execution.package.model_dump(mode="python")

    payload["canonical_effect"] = True
    with pytest.raises(ValidationError):
        ProductPackage.model_validate(payload)

    payload = execution.package.model_dump(mode="python")
    payload["external_effect"] = True
    with pytest.raises(ValidationError):
        ProductPackage.model_validate(payload)


SPRINT33_TESTED_PATHS = {
    "media-governed-source-retrieval",
    "media-publication-shaped-no-effect",
    "media-feedback-calibration",
    "career-professional-state-retrieval",
    "career-opportunity-projection",
    "career-external-action-approved-test-path",
    "cognitive-history-retrieval",
    "cognitive-correction-request",
    "cognitive-retraction-request",
    "human-controls-stricter-than-tenant",
    "exact-product-retry-no-effect",
    "cross-product-purpose-denied",
    "cross-product-audience-denied",
    "cross-product-subject-denied",
    "cross-product-tenant-denied",
    "cross-product-intent-denied",
    "career-missing-external-action-approval-denied",
    "career-mismatched-external-action-approval-denied",
    "human-consent-denied",
    "human-revocation-denied",
    "direct-canonical-product-output-denied",
    "production-effect-denied",
}


def test_every_declared_sprint33_path_has_automated_coverage() -> None:
    sprint33_hosted_downstream_path_manifest().assert_complete_coverage(SPRINT33_TESTED_PATHS)


def test_sprint33_paths_are_test_only_and_preserve_product_boundaries() -> None:
    manifest = sprint33_hosted_downstream_path_manifest()
    assert manifest.execution_context == ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "direct-canonical-write" in path.prohibited_effects
        assert "cross-product-leakage" in path.prohibited_effects
        assert "authority-reuse" in path.prohibited_effects
        assert "human-agency-bypass" in path.prohibited_effects
