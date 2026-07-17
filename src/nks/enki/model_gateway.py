"""Provider-neutral, receipted model gateway for governed Enki model use."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.enki_model_use_policy import (
    build_enki_model_use_package,
    model_use_context_sha256,
)
from nks.application.governed_transactions import canonical_sha256
from nks.enki.model_use_contracts import EnkiModelUsePackage, EnkiModelUseRequest
from nks.governance.approvals import ExecutionContext


class ModelGatewayConflictError(RuntimeError):
    pass


class ModelGatewayProviderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider_id: str = Field(min_length=1)
    response_text: str
    external_effect: bool


class ModelGatewayProvider(Protocol):
    provider_id: str

    def invoke(
        self,
        package: EnkiModelUsePackage,
        *,
        replay_key: str,
    ) -> ModelGatewayProviderResponse: ...


class ModelGatewayExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    gateway_request_id: str = Field(min_length=1)
    model_use_request: EnkiModelUseRequest
    expected_context_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    requested_at: datetime

    @model_validator(mode="after")
    def validate_context_binding(self) -> "ModelGatewayExecutionRequest":
        expected = model_use_context_sha256(self.model_use_request)
        if self.expected_context_sha256 != expected:
            raise ValueError("model gateway context hash does not match model-use request")
        if self.requested_at != self.model_use_request.requested_at:
            raise ValueError("model gateway request time must match package request time")
        return self


class ModelGatewayOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider_id: str
    response_text: str
    response_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    canonical: bool = False

    @model_validator(mode="after")
    def validate_noncanonical_output(self) -> "ModelGatewayOutput":
        if self.canonical:
            raise ValueError("model gateway output cannot be canonical")
        if self.response_sha256 != canonical_sha256(self.response_text):
            raise ValueError("model gateway response hash is invalid")
        return self


class ModelGatewayReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: str
    gateway_request_id: str
    package_id: str
    package_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    context_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    provider_id: str
    replay_key: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    response_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    execution_context: ExecutionContext
    external_effect: bool
    canonical_mutation: bool = False
    recorded_at: datetime

    @model_validator(mode="after")
    def validate_gateway_boundary(self) -> "ModelGatewayReceipt":
        if self.canonical_mutation:
            raise ValueError("model gateway receipts cannot claim canonical mutation")
        if self.execution_context == ExecutionContext.TEST and self.external_effect:
            raise ValueError("TEST model gateway receipts cannot claim external effects")
        return self


class ModelGatewayExecution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    package: EnkiModelUsePackage
    output: ModelGatewayOutput
    receipt: ModelGatewayReceipt
    replayed: bool


class ModelGatewayReplayStore:
    """Minimal append-once replay store keyed by exact governed request inputs."""

    def __init__(self) -> None:
        self._executions: dict[str, ModelGatewayExecution] = {}

    def get(self, replay_key: str) -> ModelGatewayExecution | None:
        return self._executions.get(replay_key)

    def append(self, replay_key: str, execution: ModelGatewayExecution) -> None:
        existing = self._executions.get(replay_key)
        if existing is not None and existing != execution:
            raise ModelGatewayConflictError("replay key already binds a different execution")
        self._executions[replay_key] = execution


class DeterministicNoEffectModelProvider:
    """TEST provider with no network, credential, transport, or canonical-write surface."""

    provider_id = "enki-deterministic-no-effect-model/v1"

    def invoke(
        self,
        package: EnkiModelUsePackage,
        *,
        replay_key: str,
    ) -> ModelGatewayProviderResponse:
        if package.execution_context != ExecutionContext.TEST:
            raise PermissionError("no-effect model provider accepts TEST packages only")
        response_text = (
            "NO_EFFECT_TEST:" + canonical_sha256(
                {
                    "provider_id": self.provider_id,
                    "package_sha256": package.package_sha256,
                    "replay_key": replay_key,
                    "included_item_ids": [item.item_id for item in package.included_items],
                }
            )
        )
        return ModelGatewayProviderResponse(
            provider_id=self.provider_id,
            response_text=response_text,
            external_effect=False,
        )


def _replay_key(request: ModelGatewayExecutionRequest, package: EnkiModelUsePackage) -> str:
    return canonical_sha256(
        {
            "gateway_request_id": request.gateway_request_id,
            "package_sha256": package.package_sha256,
            "context_sha256": package.context_sha256,
            "execution_context": package.execution_context,
        }
    )


def execute_model_gateway(
    request: ModelGatewayExecutionRequest,
    *,
    provider: ModelGatewayProvider,
    replay_store: ModelGatewayReplayStore,
) -> ModelGatewayExecution:
    """Policy-build, invoke, receipt, and replay one exact provider-neutral model request."""

    package = build_enki_model_use_package(request.model_use_request)
    if package.context_sha256 != request.expected_context_sha256:
        raise ModelGatewayConflictError("built package context does not match gateway request")

    replay_key = _replay_key(request, package)
    existing = replay_store.get(replay_key)
    if existing is not None:
        return existing.model_copy(update={"replayed": True})

    response = provider.invoke(package, replay_key=replay_key)
    if response.provider_id != provider.provider_id:
        raise ModelGatewayConflictError("provider response identity does not match provider")
    if package.execution_context == ExecutionContext.TEST and response.external_effect:
        raise PermissionError("TEST model gateway cannot produce external effects")

    output = ModelGatewayOutput(
        provider_id=response.provider_id,
        response_text=response.response_text,
        response_sha256=canonical_sha256(response.response_text),
        canonical=False,
    )
    receipt = ModelGatewayReceipt(
        receipt_id=f"MODEL-GATEWAY-{request.gateway_request_id}",
        gateway_request_id=request.gateway_request_id,
        package_id=package.package_id,
        package_sha256=package.package_sha256,
        context_sha256=package.context_sha256,
        provider_id=response.provider_id,
        replay_key=replay_key,
        response_sha256=output.response_sha256,
        execution_context=package.execution_context,
        external_effect=response.external_effect,
        canonical_mutation=False,
        recorded_at=request.requested_at,
    )
    execution = ModelGatewayExecution(
        package=package,
        output=output,
        receipt=receipt,
        replayed=False,
    )
    replay_store.append(replay_key, execution)
    return execution
