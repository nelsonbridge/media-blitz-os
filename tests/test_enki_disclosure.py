from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from nks.enki.contracts import (
    ConfidenceAssertion,
    ConfidenceLevel,
    FindingKind,
    ReconciliationFinding,
    ReconciliationResult,
    SubjectRef,
)
from nks.enki.disclosure import (
    ConservativeDisclosureService,
    DisclosureAudience,
    DisclosureContext,
    disclosure_content_hash,
)
from nks.governance.approvals import (
    ApprovalConsumptionStatus,
    ApprovalDecision,
    ApprovalGrant,
    ApprovalRequest,
    ExecutionContext,
    evaluate_approval,
)


def _now() -> datetime:
    return datetime(2026, 7, 13, 22, 0, tzinfo=timezone.utc)


def _result(level: ConfidenceLevel = ConfidenceLevel.HIGH) -> ReconciliationResult:
    subject = SubjectRef(subject_id="SUBJECT-1", subject_type="PERSON")
    finding = ReconciliationFinding(
        finding_id="RF-1",
        subject=subject,
        domain="career",
        finding_kind=FindingKind.DIVERGENCE,
        summary="A recorded decision diverges from the supplied objective.",
        observation_ids=["OBS-1"],
        relationship_ids=["REL-1"],
        evidence_ids=["E-1"],
        objective_refs=["OBJ-1"],
        priority_refs=["PRI-1"],
        confidence=ConfidenceAssertion(
            level=level,
            rationale=(
                "Supported by attributable evidence."
                if level != ConfidenceLevel.UNKNOWN
                else "Support is incomplete."
            ),
            evidence_ids=["E-1"] if level != ConfidenceLevel.UNKNOWN else [],
        ),
        created_at=_now(),
        interpretation_version="enki-test/v1",
    )
    return ReconciliationResult(
        subject=subject,
        domain="career",
        findings=[finding],
        unresolved_observation_ids=[],
        interpretation_version="enki-test/v1",
        reconciled_at=_now(),
    )


def _external_approval(
    result: ReconciliationResult,
    *,
    action: str = "disclose:external_model",
):
    content_hash = disclosure_content_hash(result, {"RF-1"})
    transaction_id = "TX-DISCLOSE-1"
    request = ApprovalRequest(
        execution_context=ExecutionContext.TEST,
        action=action,
        subject_id=result.subject.subject_id,
        content_sha256=content_hash,
        acceptable_authority_classes={"SUBJECT"},
        transaction_id=transaction_id,
        requested_at=_now(),
    )
    grant = ApprovalGrant(
        approval_id="APR-DISCLOSE-1",
        decision=ApprovalDecision.APPROVED,
        execution_context=ExecutionContext.TEST,
        permitted_actions={action},
        subject_id=result.subject.subject_id,
        content_sha256=content_hash,
        authorized_by="SUBJECT-1",
        authority_class="SUBJECT",
        issued_at=_now() - timedelta(minutes=1),
        expires_at=_now() + timedelta(hours=1),
        consumption_status=ApprovalConsumptionStatus.RESERVED,
        reserved_by_transaction_id=transaction_id,
    )
    return evaluate_approval(grant, request)


def test_subject_requested_finding_is_surfaced_without_external_approval() -> None:
    disclosed = ConservativeDisclosureService().evaluate(
        _result(),
        DisclosureContext(
            disclosure_id="DISC-1",
            audience=DisclosureAudience.SUBJECT,
            purpose="answer the subject's current question",
            requested_finding_ids={"RF-1"},
            requested_by_subject=True,
            policy_version="disclosure-test/v1",
        ),
    )

    assert [item.finding_id for item in disclosed.findings] == ["RF-1"]
    assert disclosed.receipt.surfaced_finding_ids == ["RF-1"]
    assert disclosed.receipt.approval_id is None


def test_unrequested_subject_disclosure_is_withheld() -> None:
    disclosed = ConservativeDisclosureService().evaluate(
        _result(),
        DisclosureContext(
            disclosure_id="DISC-2",
            audience=DisclosureAudience.SUBJECT,
            purpose="unsolicited disclosure",
            requested_finding_ids={"RF-1"},
            requested_by_subject=False,
            policy_version="disclosure-test/v1",
        ),
    )

    assert disclosed.findings == []
    assert disclosed.receipt.withheld_finding_ids == ["RF-1"]


def test_unknown_confidence_is_deferred_not_erased() -> None:
    disclosed = ConservativeDisclosureService().evaluate(
        _result(ConfidenceLevel.UNKNOWN),
        DisclosureContext(
            disclosure_id="DISC-3",
            audience=DisclosureAudience.SUBJECT,
            purpose="requested review",
            requested_finding_ids={"RF-1"},
            requested_by_subject=True,
            policy_version="disclosure-test/v1",
        ),
    )

    assert disclosed.findings == []
    assert disclosed.receipt.deferred_finding_ids == ["RF-1"]
    assert disclosed.receipt.withheld_finding_ids == []


def test_external_disclosure_requires_content_bound_reserved_approval() -> None:
    result = _result()
    service = ConservativeDisclosureService()

    without_approval = service.evaluate(
        result,
        DisclosureContext(
            disclosure_id="DISC-4",
            audience=DisclosureAudience.EXTERNAL_MODEL,
            purpose="model personalization",
            requested_finding_ids={"RF-1"},
            policy_version="disclosure-test/v1",
        ),
    )
    with_approval = service.evaluate(
        result,
        DisclosureContext(
            disclosure_id="DISC-5",
            audience=DisclosureAudience.EXTERNAL_MODEL,
            purpose="model personalization",
            requested_finding_ids={"RF-1"},
            policy_version="disclosure-test/v1",
            approval=_external_approval(result),
        ),
    )

    assert without_approval.receipt.withheld_finding_ids == ["RF-1"]
    assert with_approval.receipt.surfaced_finding_ids == ["RF-1"]
    assert with_approval.receipt.approval_id == "APR-DISCLOSE-1"
    assert with_approval.receipt.execution_context == ExecutionContext.TEST
    assert with_approval.receipt.transaction_id == "TX-DISCLOSE-1"


def test_external_approval_for_wrong_action_is_withheld() -> None:
    result = _result()
    disclosed = ConservativeDisclosureService().evaluate(
        result,
        DisclosureContext(
            disclosure_id="DISC-6",
            audience=DisclosureAudience.EXTERNAL_MODEL,
            purpose="model personalization",
            requested_finding_ids={"RF-1"},
            policy_version="disclosure-test/v1",
            approval=_external_approval(result, action="disclose:public"),
        ),
    )

    assert disclosed.receipt.withheld_finding_ids == ["RF-1"]
    assert any(
        "approval action does not match" in reason
        for reason in disclosed.receipt.decisions[0].reasons
    )


def test_unknown_finding_reference_fails_closed() -> None:
    with pytest.raises(ValueError, match="unknown finding references"):
        ConservativeDisclosureService().evaluate(
            _result(),
            DisclosureContext(
                disclosure_id="DISC-7",
                audience=DisclosureAudience.SUBJECT,
                purpose="requested review",
                requested_finding_ids={"RF-MISSING"},
                requested_by_subject=True,
                policy_version="disclosure-test/v1",
            ),
        )
