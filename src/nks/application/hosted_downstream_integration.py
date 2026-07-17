"""Hosted TEST integration for Enki downstream product suites.

The integration consumes only governed retrieval projections and stable consumer
boundaries. It never receives canonical repositories, canonical writer handles, or
approval-consumption primitives. All deliveries are no-effect TEST receipts.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.downstream_products import (
    NoEffectProductAdapter,
    NoEffectProductReceipt,
    ProductBoundaryFailure,
    ProductBoundaryRegistry,
    ProductPackage,
    ProductSuite,
)
from nks.application.governed_transactions import canonical_sha256
from nks.enki.governed_retrieval import (
    GovernedKnowledgeRecord,
    GovernedRetrievalRequest,
    KnowledgeProjection,
    retrieve_governed_knowledge,
)
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import HumanBoundaryPolicy


class ConsumerIntent(StrEnum):
    MEDIA_PUBLICATION_PROOF = "MEDIA_PUBLICATION_PROOF"
    MEDIA_DISTRIBUTION_PROOF = "MEDIA_DISTRIBUTION_PROOF"
    CAREER_OPPORTUNITY_VIEW = "CAREER_OPPORTUNITY_VIEW"
    CAREER_APPLICATION_PREP = "CAREER_APPLICATION_PREP"
    COGNITIVE_CONTINUITY_VIEW = "COGNITIVE_CONTINUITY_VIEW"
    COGNITIVE_REFLECTION = "COGNITIVE_REFLECTION"
    COGNITIVE_CORRECTION_REQUEST = "COGNITIVE_CORRECTION_REQUEST"
    COGNITIVE_RETRACTION_REQUEST = "COGNITIVE_RETRACTION_REQUEST"


class ExternalActionAuthorization(BaseModel):
    """Exact TEST authority to exercise a downstream external-action path with no effect."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_id: str = Field(min_length=1)
    suite: ProductSuite
    action: str = Field(min_length=1)
    boundary_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    projection_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    execution_context: ExecutionContext
    authorized_by: str = Field(min_length=1)
    authorized_at: datetime
    allowed: bool
    authorization_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash_and_context(self) -> "ExternalActionAuthorization":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("Sprint 33 external-action authorization is TEST-only")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"authorization_sha256"})
        )
        if self.authorization_sha256 != expected:
            raise ValueError("external-action authorization hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "ExternalActionAuthorization":
        payload = dict(values)
        payload["authorization_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class HumanContinuityControl(BaseModel):
    """Human-specific control surface stricter than generic tenant authorization."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy: HumanBoundaryPolicy
    explicit_human_authority: bool
    privacy_acknowledged: bool
    temporal_authority_acknowledged: bool
    requested_intent: ConsumerIntent

    @property
    def permits_use(self) -> bool:
        return (
            self.policy.permits_use
            and self.explicit_human_authority
            and self.privacy_acknowledged
            and self.temporal_authority_acknowledged
        )


class HostedConsumerExecution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    suite: ProductSuite
    intent: ConsumerIntent
    projection: KnowledgeProjection
    package: ProductPackage
    receipt: NoEffectProductReceipt
    external_action_authorization_id: str | None = None
    human_control_applied: bool = False
    calibration_sha256: str | None = None


_INTENT_OUTPUT_KIND = {
    ConsumerIntent.MEDIA_PUBLICATION_PROOF: "publication-package",
    ConsumerIntent.MEDIA_DISTRIBUTION_PROOF: "distribution-plan",
    ConsumerIntent.CAREER_OPPORTUNITY_VIEW: "opportunity-view",
    ConsumerIntent.CAREER_APPLICATION_PREP: "application-package",
    ConsumerIntent.COGNITIVE_CONTINUITY_VIEW: "continuity-view",
    ConsumerIntent.COGNITIVE_REFLECTION: "reflection-package",
    ConsumerIntent.COGNITIVE_CORRECTION_REQUEST: "reflection-package",
    ConsumerIntent.COGNITIVE_RETRACTION_REQUEST: "reflection-package",
}

_INTENT_SUITE = {
    ConsumerIntent.MEDIA_PUBLICATION_PROOF: ProductSuite.MEDIA_BLITZ,
    ConsumerIntent.MEDIA_DISTRIBUTION_PROOF: ProductSuite.MEDIA_BLITZ,
    ConsumerIntent.CAREER_OPPORTUNITY_VIEW: ProductSuite.CAREER_INTELLIGENCE_PLACEMENT,
    ConsumerIntent.CAREER_APPLICATION_PREP: ProductSuite.CAREER_INTELLIGENCE_PLACEMENT,
    ConsumerIntent.COGNITIVE_CONTINUITY_VIEW: ProductSuite.PERSONAL_COGNITIVE_CONTINUITY,
    ConsumerIntent.COGNITIVE_REFLECTION: ProductSuite.PERSONAL_COGNITIVE_CONTINUITY,
    ConsumerIntent.COGNITIVE_CORRECTION_REQUEST: ProductSuite.PERSONAL_COGNITIVE_CONTINUITY,
    ConsumerIntent.COGNITIVE_RETRACTION_REQUEST: ProductSuite.PERSONAL_COGNITIVE_CONTINUITY,
}


class HostedDownstreamConsumerService:
    """Execute versioned product integrations against governed TEST retrieval only."""

    def __init__(
        self,
        *,
        registry: ProductBoundaryRegistry,
        delivery_adapter: NoEffectProductAdapter,
    ) -> None:
        self._registry = registry
        self._delivery = delivery_adapter

    def run(
        self,
        *,
        suite: ProductSuite,
        intent: ConsumerIntent,
        records: list[GovernedKnowledgeRecord],
        retrieval_request: GovernedRetrievalRequest,
        now: datetime,
        external_action_authorization: ExternalActionAuthorization | None = None,
        human_control: HumanContinuityControl | None = None,
        simulated_feedback: tuple[str, ...] = (),
    ) -> HostedConsumerExecution:
        contract = self._registry.get(suite)
        if _INTENT_SUITE[intent] != suite:
            raise ProductBoundaryFailure("consumer intent belongs to a different product suite")
        if contract.boundary.execution_context != ExecutionContext.TEST:
            raise ProductBoundaryFailure("hosted downstream integration is TEST-only")

        self._assert_retrieval_boundary(contract, retrieval_request)
        projection = retrieve_governed_knowledge(records, retrieval_request)
        output_kind = _INTENT_OUTPUT_KIND[intent]
        if output_kind not in contract.permitted_output_kinds:
            raise ProductBoundaryFailure("output kind is outside product contract")

        external_authorization_id = None
        if suite == ProductSuite.CAREER_INTELLIGENCE_PLACEMENT:
            external_authorization_id = self._validate_career_authority(
                intent,
                contract.boundary.boundary_sha256,
                projection.projection_hash,
                external_action_authorization,
            )

        human_control_applied = False
        if suite == ProductSuite.PERSONAL_COGNITIVE_CONTINUITY:
            self._validate_human_controls(intent, human_control)
            human_control_applied = True

        calibration_sha256 = None
        if suite == ProductSuite.MEDIA_BLITZ:
            calibration_sha256 = canonical_sha256(
                {
                    "projection_sha256": projection.projection_hash,
                    "simulated_feedback": sorted(simulated_feedback),
                    "delivery_mode": "TEST_NO_EFFECT",
                }
            )

        source_receipt_sha256 = canonical_sha256(
            {
                "retrieval_request": retrieval_request,
                "projection_sha256": projection.projection_hash,
            }
        )
        package_payload = {
            "package_id": f"{suite.value}-{intent.value}-{projection.projection_hash.removeprefix('sha256:')[:20]}",
            "suite": suite,
            "output_kind": output_kind,
            "source_request_id": canonical_sha256(retrieval_request),
            "source_receipt_sha256": source_receipt_sha256,
            "boundary": contract.boundary,
            "provenance_refs": sorted(
                {provenance for hit in projection.hits for provenance in hit.provenance_ids}
            )
            or ["NO-ELIGIBLE-PROVENANCE"],
            "context_refs": [
                f"purpose:{retrieval_request.purpose}",
                f"audience:{retrieval_request.audience}",
                f"timeline:{projection.timeline_hash}",
            ],
            "privacy_labels": ["governed-retrieval", "test-only"],
            "authority_ref": contract.authorization_id,
            "payload": {
                "intent": intent.value,
                "projection": projection.model_dump(mode="json"),
                "external_action_authorization_id": external_authorization_id,
                "human_control_applied": human_control_applied,
                "simulated_feedback": list(simulated_feedback),
                "calibration_sha256": calibration_sha256,
            },
            "canonical_effect": False,
            "external_effect": False,
        }
        package = ProductPackage(
            **package_payload,
            package_sha256=canonical_sha256(package_payload),
        )
        receipt = self._delivery.deliver(package, now=now)
        return HostedConsumerExecution(
            suite=suite,
            intent=intent,
            projection=projection,
            package=package,
            receipt=receipt,
            external_action_authorization_id=external_authorization_id,
            human_control_applied=human_control_applied,
            calibration_sha256=calibration_sha256,
        )

    @staticmethod
    def _assert_retrieval_boundary(contract, request: GovernedRetrievalRequest) -> None:
        boundary = contract.boundary
        checks = {
            "tenant": request.tenant_id == boundary.tenant_id,
            "subject": request.subject_id == boundary.subject_id,
            "domain": request.domain == boundary.domain,
            "audience": request.audience == boundary.audience,
            "purpose": request.purpose == contract.purpose,
        }
        for name, valid in checks.items():
            if not valid:
                raise ProductBoundaryFailure(f"cross-product {name} boundary leakage denied")

    @staticmethod
    def _validate_career_authority(
        intent: ConsumerIntent,
        boundary_sha256: str,
        projection_sha256: str,
        authorization: ExternalActionAuthorization | None,
    ) -> str | None:
        if intent != ConsumerIntent.CAREER_APPLICATION_PREP:
            return None
        if authorization is None:
            raise ProductBoundaryFailure("career external-action approval is required")
        if authorization.suite != ProductSuite.CAREER_INTELLIGENCE_PLACEMENT:
            raise ProductBoundaryFailure("cross-product external-action authority denied")
        if authorization.action != "prepare-external-application":
            raise ProductBoundaryFailure("external-action authorization action mismatch")
        if authorization.boundary_sha256 != boundary_sha256:
            raise ProductBoundaryFailure("external-action authorization boundary mismatch")
        if authorization.projection_sha256 != projection_sha256:
            raise ProductBoundaryFailure("external-action authorization projection mismatch")
        if not authorization.allowed:
            raise ProductBoundaryFailure("career external-action approval denied")
        return authorization.authorization_id

    @staticmethod
    def _validate_human_controls(
        intent: ConsumerIntent,
        control: HumanContinuityControl | None,
    ) -> None:
        if control is None or not control.permits_use:
            raise ProductBoundaryFailure("human continuity controls deny use")
        if control.requested_intent != intent:
            raise ProductBoundaryFailure("human continuity intent mismatch")
        if intent in {
            ConsumerIntent.COGNITIVE_CORRECTION_REQUEST,
            ConsumerIntent.COGNITIVE_RETRACTION_REQUEST,
        } and control.policy.correction_or_retraction_blocked:
            raise ProductBoundaryFailure("human correction or retraction is blocked")
