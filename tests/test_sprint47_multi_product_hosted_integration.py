from __future__ import annotations

from datetime import datetime, timezone

import pytest

from nks.application.hosted_downstream_integration import (
    HostedIntegrationError,
    ProductConsumer,
)
from nks.application.hosted_platform_operations import (
    HostedOperation,
    HostedPlatformError,
    OperationStatus,
)
from nks.application.multi_product_hosted_integration import (
    MultiProductHostedIntegration,
    MultiProductIntegrationError,
    MultiProductOperationSpec,
)
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryContext, HumanBoundaryPolicy


NOW = datetime(2026, 7, 18, 2, 0, tzinfo=timezone.utc)


def media_spec(operation_id: str = "OP-MEDIA") -> MultiProductOperationSpec:
    return MultiProductOperationSpec(
        operation_id=operation_id,
        product=ProductConsumer.MEDIA_BLITZ,
        tenant_id="TENANT-MEDIA",
        subject_id="SUBJECT-PUBLICATION-1",
        subject_type="PUBLICATION",
        domain="publication-corpus",
        purpose="publication-planning",
        state_payload={"status": "draft", "title": "Governed article"},
        provenance_ids=("PROV-MEDIA-1",),
        data_classification="INTERNAL",
        submitted_at=NOW,
    )


def career_spec(operation_id: str = "OP-CAREER") -> MultiProductOperationSpec:
    return MultiProductOperationSpec(
        operation_id=operation_id,
        product=ProductConsumer.CAREER_INTELLIGENCE,
        tenant_id="TENANT-CAREER",
        subject_id="SUBJECT-PROFILE-1",
        subject_type="PROFILE",
        domain="career-profile",
        purpose="career-assistance",
        state_payload={"role": "Enterprise Architect", "status": "active"},
        provenance_ids=("PROV-CAREER-1",),
        data_classification="INTERNAL",
        submitted_at=NOW,
    )


def personal_spec(
    operation_id: str = "OP-PERSONAL",
    *,
    human_policy: HumanBoundaryPolicy | None = None,
) -> MultiProductOperationSpec:
    return MultiProductOperationSpec(
        operation_id=operation_id,
        product=ProductConsumer.PERSONAL_COGNITIVE_CONTINUITY,
        tenant_id="TENANT-PERSONAL",
        subject_id="SUBJECT-PERSON-1",
        subject_type="PERSON",
        domain="personal-profile",
        purpose="personal-continuity",
        state_payload={"preference": "quiet", "confidence": "high"},
        provenance_ids=("PROV-PERSONAL-1",),
        data_classification="RESTRICTED",
        submitted_at=NOW,
        human_policy=human_policy,
    )


def consent_policy() -> HumanBoundaryPolicy:
    return HumanBoundaryPolicy(consent_granted=True, purpose_allowed=True)


def execute_all(integration: MultiProductHostedIntegration):
    media = integration.execute(media_spec())
    career = integration.execute(career_spec())
    personal = integration.execute(personal_spec(human_policy=consent_policy()))
    return media, career, personal


def test_all_three_products_execute_through_shared_hosted_contracts_and_report_lineage():
    integration = MultiProductHostedIntegration()

    media, career, personal = execute_all(integration)
    report = integration.report(run_id="RUN-47-ALL")

    assert {result.product for result in report.results} == {
        ProductConsumer.MEDIA_BLITZ,
        ProductConsumer.CAREER_INTELLIGENCE,
        ProductConsumer.PERSONAL_COGNITIVE_CONTINUITY,
    }
    assert {lineage.product for lineage in report.lineages} == set(report.products)
    assert media.state_id in integration.consumers[ProductConsumer.MEDIA_BLITZ].reconstruct(media.state_id).state_id
    assert career.state_id == integration.consumers[ProductConsumer.CAREER_INTELLIGENCE].reconstruct(career.state_id).state_id
    assert personal.state_id == integration.consumers[ProductConsumer.PERSONAL_COGNITIVE_CONTINUITY].reconstruct(personal.state_id).state_id
    assert all(lineage.state_ids for lineage in report.lineages)
    assert all(lineage.provenance_ids for lineage in report.lineages)
    assert all(lineage.transaction_ids for lineage in report.lineages)
    assert report.provider_effects == 0
    assert report.external_effects == 0
    assert report.report_sha256.startswith("sha256:")


def test_cross_product_domain_and_purpose_leakage_fail_before_state_effect():
    integration = MultiProductHostedIntegration()
    wrong_domain = media_spec("OP-WRONG-DOMAIN").model_copy(
        update={"domain": "personal-profile"}
    )
    wrong_purpose = career_spec("OP-WRONG-PURPOSE").model_copy(
        update={"purpose": "personal-continuity"}
    )

    with pytest.raises(MultiProductIntegrationError, match="domain"):
        integration.execute(wrong_domain)
    with pytest.raises(MultiProductIntegrationError, match="purpose"):
        integration.execute(wrong_purpose)

    assert integration.state_store.all_states() == ()
    assert integration.platform_runtime.operation_receipts() == ()


def test_product_tenants_and_state_lineage_remain_isolated():
    integration = MultiProductHostedIntegration()
    media, career, personal = execute_all(integration)

    assert integration.state_store.get("TENANT-MEDIA", media.state_id) is not None
    assert integration.state_store.get("TENANT-CAREER", media.state_id) is None
    assert integration.state_store.get("TENANT-PERSONAL", career.state_id) is None
    assert integration.state_store.get("TENANT-MEDIA", personal.state_id) is None

    media_reconstruction = integration.consumers[ProductConsumer.MEDIA_BLITZ].reconstruct(media.state_id)
    career_reconstruction = integration.consumers[ProductConsumer.CAREER_INTELLIGENCE].reconstruct(career.state_id)
    personal_reconstruction = integration.consumers[ProductConsumer.PERSONAL_COGNITIVE_CONTINUITY].reconstruct(personal.state_id)
    assert media_reconstruction.provenance_ids == ("PROV-MEDIA-1",)
    assert career_reconstruction.provenance_ids == ("PROV-CAREER-1",)
    assert personal_reconstruction.provenance_ids == ("PROV-PERSONAL-1",)


def test_per_consumer_and_global_contention_are_bounded_across_products():
    integration = MultiProductHostedIntegration(global_active_limit=2, default_consumer_active_limit=1)
    boundary = BoundaryContext(
        namespace_id="NKS-HOSTED-INTEGRATION-TEST",
        tenant_id="TENANT-MEDIA",
        subject_id="SUBJECT-PUBLICATION-1",
        domain="publication-corpus",
        audience="internal",
        execution_context=ExecutionContext.TEST,
    )
    media_one = HostedOperation(
        operation_id="ACTIVE-MEDIA-1",
        consumer_id=ProductConsumer.MEDIA_BLITZ.value,
        purpose="publication-planning",
        boundary_context=boundary,
        operation_type="state.create",
        payload_hash=media_spec().payload_sha256,
        submitted_at=NOW,
        data_classification="INTERNAL",
    )
    media_two = media_one.model_copy(update={"operation_id": "ACTIVE-MEDIA-2"})
    career = HostedOperation(
        operation_id="ACTIVE-CAREER-1",
        consumer_id=ProductConsumer.CAREER_INTELLIGENCE.value,
        purpose="career-assistance",
        boundary_context=boundary.model_copy(
            update={
                "tenant_id": "TENANT-CAREER",
                "subject_id": "SUBJECT-PROFILE-1",
                "domain": "career-profile",
            }
        ),
        operation_type="state.create",
        payload_hash=career_spec().payload_sha256,
        submitted_at=NOW,
        data_classification="INTERNAL",
    )
    personal = HostedOperation(
        operation_id="ACTIVE-PERSONAL-1",
        consumer_id=ProductConsumer.PERSONAL_COGNITIVE_CONTINUITY.value,
        purpose="personal-continuity",
        boundary_context=boundary.model_copy(
            update={
                "tenant_id": "TENANT-PERSONAL",
                "subject_id": "SUBJECT-PERSON-1",
                "domain": "personal-profile",
            }
        ),
        operation_type="state.create",
        payload_hash=personal_spec().payload_sha256,
        submitted_at=NOW,
        data_classification="RESTRICTED",
        contains_raw_sensitive_fields=True,
    )

    integration.platform_runtime.begin_operation(media_one)
    with pytest.raises(HostedPlatformError, match="consumer is saturated"):
        integration.platform_runtime.begin_operation(media_two)
    integration.platform_runtime.begin_operation(career)
    with pytest.raises(HostedPlatformError, match="platform is saturated"):
        integration.platform_runtime.begin_operation(personal)

    integration.platform_runtime.fail_operation(
        media_one.operation_id,
        reason="release",
        occurred_at=NOW,
    )
    integration.platform_runtime.fail_operation(
        career.operation_id,
        reason="release",
        occurred_at=NOW,
    )
    assert integration.platform_runtime.active_operation_ids() == ()


def test_product_failure_creates_incident_then_retry_and_exact_replay_converge():
    integration = MultiProductHostedIntegration()
    spec = career_spec("OP-CAREER-FAIL-RETRY")

    with pytest.raises(RuntimeError, match="injected product integration failure"):
        integration.execute(spec, inject_failure=True)

    incidents = integration.incidents()
    assert len(incidents) == 1
    assert incidents[0].consumer_id == ProductConsumer.CAREER_INTELLIGENCE.value
    assert incidents[0].error_type == "RuntimeError"
    assert "injected" not in incidents[0].error_fingerprint

    recovered = integration.execute(spec)
    replay = integration.exact_replay(spec)

    assert recovered.replayed is False
    assert replay.replayed is True
    assert replay.state_id == recovered.state_id
    assert integration.state_store.all_states().__len__() == 1
    assert integration.receipt_store.all_receipts().__len__() == 1


def test_personal_cognitive_continuity_remains_stricter_during_integrated_failure_and_retry():
    integration = MultiProductHostedIntegration()
    denied = personal_spec("OP-PERSONAL-POLICY")

    with pytest.raises(HostedIntegrationError, match="human policy is required"):
        integration.execute(denied)

    assert len(integration.incidents()) == 1
    assert integration.state_store.all_states() == ()

    permitted = personal_spec(
        "OP-PERSONAL-POLICY",
        human_policy=consent_policy(),
    )
    result = integration.execute(permitted)

    assert result.product == ProductConsumer.PERSONAL_COGNITIVE_CONTINUITY
    assert result.state_id.startswith("STATE-")
    assert integration.state_store.get("TENANT-PERSONAL", result.state_id) is not None


def test_integrated_telemetry_is_privacy_preserving_and_product_kpis_are_stable():
    integration = MultiProductHostedIntegration()
    execute_all(integration)

    telemetry = integration.platform_runtime.telemetry_events()
    summary = integration.platform_runtime.telemetry_summary()

    assert len(telemetry) == 3
    assert all(event.raw_sensitive_fields_persisted is False for event in telemetry)
    assert all(event.boundary_hash.startswith("sha256:") for event in telemetry)
    assert summary.completed_operations == 3
    assert summary.failed_operations == 0
    assert summary.telemetry_events == 3
    assert summary.incidents == 0
    assert set(integration.platform_runtime.consumer_operation_counts()) == {
        ProductConsumer.MEDIA_BLITZ.value,
        ProductConsumer.CAREER_INTELLIGENCE.value,
        ProductConsumer.PERSONAL_COGNITIVE_CONTINUITY.value,
    }


def test_shared_platform_export_and_recovery_preserve_integrated_operation_evidence():
    integration = MultiProductHostedIntegration()
    execute_all(integration)
    exported = integration.export_platform_state()
    recovered = integration.recover_platform_runtime()

    assert recovered.export_state() == exported
    assert recovered.operation_receipts() == integration.platform_runtime.operation_receipts()
    assert recovered.telemetry_events() == integration.platform_runtime.telemetry_events()
    assert recovered.incidents() == integration.platform_runtime.incidents()
    assert recovered.active_operation_ids() == ()


def test_integrated_report_is_deterministic_and_contains_no_missing_product_lineage():
    integration = MultiProductHostedIntegration()
    execute_all(integration)

    first = integration.report(run_id="RUN-DETERMINISTIC")
    second = integration.report(run_id="RUN-DETERMINISTIC")

    assert first == second
    assert first.report_sha256 == second.report_sha256
    assert len(first.lineages) == 3
    for lineage in first.lineages:
        assert len(lineage.state_ids) >= 1
        assert len(lineage.state_hashes) == len(lineage.state_ids)
        assert len(lineage.reconstruction_hashes) == len(lineage.state_ids)
        assert lineage.lineage_sha256.startswith("sha256:")


def test_integrated_report_includes_product_specific_incident_after_recovery():
    integration = MultiProductHostedIntegration()
    integration.execute(media_spec())
    failed = career_spec("OP-CAREER-INCIDENT")
    with pytest.raises(RuntimeError):
        integration.execute(failed, inject_failure=True)
    integration.execute(failed)
    integration.execute(personal_spec(human_policy=consent_policy()))

    report = integration.report(run_id="RUN-WITH-INCIDENT")

    assert len(report.incident_ids) == 1
    assert report.incident_ids[0].startswith("INCIDENT-")
    assert set(report.products) == {
        ProductConsumer.MEDIA_BLITZ,
        ProductConsumer.CAREER_INTELLIGENCE,
        ProductConsumer.PERSONAL_COGNITIVE_CONTINUITY,
    }
