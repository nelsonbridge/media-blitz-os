from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from nks.application.consumer_adapters import ConsumerApiAdapter
from nks.application.consumer_contracts import ConsumerOperation
from nks.application.consumer_service import (
    ConsumerGateway,
    DeterministicConsumerApplicationService,
)
from nks.application.downstream_products import (
    EXPECTED_AUDIENCE,
    DownstreamProductProofService,
    NoEffectProductAdapter,
    ProductBoundaryFailure,
    ProductBoundaryRegistry,
    ProductConsumerContract,
    ProductSuite,
    downstream_contract_fixture,
)
from nks.application.sprint22_path_manifest import sprint22_downstream_path_manifest
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import (
    BoundaryAction,
    BoundaryAuthorization,
    BoundaryContext,
)


NOW = datetime(2026, 7, 15, 7, 0, tzinfo=timezone.utc)


OUTPUTS = {
    ProductSuite.MEDIA_BLITZ: {"publication-package", "distribution-plan"},
    ProductSuite.CAREER_INTELLIGENCE_PLACEMENT: {
        "opportunity-view",
        "application-package",
    },
    ProductSuite.PERSONAL_COGNITIVE_CONTINUITY: {
        "continuity-view",
        "reflection-package",
    },
}


PRIMARY_OUTPUT = {
    ProductSuite.MEDIA_BLITZ: "publication-package",
    ProductSuite.CAREER_INTELLIGENCE_PLACEMENT: "opportunity-view",
    ProductSuite.PERSONAL_COGNITIVE_CONTINUITY: "continuity-view",
}


def make_boundary(
    suite: ProductSuite,
    *,
    execution_context: ExecutionContext = ExecutionContext.TEST,
) -> BoundaryContext:
    return BoundaryContext(
        namespace_id="enki",
        tenant_id="tenant-downstream",
        subject_id="subject-downstream",
        domain="knowledge",
        audience=EXPECTED_AUDIENCE[suite],
        execution_context=execution_context,
    )


def make_contract(
    suite: ProductSuite,
    *,
    authorization_id: str | None = None,
    execution_context: ExecutionContext = ExecutionContext.TEST,
) -> ProductConsumerContract:
    return ProductConsumerContract.create(
        contract_id=f"PRODUCT-CONTRACT-{suite.value}",
        suite=suite,
        consumer_contract_version="1.0",
        boundary=make_boundary(suite, execution_context=execution_context),
        authorization_id=authorization_id or f"AUTH-{suite.value}",
        purpose=f"test-proof-{suite.value.lower()}",
        permitted_output_kinds=OUTPUTS[suite],
    )


def make_authorization(contract: ProductConsumerContract) -> BoundaryAuthorization:
    return BoundaryAuthorization(
        authorization_id=contract.authorization_id,
        boundary=contract.boundary,
        permitted_actions={BoundaryAction.READ},
        authority_class=f"downstream-{contract.suite.value.lower()}",
        issued_at=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(hours=1),
    )


def build_proof_service(
    contracts: list[ProductConsumerContract],
) -> tuple[DownstreamProductProofService, NoEffectProductAdapter]:
    authorizations = {
        contract.authorization_id: make_authorization(contract) for contract in contracts
    }
    application = DeterministicConsumerApplicationService()
    gateway = ConsumerGateway(
        authorizations=authorizations,
        services={
            ConsumerOperation.QUERY: application,
            ConsumerOperation.COMMAND: application,
        },
    )
    adapter = NoEffectProductAdapter()
    return (
        DownstreamProductProofService(
            registry=ProductBoundaryRegistry(contracts),
            consumer_api=ConsumerApiAdapter(gateway),
            adapter=adapter,
        ),
        adapter,
    )


def make_request(
    contract: ProductConsumerContract,
    *,
    product_scope: ProductSuite | None = None,
    boundary: BoundaryContext | None = None,
    authorization_id: str | None = None,
    payload_extra: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "product_scope": (product_scope or contract.suite).value,
        "items": [
            {
                "id": f"ITEM-{contract.suite.value}",
                "value": "synthetic-test-value",
            }
        ],
    }
    if payload_extra:
        payload.update(payload_extra)
    return {
        "request_id": f"REQ-{contract.suite.value}",
        "contract_version": "1.0",
        "operation": "QUERY",
        "boundary": (boundary or contract.boundary).model_dump(mode="json"),
        "authorization_id": authorization_id or contract.authorization_id,
        "idempotency_key": f"idem-{contract.suite.value}",
        "payload": payload,
        "pagination": {"page_size": 10, "cursor": None},
    }


@pytest.mark.parametrize("suite", list(ProductSuite))
def test_each_downstream_suite_completes_end_to_end_no_effect_proof(
    suite: ProductSuite,
) -> None:
    contracts = [make_contract(item) for item in ProductSuite]
    service, adapter = build_proof_service(contracts)
    contract = next(item for item in contracts if item.suite == suite)

    package, receipt = service.run(
        suite=suite,
        consumer_request=make_request(contract),
        output_kind=PRIMARY_OUTPUT[suite],
        provenance_refs=["SOURCE-TEST-001"],
        context_refs=["CONTEXT-TEST-001"],
        privacy_labels=["synthetic", "internal"],
        now=NOW,
    )

    assert package.suite == suite
    assert package.boundary == contract.boundary
    assert package.provenance_refs == ["SOURCE-TEST-001"]
    assert package.context_refs == ["CONTEXT-TEST-001"]
    assert package.privacy_labels == ["synthetic", "internal"]
    assert package.authority_ref == contract.authorization_id
    assert package.canonical_effect is False
    assert package.external_effect is False
    assert receipt.outcome == "TEST_NO_EFFECT"
    assert receipt.canonical_mutation is False
    assert receipt.external_effect is False
    assert adapter.receipts[package.package_id] == receipt


def test_exact_product_package_retry_reuses_no_effect_receipt() -> None:
    contract = make_contract(ProductSuite.MEDIA_BLITZ)
    service, adapter = build_proof_service([contract])
    kwargs = {
        "suite": contract.suite,
        "consumer_request": make_request(contract),
        "output_kind": "publication-package",
        "provenance_refs": ["SOURCE-TEST-001"],
        "context_refs": ["CONTEXT-TEST-001"],
        "privacy_labels": ["synthetic"],
        "now": NOW,
    }

    first_package, first_receipt = service.run(**kwargs)
    second_package, second_receipt = service.run(**kwargs)

    assert second_package == first_package
    assert second_receipt == first_receipt
    assert len(adapter.receipts) == 1


def test_cross_product_authority_reuse_fails_closed() -> None:
    shared = "AUTH-SHARED-DENIED"
    media = make_contract(ProductSuite.MEDIA_BLITZ, authorization_id=shared)
    career = make_contract(
        ProductSuite.CAREER_INTELLIGENCE_PLACEMENT,
        authorization_id=shared,
    )

    with pytest.raises(ProductBoundaryFailure, match="authority reuse"):
        ProductBoundaryRegistry([media, career])


def test_cross_product_data_leakage_and_audience_widening_fail_closed() -> None:
    media = make_contract(ProductSuite.MEDIA_BLITZ)
    career = make_contract(ProductSuite.CAREER_INTELLIGENCE_PLACEMENT)
    service, _ = build_proof_service([media, career])

    leaked = make_request(
        media,
        product_scope=ProductSuite.CAREER_INTELLIGENCE_PLACEMENT,
    )
    widened = make_request(media, boundary=career.boundary)

    with pytest.raises(ProductBoundaryFailure, match="data leakage"):
        service.run(
            suite=media.suite,
            consumer_request=leaked,
            output_kind="publication-package",
            provenance_refs=["SOURCE-1"],
            context_refs=["CTX-1"],
            privacy_labels=[],
            now=NOW,
        )
    with pytest.raises(ProductBoundaryFailure, match="audience widening"):
        service.run(
            suite=media.suite,
            consumer_request=widened,
            output_kind="publication-package",
            provenance_refs=["SOURCE-1"],
            context_refs=["CTX-1"],
            privacy_labels=[],
            now=NOW,
        )


def test_authority_reuse_and_direct_canonical_product_output_fail_closed() -> None:
    media = make_contract(ProductSuite.MEDIA_BLITZ)
    career = make_contract(ProductSuite.CAREER_INTELLIGENCE_PLACEMENT)
    service, _ = build_proof_service([media, career])

    reused_authority = make_request(
        media,
        authorization_id=career.authorization_id,
    )
    canonical_intent = make_request(
        media,
        payload_extra={"recommendation_to_canonical": {"value": "never"}},
    )

    with pytest.raises(ProductBoundaryFailure, match="authority reuse"):
        service.run(
            suite=media.suite,
            consumer_request=reused_authority,
            output_kind="publication-package",
            provenance_refs=["SOURCE-1"],
            context_refs=["CTX-1"],
            privacy_labels=[],
            now=NOW,
        )
    with pytest.raises(ProductBoundaryFailure, match="direct canonical mutation"):
        service.run(
            suite=media.suite,
            consumer_request=canonical_intent,
            output_kind="publication-package",
            provenance_refs=["SOURCE-1"],
            context_refs=["CTX-1"],
            privacy_labels=[],
            now=NOW,
        )


def test_unpermitted_output_and_production_contract_fail_closed() -> None:
    media = make_contract(ProductSuite.MEDIA_BLITZ)
    service, _ = build_proof_service([media])

    with pytest.raises(ProductBoundaryFailure, match="outside product contract"):
        service.run(
            suite=media.suite,
            consumer_request=make_request(media),
            output_kind="career-recommendation",
            provenance_refs=["SOURCE-1"],
            context_refs=["CTX-1"],
            privacy_labels=[],
            now=NOW,
        )

    with pytest.raises(ValidationError, match="TEST-only"):
        make_contract(
            ProductSuite.MEDIA_BLITZ,
            execution_context=ExecutionContext.PRODUCTION,
        )


def test_downstream_contract_fixture_is_deterministic() -> None:
    root = Path(__file__).resolve().parents[1]
    committed = json.loads(
        (root / "contracts" / "downstream-product-boundaries-v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert committed == downstream_contract_fixture()


SPRINT22_TESTED_PATHS = {
    "media-blitz-end-to-end-no-effect",
    "career-intelligence-end-to-end-no-effect",
    "cognitive-continuity-end-to-end-no-effect",
    "provenance-context-privacy-authority-preserved",
    "exact-package-retry-no-effect",
    "cross-product-data-leakage-denied",
    "cross-product-authority-reuse-denied",
    "audience-widening-denied",
    "direct-canonical-product-output-denied",
    "unpermitted-output-kind-denied",
    "production-context-denied",
}


def test_every_declared_sprint22_path_has_automated_coverage() -> None:
    sprint22_downstream_path_manifest().assert_complete_coverage(SPRINT22_TESTED_PATHS)


def test_sprint22_paths_are_test_only_and_prohibit_boundary_escape() -> None:
    manifest = sprint22_downstream_path_manifest()
    assert manifest.execution_context == ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "direct-canonical-write" in path.prohibited_effects
        assert "direct-approval-consumption" in path.prohibited_effects
        assert "cross-product-leakage" in path.prohibited_effects
        assert "authority-reuse" in path.prohibited_effects
        assert "audience-widening" in path.prohibited_effects
