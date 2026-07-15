"""Downstream product boundary contracts and no-effect TEST proof service.

Media Blitz, Career Intelligence and Placement, and Personal Cognitive Continuity
consume Enki only through the stable consumer contract. Product outputs remain
noncanonical and TEST no-effect; no product adapter receives a canonical repository
or approval-consumption primitive.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.consumer_adapters import ConsumerApiAdapter
from nks.application.consumer_contracts import ConsumerStatus
from nks.application.governed_transactions import canonical_sha256
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryContext


class ProductSuite(StrEnum):
    MEDIA_BLITZ = "MEDIA_BLITZ"
    CAREER_INTELLIGENCE_PLACEMENT = "CAREER_INTELLIGENCE_PLACEMENT"
    PERSONAL_COGNITIVE_CONTINUITY = "PERSONAL_COGNITIVE_CONTINUITY"


EXPECTED_AUDIENCE = {
    ProductSuite.MEDIA_BLITZ: "media-blitz",
    ProductSuite.CAREER_INTELLIGENCE_PLACEMENT: "career-placement",
    ProductSuite.PERSONAL_COGNITIVE_CONTINUITY: "cognitive-continuity",
}


class ProductBoundaryFailure(RuntimeError):
    pass


class ProductConsumerContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_id: str = Field(min_length=1)
    suite: ProductSuite
    consumer_contract_version: Literal["1.0"] = "1.0"
    boundary: BoundaryContext
    authorization_id: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    permitted_output_kinds: set[str] = Field(min_length=1)
    contract_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_scope_and_hash(self) -> "ProductConsumerContract":
        if self.boundary.execution_context != ExecutionContext.TEST:
            raise ValueError("Sprint 22 product contracts are TEST-only")
        if self.boundary.audience != EXPECTED_AUDIENCE[self.suite]:
            raise ValueError("product contract audience does not match suite")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"contract_sha256"})
        )
        if self.contract_sha256 != expected:
            raise ValueError("product consumer contract hash is invalid")
        return self

    @classmethod
    def create(cls, **values: Any) -> "ProductConsumerContract":
        payload = dict(values)
        payload["contract_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class ProductPackage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    package_id: str = Field(min_length=1)
    suite: ProductSuite
    output_kind: str = Field(min_length=1)
    source_request_id: str = Field(min_length=1)
    source_receipt_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    boundary: BoundaryContext
    provenance_refs: list[str] = Field(min_length=1)
    context_refs: list[str] = Field(min_length=1)
    privacy_labels: list[str]
    authority_ref: str = Field(min_length=1)
    payload: dict[str, Any]
    canonical_effect: Literal[False] = False
    external_effect: Literal[False] = False
    package_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "ProductPackage":
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"package_sha256"})
        )
        if self.package_sha256 != expected:
            raise ValueError("product package hash is invalid")
        return self


class NoEffectProductReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: str = Field(min_length=1)
    suite: ProductSuite
    package_id: str
    package_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    boundary_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    outcome: Literal["TEST_NO_EFFECT"] = "TEST_NO_EFFECT"
    canonical_mutation: Literal[False] = False
    external_effect: Literal[False] = False
    recorded_at: datetime
    receipt_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "NoEffectProductReceipt":
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"receipt_sha256"})
        )
        if self.receipt_sha256 != expected:
            raise ValueError("no-effect receipt hash is invalid")
        return self


class ProductBoundaryRegistry:
    """Reject authority reuse and duplicate product scope at registration time."""

    def __init__(self, contracts: list[ProductConsumerContract]) -> None:
        self._contracts: dict[ProductSuite, ProductConsumerContract] = {}
        authority_to_suite: dict[str, ProductSuite] = {}
        boundary_to_suite: dict[str, ProductSuite] = {}
        for contract in contracts:
            if contract.suite in self._contracts:
                raise ProductBoundaryFailure("duplicate suite contract")
            prior_authority = authority_to_suite.get(contract.authorization_id)
            if prior_authority is not None and prior_authority != contract.suite:
                raise ProductBoundaryFailure("cross-product authority reuse denied")
            boundary_sha = contract.boundary.boundary_sha256
            prior_boundary = boundary_to_suite.get(boundary_sha)
            if prior_boundary is not None and prior_boundary != contract.suite:
                raise ProductBoundaryFailure("cross-product boundary reuse denied")
            self._contracts[contract.suite] = contract
            authority_to_suite[contract.authorization_id] = contract.suite
            boundary_to_suite[boundary_sha] = contract.suite

    def get(self, suite: ProductSuite) -> ProductConsumerContract:
        try:
            return self._contracts[suite]
        except KeyError as exc:
            raise ProductBoundaryFailure("product suite is not registered") from exc


class NoEffectProductAdapter:
    """TEST adapter that records receipts but has no product or canonical side effect."""

    def __init__(self) -> None:
        self._receipts: dict[str, NoEffectProductReceipt] = {}

    @property
    def receipts(self) -> dict[str, NoEffectProductReceipt]:
        return dict(self._receipts)

    def deliver(self, package: ProductPackage, *, now: datetime) -> NoEffectProductReceipt:
        existing = self._receipts.get(package.package_id)
        if existing is not None:
            if existing.package_sha256 != package.package_sha256:
                raise ProductBoundaryFailure("package identity conflict")
            return existing
        payload = {
            "receipt_id": f"PRODUCT-RCPT-{package.package_sha256.removeprefix('sha256:')[:24]}",
            "suite": package.suite,
            "package_id": package.package_id,
            "package_sha256": package.package_sha256,
            "boundary_sha256": package.boundary.boundary_sha256,
            "outcome": "TEST_NO_EFFECT",
            "canonical_mutation": False,
            "external_effect": False,
            "recorded_at": now,
        }
        receipt = NoEffectProductReceipt(
            **payload,
            receipt_sha256=canonical_sha256(payload),
        )
        self._receipts[package.package_id] = receipt
        return receipt


_PROHIBITED_CANONICAL_INTENTS = {
    "canonical_write",
    "canonical_mutation",
    "direct_canonical_write",
    "prediction_to_canonical",
    "recommendation_to_canonical",
    "publication_decision_to_canonical",
    "inferred_preference_to_canonical",
}


class DownstreamProductProofService:
    """Execute one scoped product proof through the stable v1 consumer API."""

    def __init__(
        self,
        *,
        registry: ProductBoundaryRegistry,
        consumer_api: ConsumerApiAdapter,
        adapter: NoEffectProductAdapter,
    ) -> None:
        self._registry = registry
        self._consumer_api = consumer_api
        self._adapter = adapter

    def run(
        self,
        *,
        suite: ProductSuite,
        consumer_request: dict[str, Any],
        output_kind: str,
        provenance_refs: list[str],
        context_refs: list[str],
        privacy_labels: list[str],
        now: datetime,
    ) -> tuple[ProductPackage, NoEffectProductReceipt]:
        contract = self._registry.get(suite)
        self._validate_request(contract, consumer_request, output_kind)
        response = self._consumer_api.invoke(consumer_request, now=now)
        if response.get("status") != ConsumerStatus.OK.value:
            raise ProductBoundaryFailure(
                f"consumer request failed closed: {response.get('error_code', 'UNKNOWN')}"
            )
        response_receipt = response["receipt"]
        package_payload = {
            "package_id": f"{suite.value}-PKG-{response_receipt['response_sha256'].split(':', 1)[1][:20]}",
            "suite": suite,
            "output_kind": output_kind,
            "source_request_id": response["request_id"],
            "source_receipt_sha256": response_receipt["receipt_sha256"],
            "boundary": contract.boundary,
            "provenance_refs": provenance_refs,
            "context_refs": context_refs,
            "privacy_labels": privacy_labels,
            "authority_ref": contract.authorization_id,
            "payload": {
                "data": response["data"],
                "items": response["items"],
                "pagination": response["pagination"],
            },
            "canonical_effect": False,
            "external_effect": False,
        }
        package = ProductPackage(
            **package_payload,
            package_sha256=canonical_sha256(package_payload),
        )
        receipt = self._adapter.deliver(package, now=now)
        return package, receipt

    @staticmethod
    def _validate_request(
        contract: ProductConsumerContract,
        request: dict[str, Any],
        output_kind: str,
    ) -> None:
        if request.get("contract_version") != contract.consumer_contract_version:
            raise ProductBoundaryFailure("consumer contract version mismatch")
        if request.get("authorization_id") != contract.authorization_id:
            raise ProductBoundaryFailure("cross-product authority reuse denied")
        boundary = BoundaryContext.model_validate(request.get("boundary"))
        if boundary != contract.boundary:
            raise ProductBoundaryFailure("cross-product scope or audience widening denied")
        if output_kind not in contract.permitted_output_kinds:
            raise ProductBoundaryFailure("output kind is outside product contract")
        DownstreamProductProofService._reject_canonical_intents(request.get("payload", {}))
        scope = request.get("payload", {}).get("product_scope")
        if scope is not None and scope != contract.suite.value:
            raise ProductBoundaryFailure("cross-product data leakage denied")

    @staticmethod
    def _reject_canonical_intents(value: Any) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key).strip().lower() in _PROHIBITED_CANONICAL_INTENTS:
                    raise ProductBoundaryFailure(
                        "downstream product cannot request direct canonical mutation"
                    )
                DownstreamProductProofService._reject_canonical_intents(nested)
        elif isinstance(value, list):
            for nested in value:
                DownstreamProductProofService._reject_canonical_intents(nested)


def downstream_contract_fixture() -> dict[str, Any]:
    return {
        "consumer_contract_version": "1.0",
        "suites": {
            ProductSuite.MEDIA_BLITZ.value: {
                "audience": EXPECTED_AUDIENCE[ProductSuite.MEDIA_BLITZ],
                "outputs": ["publication-package", "distribution-plan"],
            },
            ProductSuite.CAREER_INTELLIGENCE_PLACEMENT.value: {
                "audience": EXPECTED_AUDIENCE[ProductSuite.CAREER_INTELLIGENCE_PLACEMENT],
                "outputs": ["opportunity-view", "application-package"],
            },
            ProductSuite.PERSONAL_COGNITIVE_CONTINUITY.value: {
                "audience": EXPECTED_AUDIENCE[ProductSuite.PERSONAL_COGNITIVE_CONTINUITY],
                "outputs": ["continuity-view", "reflection-package"],
            },
        },
        "required_preservation": [
            "provenance",
            "context",
            "privacy",
            "authority",
        ],
        "prohibited_direct_canonical_outputs": [
            "predictions",
            "recommendations",
            "publication-decisions",
            "inferred-preferences",
        ],
        "adapter_effect": "TEST_NO_EFFECT",
    }
