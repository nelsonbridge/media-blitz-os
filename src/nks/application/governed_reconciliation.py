"""Temporal/context eligibility and transactional reconciliation execution."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from nks.application.approval_lifecycle import ApprovalGrantRepository
from nks.application.governed_transactions import (
    FailureHook,
    GovernedOperationPlan,
    GovernedOperationResult,
    GovernedTransactionExecutor,
    GovernedTransactionJournal,
    GovernedTransactionReceipt,
    GovernedTransactionReceiptRepository,
    canonical_sha256,
)
from nks.enki.contracts import (
    Observation,
    ReconciliationFinding,
    ReconciliationRequest,
    ReconciliationResult,
    ReferenceKind,
    RelationshipAssertion,
    TemporalStatus,
)
from nks.enki.reconciliation import ReconciliationEngine
from nks.governance.approvals import ExecutionContext


class EligibilityReason(StrEnum):
    FUTURE = "FUTURE"
    EXPIRED = "EXPIRED"
    RETRACTED = "RETRACTED"
    SUPERSEDED = "SUPERSEDED"
    HISTORICAL = "HISTORICAL"
    DISPUTED = "DISPUTED"
    CONTEXT_MISMATCH = "CONTEXT_MISMATCH"
    INELIGIBLE_ENDPOINT = "INELIGIBLE_ENDPOINT"


class EligibilityPolicy(BaseModel):
    """Exact temporal and context rules for one reconciliation request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_id: str = Field(min_length=1)
    required_context: set[str] = Field(default_factory=set)
    include_historical: bool = False
    include_disputed: bool = False
    policy_version: str = Field(min_length=1)


class EligibilityDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(min_length=1)
    record_kind: str = Field(min_length=1)
    eligible: bool
    reasons: list[EligibilityReason] = Field(default_factory=list)


class EligibleReconciliationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request: ReconciliationRequest
    decisions: list[EligibilityDecision]
    policy: EligibilityPolicy


class TemporalContextEligibilityResolver:
    """Select only state applicable at the request time and context."""

    @staticmethod
    def _context_reasons(
        record_context: list[str],
        policy: EligibilityPolicy,
    ) -> list[EligibilityReason]:
        if policy.required_context and not policy.required_context <= set(record_context):
            return [EligibilityReason.CONTEXT_MISMATCH]
        return []

    def _observation_reasons(
        self,
        observation: Observation,
        *,
        as_of: datetime,
        policy: EligibilityPolicy,
    ) -> list[EligibilityReason]:
        reasons = self._context_reasons(observation.context, policy)
        as_of_date = as_of.date()
        if observation.applicability.effective_from > as_of_date:
            reasons.append(EligibilityReason.FUTURE)
        if (
            observation.applicability.effective_until is not None
            and observation.applicability.effective_until < as_of_date
        ):
            reasons.append(EligibilityReason.EXPIRED)
        if observation.temporal_status == TemporalStatus.RETRACTED:
            reasons.append(EligibilityReason.RETRACTED)
        if observation.temporal_status == TemporalStatus.SUPERSEDED:
            reasons.append(EligibilityReason.SUPERSEDED)
        if observation.temporal_status == TemporalStatus.EXPIRED:
            reasons.append(EligibilityReason.EXPIRED)
        if (
            observation.temporal_status == TemporalStatus.HISTORICAL
            and not policy.include_historical
        ):
            reasons.append(EligibilityReason.HISTORICAL)
        if (
            observation.temporal_status == TemporalStatus.DISPUTED
            and not policy.include_disputed
        ):
            reasons.append(EligibilityReason.DISPUTED)
        return list(dict.fromkeys(reasons))

    def _relationship_reasons(
        self,
        relationship: RelationshipAssertion,
        *,
        as_of: datetime,
        policy: EligibilityPolicy,
        eligible_observation_ids: set[str],
    ) -> list[EligibilityReason]:
        reasons = self._context_reasons(relationship.context, policy)
        as_of_date = as_of.date()
        if relationship.applicability.effective_from > as_of_date:
            reasons.append(EligibilityReason.FUTURE)
        if (
            relationship.applicability.effective_until is not None
            and relationship.applicability.effective_until < as_of_date
        ):
            reasons.append(EligibilityReason.EXPIRED)
        for kind, reference_id in (
            (relationship.source_kind, relationship.source_id),
            (relationship.target_kind, relationship.target_id),
        ):
            if (
                kind == ReferenceKind.OBSERVATION
                and reference_id not in eligible_observation_ids
            ):
                reasons.append(EligibilityReason.INELIGIBLE_ENDPOINT)
        return list(dict.fromkeys(reasons))

    def resolve(
        self,
        request: ReconciliationRequest,
        policy: EligibilityPolicy,
    ) -> EligibleReconciliationInput:
        decisions: list[EligibilityDecision] = []
        eligible_observations: list[Observation] = []
        for observation in request.observations:
            reasons = self._observation_reasons(
                observation,
                as_of=request.as_of,
                policy=policy,
            )
            decisions.append(
                EligibilityDecision(
                    record_id=observation.observation_id,
                    record_kind="OBSERVATION",
                    eligible=not reasons,
                    reasons=reasons,
                )
            )
            if not reasons:
                eligible_observations.append(observation)

        eligible_observation_ids = {
            item.observation_id for item in eligible_observations
        }
        eligible_relationships: list[RelationshipAssertion] = []
        for relationship in request.relationships:
            reasons = self._relationship_reasons(
                relationship,
                as_of=request.as_of,
                policy=policy,
                eligible_observation_ids=eligible_observation_ids,
            )
            decisions.append(
                EligibilityDecision(
                    record_id=relationship.relationship_id,
                    record_kind="RELATIONSHIP",
                    eligible=not reasons,
                    reasons=reasons,
                )
            )
            if not reasons:
                eligible_relationships.append(relationship)

        eligible_request = request.model_copy(
            update={
                "observations": eligible_observations,
                "relationships": eligible_relationships,
            }
        )
        return EligibleReconciliationInput(
            request=eligible_request,
            decisions=decisions,
            policy=policy,
        )


class GovernedReconciliationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation: GovernedOperationPlan
    eligible_input: EligibleReconciliationInput

    @classmethod
    def create(
        cls,
        *,
        transaction_id: str,
        request: ReconciliationRequest,
        policy: EligibilityPolicy,
        execution_context: ExecutionContext,
        acceptable_authority_classes: set[str],
        resolver: TemporalContextEligibilityResolver | None = None,
    ) -> "GovernedReconciliationPlan":
        eligible_input = (resolver or TemporalContextEligibilityResolver()).resolve(
            request,
            policy,
        )
        operation = GovernedOperationPlan(
            operation_id="enki-reconciliation",
            transaction_id=transaction_id,
            action="enki:reconcile",
            subject_id=request.subject.subject_id,
            content_sha256=canonical_sha256(eligible_input),
            execution_context=execution_context,
            acceptable_authority_classes=acceptable_authority_classes,
            requested_at=request.as_of,
            metadata={
                "eligibility_policy_id": policy.policy_id,
                "eligibility_policy_version": policy.policy_version,
            },
        )
        return cls(operation=operation, eligible_input=eligible_input)


class FindingWriter(Protocol):
    def append_findings(self, findings: list[ReconciliationFinding]) -> None: ...


class ReconciliationAdapter:
    def __init__(
        self,
        engine: ReconciliationEngine,
        writer: FindingWriter,
        request: ReconciliationRequest,
    ) -> None:
        self.result = engine.execute(request)
        self._writer = writer

    def apply(self, plan: GovernedOperationPlan) -> GovernedOperationResult:
        self._writer.append_findings(self.result.findings)
        return GovernedOperationResult(
            output_sha256=canonical_sha256(self.result),
            metadata={
                "finding_ids": [item.finding_id for item in self.result.findings],
                "unresolved_observation_ids": self.result.unresolved_observation_ids,
            },
        )


class GovernedReconciliationOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    result: ReconciliationResult
    eligibility_decisions: list[EligibilityDecision]
    transaction_receipt: GovernedTransactionReceipt


class ExecuteGovernedReconciliation:
    def __init__(
        self,
        *,
        engine: ReconciliationEngine,
        finding_writer: FindingWriter,
        approval_repository: ApprovalGrantRepository,
        journal: GovernedTransactionJournal,
        receipt_repository: GovernedTransactionReceiptRepository,
    ) -> None:
        self._engine = engine
        self._finding_writer = finding_writer
        self._executor = GovernedTransactionExecutor(
            approval_repository=approval_repository,
            journal=journal,
            receipt_repository=receipt_repository,
        )

    def execute(
        self,
        plan: GovernedReconciliationPlan,
        *,
        approval_id: str,
        now: datetime | None = None,
        failure_hook: FailureHook | None = None,
    ) -> GovernedReconciliationOutcome:
        adapter = ReconciliationAdapter(
            self._engine,
            self._finding_writer,
            plan.eligible_input.request,
        )
        receipt = self._executor.execute(
            plan.operation,
            approval_id=approval_id,
            adapter=adapter,
            now=now,
            failure_hook=failure_hook,
        )
        return GovernedReconciliationOutcome(
            result=adapter.result,
            eligibility_decisions=plan.eligible_input.decisions,
            transaction_receipt=receipt,
        )
