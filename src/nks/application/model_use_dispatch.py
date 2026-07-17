"""Capability-isolated dispatch for governed model-use packages."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from nks.application.human_state_model_use import (
    GovernedHumanStateModelUseReceipt,
    canonical_model_use_payload,
    hash_model_use_package,
)
from nks.application.model_use_journal import (
    ModelUseEventStage,
    ModelUseJournal,
    WorkflowEventWriter,
)
from nks.domain.human_state import ModelFeedbackPackage
from nks.governance.approvals import ExecutionContext

_DISPATCH_IMPLEMENTATION = "nks.application.model_use_dispatch"


class ExternalTransportReceipt(BaseModel):
    """Provider response returned by an injected production transport."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    adapter_id: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    provider_receipt_id: str = Field(min_length=1)
    dispatched_at: datetime


class ModelUseDispatchResult(BaseModel):
    """Local immutable result of a TEST simulation or PRODUCTION transmission."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    transaction_id: str
    model_use_receipt_id: str
    execution_context: ExecutionContext
    payload_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    adapter_id: str
    destination: str
    external_effect: bool
    provider_receipt_id: str | None = None
    dispatched_at: datetime


class ProductionModelUseTransport(Protocol):
    """Explicit production-only capability boundary."""

    def transmit(
        self,
        payload: str,
        *,
        transaction_id: str,
        payload_hash: str,
    ) -> ExternalTransportReceipt: ...


def _validate_package_receipt(
    package: ModelFeedbackPackage,
    receipt: GovernedHumanStateModelUseReceipt,
) -> None:
    observed_hash = hash_model_use_package(package)
    if observed_hash != receipt.payload_hash:
        raise ValueError("model-use package hash does not match governed receipt")
    if package.subject_id != receipt.subject_id:
        raise ValueError("model-use package subject does not match governed receipt")
    if package.domain != receipt.domain:
        raise ValueError("model-use package domain does not match governed receipt")
    if package.permitted_scope != receipt.destination_scope:
        raise ValueError("model-use package scope does not match governed receipt")


class TestModelUseDispatcher:
    """TEST dispatcher with no external transport capability.

    The constructor accepts no transport, credentials, endpoint, callback, or
    generic adapter. It can validate and report a simulated dispatch, but it is
    structurally unable to transmit the package outside the current process.
    """

    __test__ = False

    def __init__(self, *, event_writer: WorkflowEventWriter | None = None) -> None:
        self._journal = ModelUseJournal(event_writer)

    def dispatch(
        self,
        package: ModelFeedbackPackage,
        receipt: GovernedHumanStateModelUseReceipt,
    ) -> ModelUseDispatchResult:
        if receipt.execution_context != ExecutionContext.TEST:
            raise PermissionError("TEST dispatcher accepts only TEST receipts")
        _validate_package_receipt(package, receipt)
        result = ModelUseDispatchResult(
            transaction_id=receipt.transaction_id,
            model_use_receipt_id=receipt.receipt_id,
            execution_context=ExecutionContext.TEST,
            payload_hash=receipt.payload_hash,
            adapter_id="test-no-external-effect",
            destination="TEST_CAPTURE",
            external_effect=False,
            dispatched_at=receipt.recorded_at,
        )
        self._journal.record(
            ModelUseEventStage.TEST_DISPATCH_SIMULATED,
            occurred_at=receipt.recorded_at,
            transaction_id=receipt.transaction_id,
            subject_id=receipt.subject_id,
            approval_id=receipt.approval_id,
            policy_id=receipt.policy_id,
            payload_hash=receipt.payload_hash,
            execution_context=receipt.execution_context.value,
            actor_capability="test-model-use-dispatch",
            actor_implementation=_DISPATCH_IMPLEMENTATION,
        )
        return result


class ProductionModelUseDispatcher:
    """PRODUCTION dispatcher that requires an explicit external transport."""

    def __init__(
        self,
        transport: ProductionModelUseTransport,
        *,
        event_writer: WorkflowEventWriter | None = None,
    ) -> None:
        self._transport = transport
        self._journal = ModelUseJournal(event_writer)

    def dispatch(
        self,
        package: ModelFeedbackPackage,
        receipt: GovernedHumanStateModelUseReceipt,
    ) -> ModelUseDispatchResult:
        if receipt.execution_context != ExecutionContext.PRODUCTION:
            raise PermissionError(
                "production dispatcher requires a PRODUCTION model-use receipt"
            )
        _validate_package_receipt(package, receipt)
        try:
            external = self._transport.transmit(
                canonical_model_use_payload(package),
                transaction_id=receipt.transaction_id,
                payload_hash=receipt.payload_hash,
            )
        except Exception as exc:
            self._journal.record(
                ModelUseEventStage.DISPATCH_FAILED,
                occurred_at=receipt.recorded_at,
                transaction_id=receipt.transaction_id,
                subject_id=receipt.subject_id,
                approval_id=receipt.approval_id,
                policy_id=receipt.policy_id,
                payload_hash=receipt.payload_hash,
                execution_context=receipt.execution_context.value,
                failure_type=type(exc).__name__,
                actor_capability="production-model-use-dispatch",
                actor_implementation=_DISPATCH_IMPLEMENTATION,
            )
            raise

        result = ModelUseDispatchResult(
            transaction_id=receipt.transaction_id,
            model_use_receipt_id=receipt.receipt_id,
            execution_context=ExecutionContext.PRODUCTION,
            payload_hash=receipt.payload_hash,
            adapter_id=external.adapter_id,
            destination=external.destination,
            external_effect=True,
            provider_receipt_id=external.provider_receipt_id,
            dispatched_at=external.dispatched_at,
        )
        self._journal.record(
            ModelUseEventStage.PRODUCTION_DISPATCHED,
            occurred_at=receipt.recorded_at,
            transaction_id=receipt.transaction_id,
            subject_id=receipt.subject_id,
            approval_id=receipt.approval_id,
            policy_id=receipt.policy_id,
            payload_hash=receipt.payload_hash,
            execution_context=receipt.execution_context.value,
            actor_capability="production-model-use-dispatch",
            actor_implementation=_DISPATCH_IMPLEMENTATION,
        )
        return result
