from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from nks.application.enki_model_use_policy import model_use_context_sha256
from nks.application.governed_transactions import canonical_sha256
from nks.application.sprint32_path_manifest import sprint32_retrieval_model_gateway_path_manifest
from nks.enki.contracts import ConfidenceAssertion, ConfidenceLevel, SubjectRef
from nks.enki.governed_retrieval import (
    GovernedKnowledgeRecord,
    GovernedRetrievalRequest,
    KnowledgeProjection,
    PrivacyClass,
    RetrievalMode,
    RetrievalView,
    StaleKnowledgeStateError,
    retrieve_governed_knowledge,
)
from nks.enki.model_gateway import (
    DeterministicNoEffectModelProvider,
    ModelGatewayExecutionRequest,
    ModelGatewayOutput,
    ModelGatewayProviderResponse,
    ModelGatewayReplayStore,
    execute_model_gateway,
)
from nks.enki.model_use_contracts import (
    EnkiModelUseDirective,
    EnkiModelUseItem,
    EnkiModelUseRequest,
    ModelUseAudience,
    ModelUseConsentState,
    ModelUseDirectiveAction,
    ModelUseItemKind,
    ModelUseSensitivity,
    ModelUseTemporalState,
)
from nks.enki.temporal_authority import (
    TemporalAuthorityDisposition,
    TemporalAuthorityEnvelope,
)
from nks.governance.approvals import ExecutionContext


T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
T1 = datetime(2026, 2, 1, tzinfo=timezone.utc)
T2 = datetime(2026, 3, 1, tzinfo=timezone.utc)
SUBJECT = SubjectRef(subject_id="PERSON-1", subject_type="PERSON")


def _knowledge(
    record_id: str,
    content: str,
    *,
    tenant_id: str = "TENANT-1",
    subject_id: str = "PERSON-1",
    domain: str = "career",
    authority_class: str | None = None,
    disposition: TemporalAuthorityDisposition = TemporalAuthorityDisposition.ACTIVE,
    recorded_at: datetime = T0,
    effective_from: datetime = T0,
    authority_valid_from: datetime = T0,
    authority_valid_to: datetime | None = None,
    superseded_at: datetime | None = None,
    supersedes_record_id: str | None = None,
    audiences: frozenset[str] = frozenset({"assistant"}),
    purposes: frozenset[str] = frozenset({"career-assistance"}),
    privacy_class: PrivacyClass = PrivacyClass.INTERNAL,
) -> GovernedKnowledgeRecord:
    envelope = TemporalAuthorityEnvelope(
        record_id=record_id,
        subject_id=subject_id,
        domain=domain,
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
        tenant_id=tenant_id,
        content=content,
        allowed_audiences=audiences,
        allowed_purposes=purposes,
        privacy_class=privacy_class,
        provenance_ids=(f"PROV-{record_id}",),
    )


def _retrieval_request(**updates: object) -> GovernedRetrievalRequest:
    values: dict[str, object] = {
        "tenant_id": "TENANT-1",
        "subject_id": "PERSON-1",
        "domain": "career",
        "audience": "assistant",
        "purpose": "career-assistance",
        "query": "",
        "mode": RetrievalMode.STRUCTURED,
        "view": RetrievalView.CURRENT,
        "effective_at": T2,
        "authority_at": T2,
        "page_size": 50,
    }
    values.update(updates)
    return GovernedRetrievalRequest(**values)


def test_current_and_historical_views_are_explicit_and_distinguishable() -> None:
    historical = _knowledge(
        "R1",
        "Previous operating model",
        authority_class="operating-model",
        disposition=TemporalAuthorityDisposition.SUPERSEDED,
        authority_valid_to=T1,
        superseded_at=T1,
    )
    current = _knowledge(
        "R2",
        "Current operating model",
        authority_class="operating-model",
        recorded_at=T1,
        effective_from=T1,
        authority_valid_from=T1,
        supersedes_record_id="R1",
    )

    current_view = retrieve_governed_knowledge(
        [historical, current], _retrieval_request(view=RetrievalView.CURRENT)
    )
    historical_view = retrieve_governed_knowledge(
        [historical, current], _retrieval_request(view=RetrievalView.HISTORICAL)
    )

    assert [hit.record_id for hit in current_view.hits] == ["R2"]
    assert [hit.record_id for hit in historical_view.hits] == ["R1"]
    assert current_view.hits[0].is_current_authority is True
    assert historical_view.hits[0].is_current_authority is False
    assert current_view.canonical is False
    assert historical_view.canonical is False


def test_structured_and_semantic_retrieval_are_deterministic() -> None:
    records = [
        _knowledge("R-A", "Enterprise architecture and governed knowledge"),
        _knowledge("R-B", "Career profile and opportunity intelligence"),
    ]
    structured = retrieve_governed_knowledge(
        records,
        _retrieval_request(query="opportunity", mode=RetrievalMode.STRUCTURED),
    )
    semantic_first = retrieve_governed_knowledge(
        records,
        _retrieval_request(query="governed architecture", mode=RetrievalMode.SEMANTIC),
    )
    semantic_second = retrieve_governed_knowledge(
        list(reversed(records)),
        _retrieval_request(query="governed architecture", mode=RetrievalMode.SEMANTIC),
    )

    assert [hit.record_id for hit in structured.hits] == ["R-B"]
    assert [hit.record_id for hit in semantic_first.hits] == ["R-A"]
    assert semantic_first == semantic_second


def test_tenant_and_subject_boundaries_cannot_leak_or_influence_timeline() -> None:
    allowed = _knowledge("R1", "Allowed tenant content")
    other_tenant = _knowledge("R2", "Secret other tenant content", tenant_id="TENANT-2")
    other_subject = _knowledge("R3", "Secret other subject content", subject_id="PERSON-2")

    result = retrieve_governed_knowledge(
        [allowed, other_tenant, other_subject], _retrieval_request(view=RetrievalView.ALL)
    )
    baseline = retrieve_governed_knowledge(
        [allowed], _retrieval_request(view=RetrievalView.ALL)
    )

    assert [hit.record_id for hit in result.hits] == ["R1"]
    assert result.timeline_hash == baseline.timeline_hash
    assert result.projection_hash == baseline.projection_hash


def test_audience_purpose_and_restricted_privacy_are_withheld() -> None:
    audience_denied = _knowledge("A", "Audience denied", audiences=frozenset({"other"}))
    purpose_denied = _knowledge("P", "Purpose denied", purposes=frozenset({"other"}))
    restricted = _knowledge("X", "Restricted", privacy_class=PrivacyClass.RESTRICTED)

    result = retrieve_governed_knowledge(
        [audience_denied, purpose_denied, restricted],
        _retrieval_request(view=RetrievalView.ALL),
    )

    assert result.hits == ()
    assert result.withheld_count == 3


def test_pagination_is_stable_and_stale_cursors_fail_closed() -> None:
    records = [_knowledge("R1", "one"), _knowledge("R2", "two"), _knowledge("R3", "three")]
    first = retrieve_governed_knowledge(records, _retrieval_request(page_size=1))
    assert [hit.record_id for hit in first.hits] == ["R1"]
    assert first.next_cursor is not None

    second = retrieve_governed_knowledge(
        records,
        _retrieval_request(page_size=1, cursor=first.next_cursor),
    )
    assert [hit.record_id for hit in second.hits] == ["R2"]

    with pytest.raises(StaleKnowledgeStateError, match="cursor does not match"):
        retrieve_governed_knowledge(records, _retrieval_request(cursor="sha256:" + "0" * 64 + ":1"))


def test_stale_expected_timeline_hash_fails_closed() -> None:
    with pytest.raises(StaleKnowledgeStateError, match="timeline hash is stale"):
        retrieve_governed_knowledge(
            [_knowledge("R1", "current")],
            _retrieval_request(expected_timeline_hash="sha256:" + "0" * 64),
        )


def test_projection_cannot_claim_canonical_authority() -> None:
    result = retrieve_governed_knowledge([_knowledge("R1", "current")], _retrieval_request())
    payload = result.model_dump(mode="python")
    payload["canonical"] = True

    with pytest.raises(ValidationError, match="cannot be canonical"):
        KnowledgeProjection.model_validate(payload)


def _confidence() -> ConfidenceAssertion:
    return ConfidenceAssertion(
        level=ConfidenceLevel.HIGH,
        rationale="High-confidence TEST fixture.",
        evidence_ids=["EVIDENCE-1"],
    )


def _model_item(
    *, sensitivity: ModelUseSensitivity = ModelUseSensitivity.PUBLIC
) -> EnkiModelUseItem:
    return EnkiModelUseItem(
        item_id="ITEM-1",
        item_kind=ModelUseItemKind.FINDING,
        subject=SUBJECT,
        domain="career",
        content_sha256=canonical_sha256("finding"),
        context=["current-role"],
        temporal_state=ModelUseTemporalState.CURRENT,
        confidence=_confidence(),
        sensitivity=sensitivity,
        consent_state=ModelUseConsentState.GRANTED,
        allowed_purposes={"career-assistance"},
        provenance_classification="SYNTHETIC/TEST",
    )


def _model_directive(item: EnkiModelUseItem) -> EnkiModelUseDirective:
    return EnkiModelUseDirective(
        directive_id="DIR-1",
        action=ModelUseDirectiveAction.INCLUDE,
        item_id=item.item_id,
        item_kind=item.item_kind,
        subject=item.subject,
        domain=item.domain,
        purpose="career-assistance",
        audience=ModelUseAudience.INTERNAL_MODEL,
        required_context={"current-role"},
        rationale="TEST-authorized exact model-use directive.",
        issued_by="PERSON-1",
        authority_class="SUBJECT",
        issued_at=T1 - timedelta(minutes=5),
    )


def _model_request(
    *, sensitivity: ModelUseSensitivity = ModelUseSensitivity.PUBLIC
) -> EnkiModelUseRequest:
    item = _model_item(sensitivity=sensitivity)
    return EnkiModelUseRequest(
        package_id="PKG-1",
        subject=SUBJECT,
        domain="career",
        purpose="career-assistance",
        audience=ModelUseAudience.INTERNAL_MODEL,
        context={"current-role"},
        execution_context=ExecutionContext.TEST,
        items=[item],
        directives=[_model_directive(item)],
        requested_at=T1,
        package_version="enki-model-use/v1",
    )


def _gateway_request(model_request: EnkiModelUseRequest) -> ModelGatewayExecutionRequest:
    return ModelGatewayExecutionRequest(
        gateway_request_id="GW-1",
        model_use_request=model_request,
        expected_context_sha256=model_use_context_sha256(model_request),
        requested_at=model_request.requested_at,
    )


def test_provider_neutral_model_gateway_is_receipted_noncanonical_and_replayable() -> None:
    request = _gateway_request(_model_request())
    store = ModelGatewayReplayStore()
    provider = DeterministicNoEffectModelProvider()

    first = execute_model_gateway(request, provider=provider, replay_store=store)
    second = execute_model_gateway(request, provider=provider, replay_store=store)

    assert first.package.included_items[0].item_id == "ITEM-1"
    assert first.output.canonical is False
    assert first.receipt.canonical_mutation is False
    assert first.receipt.external_effect is False
    assert first.receipt.provider_id == provider.provider_id
    assert first.replayed is False
    assert second.replayed is True
    assert second.receipt == first.receipt
    assert second.output == first.output


def test_policy_filtered_model_package_withholds_restricted_item() -> None:
    execution = execute_model_gateway(
        _gateway_request(_model_request(sensitivity=ModelUseSensitivity.RESTRICTED)),
        provider=DeterministicNoEffectModelProvider(),
        replay_store=ModelGatewayReplayStore(),
    )

    assert execution.package.included_items == []
    assert execution.package.decisions[0].action.value == "WITHHOLD"
    assert "RESTRICTED" in execution.package.decisions[0].reasons[0]


def test_invalid_model_gateway_context_binding_is_rejected() -> None:
    model_request = _model_request()
    with pytest.raises(ValidationError, match="context hash does not match"):
        ModelGatewayExecutionRequest(
            gateway_request_id="GW-BAD",
            model_use_request=model_request,
            expected_context_sha256="sha256:" + "0" * 64,
            requested_at=model_request.requested_at,
        )


class _ExternalEffectTestProvider:
    provider_id = "bad-test-provider"

    def invoke(self, package, *, replay_key):
        return ModelGatewayProviderResponse(
            provider_id=self.provider_id,
            response_text="should never be accepted",
            external_effect=True,
        )


def test_test_model_gateway_cannot_claim_external_effect() -> None:
    with pytest.raises(PermissionError, match="cannot produce external effects"):
        execute_model_gateway(
            _gateway_request(_model_request()),
            provider=_ExternalEffectTestProvider(),
            replay_store=ModelGatewayReplayStore(),
        )


def test_model_output_cannot_claim_canonical_authority() -> None:
    text = "model output"
    with pytest.raises(ValidationError, match="cannot be canonical"):
        ModelGatewayOutput(
            provider_id="provider",
            response_text=text,
            response_sha256=canonical_sha256(text),
            canonical=True,
        )


SPRINT32_TESTED_PATHS = {
    "current-authority-retrieval",
    "historical-retrieval",
    "structured-retrieval",
    "semantic-retrieval",
    "deterministic-pagination",
    "noncanonical-projection",
    "policy-filtered-model-package",
    "provider-neutral-model-gateway",
    "model-gateway-receipt",
    "deterministic-replay",
    "tenant-leakage-denied",
    "subject-leakage-denied",
    "audience-leakage-denied",
    "purpose-leakage-denied",
    "stale-state-denied",
    "stale-cursor-denied",
    "invalid-context-hash-denied",
    "test-external-effect-denied",
    "model-output-canonicalization-denied",
}


def test_every_declared_sprint32_path_has_automated_coverage() -> None:
    sprint32_retrieval_model_gateway_path_manifest().assert_complete_coverage(
        SPRINT32_TESTED_PATHS
    )


def test_sprint32_paths_are_test_only_and_prohibit_authority_leakage() -> None:
    manifest = sprint32_retrieval_model_gateway_path_manifest()
    assert manifest.execution_context == ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "canonical-mutation" in path.prohibited_effects
        assert "cross-boundary-leakage" in path.prohibited_effects
        assert "projection-authority" in path.prohibited_effects
