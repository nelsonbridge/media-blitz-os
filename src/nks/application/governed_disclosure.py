"""Transactional disclosure with privacy, consent, purpose, and redaction controls."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    DisclosureAction,
    DisclosureDecision,
    ReconciliationResult,
)
from nks.enki.disclosure import (
    ConservativeDisclosureService,
    DisclosureAudience,
    DisclosureContext,
    DisclosureReceipt,
    DisclosureResult,
    disclosure_content_hash,
)
from nks.governance.approvals import ApprovalRequest, ExecutionContext, evaluate_approval


class DisclosureConsentState(StrEnum):
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    REVOKED = "REVOKED"
    NOT_REQUIRED = "NOT_REQUIRED"
    UNKNOWN = "UNKNOWN"


class SensitivityLevel(StrEnum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    PRIVATE = "PRIVATE"
    RESTRICTED = "RESTRICTED"


class DisclosureProtectionPolicy(BaseModel):
    """Exact audience, purpose, sensitivity, consent, redaction, and validity policy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_id: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    allowed_purposes: set[str] = Field(min_length=1)
    allowed_audiences: set[DisclosureAudience] = Field(min_length=1)
    sensitivity: SensitivityLevel
    consent_state: DisclosureConsentState
    redaction_required_for: set[DisclosureAudience] = Field(default_factory=set)
    approved_by: str = Field(min_length=1)
    approved_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_window(self) -> "DisclosureProtectionPolicy":
        if self.expires_at is not None and self.expires_at <= self.approved_at:
            raise ValueError("expires_at must follow approved_at")
        if self.revoked_at is not None and self.revoked_at < self.approved_at:
            raise ValueError("revoked_at cannot precede approved_at")
        return self

    def withholding_reasons(
        self,
        *,
        audience: DisclosureAudience,
        purpose: str,
        at: datetime,
    ) -> list[str]:
        reasons: list[str] = []
        if purpose not in self.allowed_purposes:
            reasons.append("purpose is not allowed by the protection policy")
        if audience not in self.allowed_audiences:
            reasons.append("audience is not allowed by the protection policy")
        if self.consent_state in {
            DisclosureConsentState.DENIED,
            DisclosureConsentState.REVOKED,
            DisclosureConsentState.UNKNOWN,
        }:
            reasons.append(f"disclosure consent state is {self.consent_state.value}")
        if self.expires_at is not None and self.expires_at <= at:
            reasons.append("protection policy is expired")
        if self.revoked_at is not None and self.revoked_at <= at:
            reasons.append("protection policy is revoked")
        if audience in self.redaction_required_for:
            reasons.append(
                "redaction is required and no separately approved redacted derivative was supplied"
            )
        if (
            self.sensitivity == SensitivityLevel.INTERNAL
            and audience in {DisclosureAudience.EXTERNAL_MODEL, DisclosureAudience.PUBLIC}
        ):
            reasons.append("INTERNAL material cannot be externally disclosed")
        if (
            self.sensitivity == SensitivityLevel.PRIVATE
            and audience not in {
                DisclosureAudience.SUBJECT,
                DisclosureAudience.INTERNAL_OPERATOR,
            }
        ):
            reasons.append("PRIVATE material cannot be disclosed to this audience")
        if (
            self.sensitivity == SensitivityLevel.RESTRICTED
            and audience != DisclosureAudience.SUBJECT
        ):
            reasons.append("RESTRICTED material is limited to the subject")
        return list(dict.fromkeys(reasons))


class GovernedDisclosurePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    result: ReconciliationResult
    disclosure_id: str = Field(min_length=1)
    audience: DisclosureAudience
    purpose: str = Field(min_length=1)
    requested_finding_ids: set[str] = Field(min_length=1)
    requested_by_subject: bool = False
    protection_policy: DisclosureProtectionPolicy

    @model_validator(mode="after")
    def validate_scope(self) -> "GovernedDisclosurePayload":
        if self.protection_policy.subject_id != self.result.subject.subject_id:
            raise ValueError("protection policy subject does not match findings subject")
        finding_ids = {item.finding_id for item in self.result.findings}
        unknown = self.requested_finding_ids - finding_ids
        if unknown:
            raise ValueError(f"unknown requested findings: {sorted(unknown)}")
        return self


class GovernedDisclosurePlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation: GovernedOperationPlan
    payload: GovernedDisclosurePayload

    @classmethod
    def create(
        cls,
        *,
        transaction_id: str,
        result: ReconciliationResult,
        disclosure_id: str,
        audience: DisclosureAudience,
        purpose: str,
        requested_finding_ids: set[str],
        requested_by_subject: bool,
        protection_policy: DisclosureProtectionPolicy,
        execution_context: ExecutionContext,
        acceptable_authority_classes: set[str],
        requested_at: datetime,
    ) -> "GovernedDisclosurePlan":
        payload = GovernedDisclosurePayload(
            result=result,
            disclosure_id=disclosure_id,
            audience=audience,
            purpose=purpose,
            requested_finding_ids=requested_finding_ids,
            requested_by_subject=requested_by_subject,
            protection_policy=protection_policy,
        )
        operation = GovernedOperationPlan(
            operation_id="enki-disclosure",
            transaction_id=transaction_id,
            action=f"disclose:{audience.value.lower()}",
            subject_id=result.subject.subject_id,
            content_sha256=disclosure_content_hash(result, requested_finding_ids),
            execution_context=execution_context,
            acceptable_authority_classes=acceptable_authority_classes,
            requested_at=requested_at,
            metadata={
                "disclosure_id": disclosure_id,
                "protection_policy_id": protection_policy.policy_id,
                "payload_sha256": canonical_sha256(payload),
            },
        )
        return cls(operation=operation, payload=payload)


class DisclosureReceiptWriter(Protocol):
    def append_disclosure_receipt(self, receipt: DisclosureReceipt) -> None: ...


class DisclosureAdapter:
    def __init__(
        self,
        *,
        plan: GovernedDisclosurePlan,
        approval_id: str,
        approval_repository: ApprovalGrantRepository,
        receipt_writer: DisclosureReceiptWriter,
        service: ConservativeDisclosureService | None = None,
        now: datetime,
    ) -> None:
        self._plan = plan
        self._approval_id = approval_id
        self._approval_repository = approval_repository
        self._receipt_writer = receipt_writer
        self._service = service or ConservativeDisclosureService()
        self._now = now
        self.result: DisclosureResult | None = None

    def _approval_request(self) -> ApprovalRequest:
        operation = self._plan.operation
        return ApprovalRequest(
            execution_context=operation.execution_context,
            action=operation.action,
            subject_id=operation.subject_id,
            content_sha256=operation.content_sha256,
            acceptable_authority_classes=operation.acceptable_authority_classes,
            transaction_id=operation.transaction_id,
            requested_at=operation.requested_at,
        )

    def _apply_protection(
        self,
        base: DisclosureResult,
        reasons: list[str],
    ) -> DisclosureResult:
        if not reasons:
            return base
        payload = self._plan.payload
        decisions: list[DisclosureDecision] = []
        for decision in base.receipt.decisions:
            if decision.finding_id in payload.requested_finding_ids:
                decisions.append(
                    decision.model_copy(
                        update={
                            "action": DisclosureAction.WITHHOLD,
                            "reasons": reasons,
                            "metadata": {
                                **decision.metadata,
                                "protection_policy_id": (
                                    payload.protection_policy.policy_id
                                ),
                                "sensitivity": (
                                    payload.protection_policy.sensitivity.value
                                ),
                            },
                        }
                    )
                )
            else:
                decisions.append(decision)
        surfaced_ids = [
            item.finding_id
            for item in decisions
            if item.action == DisclosureAction.SURFACE
        ]
        deferred_ids = [
            item.finding_id
            for item in decisions
            if item.action == DisclosureAction.DEFER
        ]
        withheld_ids = [
            item.finding_id
            for item in decisions
            if item.action == DisclosureAction.WITHHOLD
        ]
        receipt = base.receipt.model_copy(
            update={
                "surfaced_finding_ids": surfaced_ids,
                "deferred_finding_ids": deferred_ids,
                "withheld_finding_ids": withheld_ids,
                "decisions": decisions,
            }
        )
        surfaced = [
            finding
            for finding in base.findings
            if finding.finding_id in surfaced_ids
        ]
        return DisclosureResult(findings=surfaced, receipt=receipt)

    def apply(self, plan: GovernedOperationPlan) -> GovernedOperationResult:
        if plan != self._plan.operation:
            raise RuntimeError("disclosure adapter received a mismatched plan")
        grant = self._approval_repository.get_approval(self._approval_id)
        if grant is None:
            raise RuntimeError("consumed disclosure approval is missing")
        evaluation = evaluate_approval(grant, self._approval_request(), now=self._now)
        context = DisclosureContext(
            disclosure_id=self._plan.payload.disclosure_id,
            audience=self._plan.payload.audience,
            purpose=self._plan.payload.purpose,
            requested_finding_ids=self._plan.payload.requested_finding_ids,
            requested_by_subject=self._plan.payload.requested_by_subject,
            policy_version=self._plan.payload.protection_policy.policy_version,
            approval=evaluation,
        )
        base = self._service.evaluate(self._plan.payload.result, context)
        reasons = self._plan.payload.protection_policy.withholding_reasons(
            audience=self._plan.payload.audience,
            purpose=self._plan.payload.purpose,
            at=self._now,
        )
        self.result = self._apply_protection(base, reasons)
        self._receipt_writer.append_disclosure_receipt(self.result.receipt)
        return GovernedOperationResult(
            output_sha256=canonical_sha256(self.result.receipt),
            metadata={
                "disclosure_id": self.result.receipt.disclosure_id,
                "surfaced_finding_ids": self.result.receipt.surfaced_finding_ids,
                "deferred_finding_ids": self.result.receipt.deferred_finding_ids,
                "withheld_finding_ids": self.result.receipt.withheld_finding_ids,
            },
        )


class GovernedDisclosureOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    result: DisclosureResult
    transaction_receipt: GovernedTransactionReceipt


class ExecuteGovernedDisclosure:
    def __init__(
        self,
        *,
        approval_repository: ApprovalGrantRepository,
        journal: GovernedTransactionJournal,
        transaction_receipt_repository: GovernedTransactionReceiptRepository,
        disclosure_receipt_writer: DisclosureReceiptWriter,
        service: ConservativeDisclosureService | None = None,
    ) -> None:
        self._approval_repository = approval_repository
        self._disclosure_receipt_writer = disclosure_receipt_writer
        self._service = service
        self._executor = GovernedTransactionExecutor(
            approval_repository=approval_repository,
            journal=journal,
            receipt_repository=transaction_receipt_repository,
        )

    def execute(
        self,
        plan: GovernedDisclosurePlan,
        *,
        approval_id: str,
        now: datetime | None = None,
        failure_hook: FailureHook | None = None,
    ) -> GovernedDisclosureOutcome:
        at = now or plan.operation.requested_at
        adapter = DisclosureAdapter(
            plan=plan,
            approval_id=approval_id,
            approval_repository=self._approval_repository,
            receipt_writer=self._disclosure_receipt_writer,
            service=self._service,
            now=at,
        )
        transaction_receipt = self._executor.execute(
            plan.operation,
            approval_id=approval_id,
            adapter=adapter,
            now=at,
            failure_hook=failure_hook,
        )
        if adapter.result is None:
            raise RuntimeError("disclosure result was not reconstructed for this execution")
        return GovernedDisclosureOutcome(
            result=adapter.result,
            transaction_receipt=transaction_receipt,
        )
