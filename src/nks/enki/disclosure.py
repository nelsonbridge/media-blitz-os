"""Governed disclosure of reconciliation findings.

Reconciliation and disclosure are separate operations. This module decides
which already-produced findings may be surfaced to a specific audience. It does
not alter findings, objectives, priorities, or the underlying evidence.
"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from nks.enki.contracts import (
    ConfidenceLevel,
    DisclosureAction,
    DisclosureDecision,
    ReconciliationFinding,
    ReconciliationResult,
    SubjectRef,
)
from nks.governance.approvals import (
    ApprovalConsumptionStatus,
    ApprovalEvaluation,
    ExecutionContext,
)


class DisclosureAudience(StrEnum):
    SUBJECT = "SUBJECT"
    INTERNAL_OPERATOR = "INTERNAL_OPERATOR"
    EXTERNAL_MODEL = "EXTERNAL_MODEL"
    PUBLIC = "PUBLIC"


_EXTERNAL_AUDIENCES = frozenset(
    {DisclosureAudience.EXTERNAL_MODEL, DisclosureAudience.PUBLIC}
)


class DisclosureContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    disclosure_id: str = Field(min_length=1)
    audience: DisclosureAudience
    purpose: str = Field(min_length=1)
    requested_finding_ids: set[str] = Field(default_factory=set)
    requested_by_subject: bool = False
    policy_version: str = Field(min_length=1)
    approval: ApprovalEvaluation | None = None


class DisclosureReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    disclosure_id: str
    subject: SubjectRef
    domain: str
    audience: DisclosureAudience
    purpose: str
    requested_finding_ids: list[str]
    surfaced_finding_ids: list[str]
    deferred_finding_ids: list[str]
    withheld_finding_ids: list[str]
    decisions: list[DisclosureDecision]
    content_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    approval_id: str | None = None
    execution_context: ExecutionContext | None = None
    transaction_id: str | None = None
    policy_version: str


class DisclosureResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    findings: list[ReconciliationFinding] = Field(default_factory=list)
    receipt: DisclosureReceipt


def disclosure_content_hash(
    result: ReconciliationResult,
    requested_finding_ids: set[str],
) -> str:
    """Hash the exact requested findings in deterministic identifier order."""

    payload = [
        finding.model_dump(mode="json", exclude_none=False)
        for finding in sorted(result.findings, key=lambda item: item.finding_id)
        if finding.finding_id in requested_finding_ids
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class ConservativeDisclosureService:
    """Apply a restrained, audience-aware disclosure policy.

    Subject-facing disclosure requires the subject to have requested the
    findings. External model or public disclosure additionally requires a
    reserved, content-bound approval evaluation for the exact audience. An
    exact retry may use a previously consumed grant owned by the same
    transaction. Unknown-confidence findings are deferred rather than erased.
    """

    def evaluate(
        self,
        result: ReconciliationResult,
        context: DisclosureContext,
    ) -> DisclosureResult:
        findings_by_id = {finding.finding_id: finding for finding in result.findings}
        unknown_ids = context.requested_finding_ids - findings_by_id.keys()
        if unknown_ids:
            raise ValueError(f"unknown finding references: {sorted(unknown_ids)}")

        requested_hash = disclosure_content_hash(result, context.requested_finding_ids)
        authority_reasons = self._authority_reasons(result, context, requested_hash)
        decisions: list[DisclosureDecision] = []
        surfaced: list[ReconciliationFinding] = []

        for finding in sorted(result.findings, key=lambda item: item.finding_id):
            if finding.finding_id not in context.requested_finding_ids:
                action = DisclosureAction.WITHHOLD
                reasons = ["finding was not selected for this disclosure request"]
            elif authority_reasons:
                action = DisclosureAction.WITHHOLD
                reasons = list(authority_reasons)
            elif finding.confidence.level == ConfidenceLevel.UNKNOWN:
                action = DisclosureAction.DEFER
                reasons = ["finding confidence is UNKNOWN; preserve internally pending support"]
            else:
                action = DisclosureAction.SURFACE
                reasons = ["finding is requested, attributable, and authorized for this audience"]
                surfaced.append(finding)

            decisions.append(
                DisclosureDecision(
                    finding_id=finding.finding_id,
                    action=action,
                    reasons=reasons,
                    decided_at=result.reconciled_at,
                    policy_version=context.policy_version,
                    metadata={
                        "audience": context.audience.value,
                        "purpose": context.purpose,
                    },
                )
            )

        surfaced_ids = [
            decision.finding_id
            for decision in decisions
            if decision.action == DisclosureAction.SURFACE
        ]
        deferred_ids = [
            decision.finding_id
            for decision in decisions
            if decision.action == DisclosureAction.DEFER
        ]
        withheld_ids = [
            decision.finding_id
            for decision in decisions
            if decision.action == DisclosureAction.WITHHOLD
        ]
        approval = context.approval

        return DisclosureResult(
            findings=surfaced,
            receipt=DisclosureReceipt(
                disclosure_id=context.disclosure_id,
                subject=result.subject,
                domain=result.domain,
                audience=context.audience,
                purpose=context.purpose,
                requested_finding_ids=sorted(context.requested_finding_ids),
                surfaced_finding_ids=surfaced_ids,
                deferred_finding_ids=deferred_ids,
                withheld_finding_ids=withheld_ids,
                decisions=decisions,
                content_sha256=requested_hash,
                approval_id=approval.approval_id if approval else None,
                execution_context=(
                    approval.request.execution_context if approval else None
                ),
                transaction_id=approval.request.transaction_id if approval else None,
                policy_version=context.policy_version,
            ),
        )

    @staticmethod
    def _authority_reasons(
        result: ReconciliationResult,
        context: DisclosureContext,
        requested_hash: str,
    ) -> list[str]:
        reasons: list[str] = []

        if context.audience == DisclosureAudience.SUBJECT and not context.requested_by_subject:
            reasons.append("subject-facing disclosure was not requested by the subject")

        if context.audience in _EXTERNAL_AUDIENCES:
            approval = context.approval
            expected_action = f"disclose:{context.audience.value.lower()}"
            if approval is None:
                reasons.append("external disclosure requires governed approval")
            elif not approval.authorized:
                reasons.append("external disclosure approval evaluation is not authorized")
            else:
                request = approval.request
                reservation_owned = (
                    approval.consumption_status == ApprovalConsumptionStatus.RESERVED
                    and approval.reserved_by_transaction_id == request.transaction_id
                )
                retry_owned = (
                    approval.consumption_status == ApprovalConsumptionStatus.CONSUMED
                    and approval.exact_retry
                    and approval.consumed_by_transaction_id == request.transaction_id
                )
                if not reservation_owned and not retry_owned:
                    reasons.append("external disclosure approval is not reserved for execution")
                if request.action != expected_action:
                    reasons.append("approval action does not match disclosure audience")
                if request.subject_id != result.subject.subject_id:
                    reasons.append("approval subject does not match reconciliation subject")
                if request.content_sha256 != requested_hash:
                    reasons.append("approval content hash does not match requested findings")

        return reasons
