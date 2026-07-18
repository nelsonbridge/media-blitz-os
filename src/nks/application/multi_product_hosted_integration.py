"""Multi-product hosted integration proof for Enki Sprint 47.

The orchestrator composes the stable product-consumer contracts from Sprint 33 with
the shared multi-consumer platform runtime from Sprint 34.  All product writes pass
through HostedProductConsumer and all operational execution passes through
HostedPlatformRuntime.  The integration remains TEST-only and provider-neutral.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.application.hosted_downstream_integration import (
    HostedEnkiService,
    HostedProductConsumer,
    InMemoryHostedReceiptStore,
    InMemoryHostedStateStore,
    ProductConsumer,
    SubjectClass,
    product_consumer_contracts,
)
from nks.application.hosted_platform_operations import (
    HostedOperation,
    HostedOperationReceipt,
    HostedPlatformRuntime,
    IncidentEvidence,
    PortableHostedPlatformState,
)
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryContext, HumanBoundaryPolicy


class IntegratedOperationKind(StrEnum):
    STATE_CREATE = "STATE_CREATE"


class MultiProductIntegrationError(RuntimeError):
    """Fail-closed integration error without protected payload disclosure."""


class MultiProductOperationSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_id: str = Field(min_length=1)
    product: ProductConsumer
    tenant_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    subject_type: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    state_payload: dict[str, object]
    provenance_ids: tuple[str, ...] = Field(min_length=1)
    data_classification: str = Field(min_length=1)
    submitted_at: datetime
    human_policy: HumanBoundaryPolicy | None = None
    operation_kind: IntegratedOperationKind = IntegratedOperationKind.STATE_CREATE

    @property
    def payload_sha256(self) -> str:
        return canonical_sha256(
            {
                "product": self.product,
                "tenant_id": self.tenant_id,
                "subject_id": self.subject_id,
                "subject_type": self.subject_type,
                "domain": self.domain,
                "purpose": self.purpose,
                "state_payload": self.state_payload,
                "provenance_ids": self.provenance_ids,
            }
        )


class IntegratedProductResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    product: ProductConsumer
    operation_id: str
    state_id: str
    state_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    consumer_receipt_id: str
    consumer_receipt_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    platform_receipt_id: str
    platform_receipt_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    replayed: bool
    provenance_ids: tuple[str, ...]
    transaction_ids: tuple[str, ...]
    reconstruction_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    result_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "IntegratedProductResult":
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"result_sha256"})
        )
        if self.result_sha256 != expected:
            raise ValueError("integrated product result hash is invalid")
        return self


class IntegratedProductLineage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    product: ProductConsumer
    state_ids: tuple[str, ...]
    state_hashes: tuple[str, ...]
    provenance_ids: tuple[str, ...]
    transaction_ids: tuple[str, ...]
    reconstruction_hashes: tuple[str, ...]
    lineage_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "IntegratedProductLineage":
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"lineage_sha256"})
        )
        if self.lineage_sha256 != expected:
            raise ValueError("integrated product lineage hash is invalid")
        return self


class MultiProductIntegrationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    products: tuple[ProductConsumer, ...]
    results: tuple[IntegratedProductResult, ...]
    lineages: tuple[IntegratedProductLineage, ...]
    incident_ids: tuple[str, ...]
    platform_state_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    telemetry_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    provider_effects: int = Field(ge=0)
    external_effects: int = Field(ge=0)
    report_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_report(self) -> "MultiProductIntegrationReport":
        expected_products = {
            ProductConsumer.MEDIA_BLITZ,
            ProductConsumer.CAREER_INTELLIGENCE,
            ProductConsumer.PERSONAL_COGNITIVE_CONTINUITY,
        }
        if set(self.products) != expected_products:
            raise ValueError("integration report must include all three hosted products")
        if self.provider_effects != 0 or self.external_effects != 0:
            raise ValueError("Sprint 47 TEST integration cannot claim provider or external effects")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"report_sha256"})
        )
        if self.report_sha256 != expected:
            raise ValueError("multi-product integration report hash is invalid")
        return self


class MultiProductHostedIntegration:
    """Shared TEST integration surface for all three Enki product consumers."""

    def __init__(
        self,
        *,
        global_active_limit: int = 3,
        default_consumer_active_limit: int = 1,
    ) -> None:
        self.state_store = InMemoryHostedStateStore()
        self.receipt_store = InMemoryHostedReceiptStore()
        self.enki_service = HostedEnkiService(
            state_store=self.state_store,
            receipt_store=self.receipt_store,
        )
        self.platform_runtime = HostedPlatformRuntime(
            global_active_limit=global_active_limit,
            default_consumer_active_limit=default_consumer_active_limit,
        )
        self.contracts = {
            contract.product: contract for contract in product_consumer_contracts()
        }
        self.consumers = {
            product: HostedProductConsumer(self.enki_service, contract)
            for product, contract in self.contracts.items()
        }
        self._results: dict[str, IntegratedProductResult] = {}

    def _boundary(self, spec: MultiProductOperationSpec) -> BoundaryContext:
        return BoundaryContext(
            namespace_id="NKS-HOSTED-INTEGRATION-TEST",
            tenant_id=spec.tenant_id,
            subject_id=spec.subject_id,
            domain=spec.domain,
            audience="internal",
            execution_context=ExecutionContext.TEST,
        )

    def _operation(self, spec: MultiProductOperationSpec) -> HostedOperation:
        return HostedOperation(
            operation_id=spec.operation_id,
            consumer_id=spec.product.value,
            purpose=spec.purpose,
            boundary_context=self._boundary(spec),
            operation_type=spec.operation_kind.value,
            payload_hash=spec.payload_sha256,
            submitted_at=spec.submitted_at,
            data_classification=spec.data_classification,
            contains_raw_sensitive_fields=(
                spec.product == ProductConsumer.PERSONAL_COGNITIVE_CONTINUITY
            ),
        )

    def execute(
        self,
        spec: MultiProductOperationSpec,
        *,
        inject_failure: bool = False,
    ) -> IntegratedProductResult:
        contract = self.contracts[spec.product]
        if spec.domain not in contract.allowed_domains:
            raise MultiProductIntegrationError("product domain is outside the governed contract")
        if spec.purpose not in contract.allowed_purposes:
            raise MultiProductIntegrationError("product purpose is outside the governed contract")

        consumer = self.consumers[spec.product]
        operation = self._operation(spec)

        def action() -> dict[str, object]:
            if inject_failure:
                raise RuntimeError("injected product integration failure")
            state, receipt = consumer.create_state(
                tenant_id=spec.tenant_id,
                subject_id=spec.subject_id,
                subject_type=spec.subject_type,
                domain=spec.domain,
                purpose=spec.purpose,
                state_payload=spec.state_payload,
                provenance_ids=spec.provenance_ids,
                created_at=spec.submitted_at,
                human_policy=spec.human_policy,
            )
            return {
                "state_id": state.state_id,
                "state_hash": state.state_hash,
                "receipt_id": receipt.receipt_id,
                "receipt_hash": receipt.receipt_hash,
            }

        platform_receipt = self.platform_runtime.execute(operation, action)
        output = platform_receipt.output_payload or {}
        state_id = str(output["state_id"])
        reconstruction = consumer.reconstruct(state_id)
        consumer_receipt = self.receipt_store.get_for_state(state_id)[0]
        payload = {
            "product": spec.product,
            "operation_id": spec.operation_id,
            "state_id": state_id,
            "state_hash": str(output["state_hash"]),
            "consumer_receipt_id": consumer_receipt.receipt_id,
            "consumer_receipt_hash": consumer_receipt.receipt_hash,
            "platform_receipt_id": platform_receipt.receipt_id,
            "platform_receipt_hash": platform_receipt.receipt_hash,
            "replayed": platform_receipt.replayed,
            "provenance_ids": reconstruction.provenance_ids,
            "transaction_ids": reconstruction.transaction_ids,
            "reconstruction_sha256": reconstruction.reconstruction_hash,
        }
        result = IntegratedProductResult(
            **payload,
            result_sha256=canonical_sha256(payload),
        )
        self._results[spec.operation_id] = result
        return result

    def exact_replay(self, spec: MultiProductOperationSpec) -> IntegratedProductResult:
        """Replay one already-completed operation without creating another state effect."""
        replayed = self.execute(spec)
        if not replayed.replayed:
            raise MultiProductIntegrationError("expected exact replay did not replay")
        return replayed

    def incidents(self) -> tuple[IncidentEvidence, ...]:
        return self.platform_runtime.incidents()

    def export_platform_state(self) -> PortableHostedPlatformState:
        return self.platform_runtime.export_state()

    def recover_platform_runtime(self) -> HostedPlatformRuntime:
        return HostedPlatformRuntime.recover(self.platform_runtime.export_state())

    def report(self, *, run_id: str) -> MultiProductIntegrationReport:
        ordered_results = tuple(
            sorted(
                self._results.values(),
                key=lambda item: (item.product.value, item.operation_id),
            )
        )
        lineages: list[IntegratedProductLineage] = []
        for product in (
            ProductConsumer.MEDIA_BLITZ,
            ProductConsumer.CAREER_INTELLIGENCE,
            ProductConsumer.PERSONAL_COGNITIVE_CONTINUITY,
        ):
            product_results = tuple(item for item in ordered_results if item.product == product)
            if not product_results:
                raise MultiProductIntegrationError(
                    f"missing integrated workload for product {product.value}"
                )
            payload = {
                "product": product,
                "state_ids": tuple(item.state_id for item in product_results),
                "state_hashes": tuple(item.state_hash for item in product_results),
                "provenance_ids": tuple(
                    sorted(
                        {
                            provenance
                            for item in product_results
                            for provenance in item.provenance_ids
                        }
                    )
                ),
                "transaction_ids": tuple(
                    sorted(
                        {
                            transaction
                            for item in product_results
                            for transaction in item.transaction_ids
                        }
                    )
                ),
                "reconstruction_hashes": tuple(
                    item.reconstruction_sha256 for item in product_results
                ),
            }
            lineages.append(
                IntegratedProductLineage(
                    **payload,
                    lineage_sha256=canonical_sha256(payload),
                )
            )

        platform_state = self.platform_runtime.export_state()
        telemetry = self.platform_runtime.telemetry_events()
        payload = {
            "run_id": run_id,
            "products": (
                ProductConsumer.MEDIA_BLITZ,
                ProductConsumer.CAREER_INTELLIGENCE,
                ProductConsumer.PERSONAL_COGNITIVE_CONTINUITY,
            ),
            "results": ordered_results,
            "lineages": tuple(lineages),
            "incident_ids": tuple(
                incident.incident_id for incident in self.platform_runtime.incidents()
            ),
            "platform_state_sha256": platform_state.export_hash,
            "telemetry_sha256": canonical_sha256(telemetry),
            "provider_effects": 0,
            "external_effects": 0,
        }
        return MultiProductIntegrationReport(
            **payload,
            report_sha256=canonical_sha256(payload),
        )
