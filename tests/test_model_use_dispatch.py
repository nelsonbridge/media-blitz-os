from __future__ import annotations

import inspect
from datetime import date, datetime, timezone

import pytest

from nks.application.human_state_model_use import (
    GovernedHumanStateModelUseReceipt,
    canonical_model_use_payload,
    hash_model_use_package,
)
from nks.application.model_use_dispatch import (
    ExternalTransportReceipt,
    ProductionModelUseDispatcher,
    TestModelUseDispatcher,
)
from nks.application.model_use_journal import ModelUseEventStage
from nks.domain.human_state import (
    ExpressionStrength,
    HumanStateObservation,
    IngestionScope,
    ModelFeedbackPackage,
    TemporalStatus,
)
from nks.governance.approvals import ExecutionContext


def _now() -> datetime:
    return datetime(2026, 7, 14, 9, 0, tzinfo=timezone.utc)


def _package() -> ModelFeedbackPackage:
    observation = HumanStateObservation(
        observation_id="OBS-1",
        subject_id="SUBJECT-1",
        content="Prioritize stable income.",
        content_hash="sha256:" + "1" * 64,
        domain="career",
        state_type="DECLARED_PRIORITY",
        provenance="REAL",
        source_id="SOURCE-1",
        observed_at=_now(),
        effective_from=date(2026, 7, 1),
        expression_strength=ExpressionStrength.EXPLICIT,
        confidence="HIGH",
        temporal_status=TemporalStatus.CURRENT,
    )
    return ModelFeedbackPackage(
        subject_id="SUBJECT-1",
        domain="career",
        current_observation=observation,
        historical_observations=[],
        transitions=[],
        permitted_scope=IngestionScope.PERSONALIZATION,
        behavioral_instructions={"preserve_uncertainty": True},
    )


def _receipt(context: ExecutionContext) -> GovernedHumanStateModelUseReceipt:
    package = _package()
    return GovernedHumanStateModelUseReceipt(
        receipt_id="NKS-GMUR-1",
        subject_id=package.subject_id,
        domain=package.domain,
        observation_ids=[package.current_observation.observation_id],
        transition_ids=[],
        policy_id="POL-1",
        approval_id="APR-1",
        execution_context=context,
        transaction_id="TX-1",
        destination_scope=package.permitted_scope,
        payload_hash=hash_model_use_package(package),
        authorized_at=_now(),
        recorded_at=_now(),
        publisher_version="test/v1",
    )


class EventMemory:
    def __init__(self) -> None:
        self.events = []

    def append(self, event) -> None:
        self.events.append(event)


class Transport:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls = []

    def transmit(self, payload: str, *, transaction_id: str, payload_hash: str):
        self.calls.append((payload, transaction_id, payload_hash))
        if self.fail:
            raise ConnectionError("simulated provider failure")
        return ExternalTransportReceipt(
            adapter_id="provider-adapter/v1",
            destination="provider:model-personalization",
            provider_receipt_id="PROVIDER-1",
            dispatched_at=_now(),
        )


def test_test_dispatcher_has_no_transport_injection_surface() -> None:
    parameters = inspect.signature(TestModelUseDispatcher).parameters

    assert set(parameters) == {"event_writer"}
    with pytest.raises(TypeError):
        TestModelUseDispatcher(object())  # type: ignore[call-arg]


def test_test_dispatch_is_structurally_non_external() -> None:
    events = EventMemory()
    package = _package()

    result = TestModelUseDispatcher(event_writer=events).dispatch(
        package,
        _receipt(ExecutionContext.TEST),
    )

    assert result.external_effect is False
    assert result.provider_receipt_id is None
    assert result.destination == "TEST_CAPTURE"
    assert len(events.events) == 1
    assert events.events[0].payload["stage"] == (
        ModelUseEventStage.TEST_DISPATCH_SIMULATED.value
    )
    assert events.events[0].actor_capability == "test-model-use-dispatch"


def test_test_dispatcher_rejects_production_receipt() -> None:
    with pytest.raises(PermissionError, match="only TEST receipts"):
        TestModelUseDispatcher().dispatch(
            _package(),
            _receipt(ExecutionContext.PRODUCTION),
        )


def test_production_dispatcher_rejects_test_receipt_without_transport_call() -> None:
    transport = Transport()

    with pytest.raises(PermissionError, match="requires a PRODUCTION"):
        ProductionModelUseDispatcher(transport).dispatch(
            _package(),
            _receipt(ExecutionContext.TEST),
        )

    assert transport.calls == []


def test_production_dispatch_uses_explicit_transport_and_journals_effect() -> None:
    events = EventMemory()
    transport = Transport()
    package = _package()
    receipt = _receipt(ExecutionContext.PRODUCTION)

    result = ProductionModelUseDispatcher(
        transport,
        event_writer=events,
    ).dispatch(package, receipt)

    assert result.external_effect is True
    assert result.provider_receipt_id == "PROVIDER-1"
    assert transport.calls == [
        (
            canonical_model_use_payload(package),
            receipt.transaction_id,
            receipt.payload_hash,
        )
    ]
    assert events.events[0].payload["stage"] == (
        ModelUseEventStage.PRODUCTION_DISPATCHED.value
    )
    assert events.events[0].actor_capability == "production-model-use-dispatch"


def test_tampered_package_fails_before_production_transport() -> None:
    transport = Transport()
    package = _package()
    receipt = _receipt(ExecutionContext.PRODUCTION)
    tampered = package.model_copy(
        update={"behavioral_instructions": {"preserve_uncertainty": False}}
    )

    with pytest.raises(ValueError, match="package hash"):
        ProductionModelUseDispatcher(transport).dispatch(tampered, receipt)

    assert transport.calls == []


def test_production_transport_failure_is_journaled_and_re_raised() -> None:
    events = EventMemory()
    transport = Transport(fail=True)

    with pytest.raises(ConnectionError, match="provider failure"):
        ProductionModelUseDispatcher(
            transport,
            event_writer=events,
        ).dispatch(_package(), _receipt(ExecutionContext.PRODUCTION))

    assert events.events[0].payload["stage"] == ModelUseEventStage.DISPATCH_FAILED.value
    assert events.events[0].payload["failure_type"] == "ConnectionError"
    assert events.events[0].actor_implementation == "nks.application.model_use_dispatch"
