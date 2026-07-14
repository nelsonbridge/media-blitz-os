from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone

import pytest

from nks.adapters.approval_grants import JsonApprovalGrantRepository
from nks.adapters.enki_records import JsonEnkiRecordRepository
from nks.adapters.governed_transactions import JsonGovernedTransactionRepository
from nks.application.governed_disclosure import (
    DisclosureConsentState,
    DisclosureProtectionPolicy,
    ExecuteGovernedDisclosure,
    GovernedDisclosurePlan,
    SensitivityLevel,
)
from nks.application.governed_reconciliation import (
    EligibilityPolicy,
    EligibilityReason,
    ExecuteGovernedReconciliation,
    GovernedReconciliationPlan,
    TemporalContextEligibilityResolver,
)
from nks.application.governed_transactions import (
    TransactionStage,
    TransactionTerminalState,
)
from nks.enki.contracts import (
    ConfidenceAssertion,
    ConfidenceLevel,
    EvidenceRef,
    ExpressionOrigin,
    Observation,
    ReferenceKind,
    ReconciliationRequest,
    RelationshipAssertion,
    SubjectRef,
    TemporalApplicability,
    TemporalStatus,
)
from nks.enki.disclosure import DisclosureAudience
from nks.enki.reconciliation import ReconciliationEngine, RelationshipFindingStrategy
from nks.governance.approvals import (
    ApprovalConsumptionStatus,
    ApprovalDecision,
    ApprovalGrant,
    ExecutionContext,
)


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime(2026, 7, 14, 9, 0, tzinfo=timezone.utc)


SUBJECT = SubjectRef(subject_id="PERSON-1", subject_type="PERSON")


def _evidence(evidence_id: str) -> EvidenceRef:
    return EvidenceRef(
        evidence_id=evidence_id,
        source_id=f"SOURCE-{evidence_id}",
        content_hash=_hash(evidence_id),
        observed_at=_now(),
        provenance_classification="REAL",
    )


def _observation(
    observation_id: str,
    *,
    status: TemporalStatus = TemporalStatus.CURRENT,
    effective_from: date = date(2026, 7, 1),
    effective_until: date | None = None,
    context: list[str] | None = None,
) -> Observation:
    evidence = _evidence(f"E-{observation_id}")
    return Observation(
        observation_id=observation_id,
        subject=SUBJECT,
        domain="career",
        statement=f"Statement {observation_id}",
        content_hash=_hash(f"Statement {observation_id}"),
        evidence=[evidence],
        observed_at=_now(),
        applicability=TemporalApplicability(
            effective_from=effective_from,
            effective_until=effective_until,
        ),
        context=context or ["current-role"],
        expression_origin=ExpressionOrigin.SELF_DECLARED,
        confidence=ConfidenceAssertion(
            level=ConfidenceLevel.HIGH,
            rationale="direct statement",
            evidence_ids=[evidence.evidence_id],
        ),
        temporal_status=status,
    )


def _relationship(
    relationship_id: str,
    source_id: str,
    target_id: str,
    *,
    relationship_type: str = "SUPPORTS",
    evidence: bool = True,
    context: list[str] | None = None,
) -> RelationshipAssertion:
    attached = [_evidence(f"E-{relationship_id}")] if evidence else []
    return RelationshipAssertion(
        relationship_id=relationship_id,
        subject=SUBJECT,
        domain="career",
        source_kind=ReferenceKind.OBSERVATION,
        source_id=source_id,
        target_kind=ReferenceKind.OBSERVATION,
        target_id=target_id,
        relationship_type=relationship_type,
        evidence=attached,
        confidence=ConfidenceAssertion(
            level=ConfidenceLevel.HIGH,
            rationale="reviewed relationship",
            evidence_ids=[item.evidence_id for item in attached],
        ),
        observed_at=_now(),
        applicability=TemporalApplicability(effective_from=date(2026, 7, 1)),
        context=context or ["current-role"],
    )


def _request() -> ReconciliationRequest:
    observations = [
        _observation("OBS-1"),
        _observation("OBS-2"),
        _observation("OBS-FUTURE", effective_from=date(2026, 8, 1)),
        _observation("OBS-RETRACTED", status=TemporalStatus.RETRACTED),
        _observation("OBS-HISTORICAL", status=TemporalStatus.HISTORICAL),
        _observation("OBS-DISPUTED", status=TemporalStatus.DISPUTED),
        _observation("OBS-CONTEXT", context=["former-role"]),
    ]
    return ReconciliationRequest(
        subject=SUBJECT,
        domain="career",
        observations=observations,
        relationships=[
            _relationship("REL-1", "OBS-1", "OBS-2"),
            _relationship("REL-FUTURE", "OBS-1", "OBS-FUTURE"),
            _relationship(
                "REL-CONTEXT",
                "OBS-1",
                "OBS-2",
                context=["former-role"],
            ),
        ],
        objective_refs=[],
        priority_refs=[],
        as_of=_now(),
    )


def _eligibility_policy() -> EligibilityPolicy:
    return EligibilityPolicy(
        policy_id="ELIG-1",
        required_context={"current-role"},
        include_historical=False,
        include_disputed=False,
        policy_version="eligibility/v1",
    )


def _grant(operation, approval_id: str) -> ApprovalGrant:
    return ApprovalGrant(
        approval_id=approval_id,
        decision=ApprovalDecision.APPROVED,
        execution_context=operation.execution_context,
        permitted_actions={operation.action},
        subject_id=operation.subject_id,
        content_sha256=operation.content_sha256,
        authorized_by="PERSON-1",
        authority_class="SUBJECT",
        issued_at=_now() - timedelta(minutes=5),
        expires_at=_now() + timedelta(hours=1),
    )


def _engine() -> ReconciliationEngine:
    return ReconciliationEngine(
        RelationshipFindingStrategy(),
        interpretation_version="enki-test/v1",
    )


def test_temporal_context_resolver_classifies_every_ineligible_path() -> None:
    resolved = TemporalContextEligibilityResolver().resolve(
        _request(),
        _eligibility_policy(),
    )
    decisions = {item.record_id: item for item in resolved.decisions}

    assert {item.observation_id for item in resolved.request.observations} == {
        "OBS-1",
        "OBS-2",
    }
    assert {item.relationship_id for item in resolved.request.relationships} == {
        "REL-1"
    }
    assert EligibilityReason.FUTURE in decisions["OBS-FUTURE"].reasons
    assert EligibilityReason.RETRACTED in decisions["OBS-RETRACTED"].reasons
    assert EligibilityReason.HISTORICAL in decisions["OBS-HISTORICAL"].reasons
    assert EligibilityReason.DISPUTED in decisions["OBS-DISPUTED"].reasons
    assert EligibilityReason.CONTEXT_MISMATCH in decisions["OBS-CONTEXT"].reasons
    assert EligibilityReason.INELIGIBLE_ENDPOINT in decisions["REL-FUTURE"].reasons
    assert EligibilityReason.CONTEXT_MISMATCH in decisions["REL-CONTEXT"].reasons


def test_transactional_reconciliation_persists_only_eligible_findings(tmp_path) -> None:
    plan = GovernedReconciliationPlan.create(
        transaction_id="TX-REC-1",
        request=_request(),
        policy=_eligibility_policy(),
        execution_context=ExecutionContext.TEST,
        acceptable_authority_classes={"SUBJECT"},
    )
    approvals = JsonApprovalGrantRepository(tmp_path)
    approvals.save_new(_grant(plan.operation, "APR-REC-1"))
    records = JsonEnkiRecordRepository(tmp_path)
    transactions = JsonGovernedTransactionRepository(tmp_path)
    service = ExecuteGovernedReconciliation(
        engine=_engine(),
        finding_writer=records,
        approval_repository=approvals,
        journal=transactions,
        receipt_repository=transactions,
    )

    outcome = service.execute(plan, approval_id="APR-REC-1", now=_now())

    assert outcome.transaction_receipt.terminal_state == TransactionTerminalState.COMMITTED
    assert [item.finding_id for item in outcome.result.findings] == ["RF-REL-1"]
    assert records.get_finding("RF-REL-1") == outcome.result.findings[0]
    assert records.get_finding("RF-REL-FUTURE") is None
    assert approvals.get_approval(
        "APR-REC-1"
    ).consumption_status == ApprovalConsumptionStatus.CONSUMED


def test_reconciliation_recovers_after_finding_persistence_interruption(tmp_path) -> None:
    plan = GovernedReconciliationPlan.create(
        transaction_id="TX-REC-1",
        request=_request(),
        policy=_eligibility_policy(),
        execution_context=ExecutionContext.TEST,
        acceptable_authority_classes={"SUBJECT"},
    )
    approvals = JsonApprovalGrantRepository(tmp_path)
    approvals.save_new(_grant(plan.operation, "APR-REC-1"))
    records = JsonEnkiRecordRepository(tmp_path)
    transactions = JsonGovernedTransactionRepository(tmp_path)
    service = ExecuteGovernedReconciliation(
        engine=_engine(),
        finding_writer=records,
        approval_repository=approvals,
        journal=transactions,
        receipt_repository=transactions,
    )

    def fail(stage: TransactionStage) -> None:
        if stage == TransactionStage.EFFECT_APPLIED:
            raise OSError("reconciliation receipt boundary")

    with pytest.raises(OSError, match="receipt boundary"):
        service.execute(
            plan,
            approval_id="APR-REC-1",
            now=_now(),
            failure_hook=fail,
        )

    assert records.get_finding("RF-REL-1") is not None
    recovered = service.execute(plan, approval_id="APR-REC-1", now=_now())
    assert recovered.transaction_receipt.terminal_state == TransactionTerminalState.RECOVERED


def _reconciliation_result(tmp_path):
    plan = GovernedReconciliationPlan.create(
        transaction_id="TX-REC-1",
        request=_request(),
        policy=_eligibility_policy(),
        execution_context=ExecutionContext.TEST,
        acceptable_authority_classes={"SUBJECT"},
    )
    approvals = JsonApprovalGrantRepository(tmp_path)
    approvals.save_new(_grant(plan.operation, "APR-REC-1"))
    records = JsonEnkiRecordRepository(tmp_path)
    transactions = JsonGovernedTransactionRepository(tmp_path)
    service = ExecuteGovernedReconciliation(
        engine=_engine(),
        finding_writer=records,
        approval_repository=approvals,
        journal=transactions,
        receipt_repository=transactions,
    )
    return service.execute(plan, approval_id="APR-REC-1", now=_now()).result


def _protection_policy(
    *,
    sensitivity: SensitivityLevel = SensitivityLevel.PUBLIC,
    consent: DisclosureConsentState = DisclosureConsentState.GRANTED,
    allowed_audiences: set[DisclosureAudience] | None = None,
    allowed_purposes: set[str] | None = None,
    redaction_required_for: set[DisclosureAudience] | None = None,
    revoked_at: datetime | None = None,
) -> DisclosureProtectionPolicy:
    return DisclosureProtectionPolicy(
        policy_id="DP-1",
        policy_version="disclosure/v1",
        subject_id="PERSON-1",
        allowed_purposes=allowed_purposes or {"subject-review"},
        allowed_audiences=allowed_audiences or {
            DisclosureAudience.SUBJECT,
            DisclosureAudience.INTERNAL_OPERATOR,
            DisclosureAudience.PUBLIC,
        },
        sensitivity=sensitivity,
        consent_state=consent,
        redaction_required_for=redaction_required_for or set(),
        approved_by="PERSON-1",
        approved_at=_now() - timedelta(minutes=10),
        revoked_at=revoked_at,
    )


def _disclosure_plan(
    result,
    *,
    audience: DisclosureAudience = DisclosureAudience.SUBJECT,
    requested_by_subject: bool = True,
    policy: DisclosureProtectionPolicy | None = None,
    transaction_id: str = "TX-DISC-1",
    disclosure_id: str = "DISC-1",
) -> GovernedDisclosurePlan:
    return GovernedDisclosurePlan.create(
        transaction_id=transaction_id,
        result=result,
        disclosure_id=disclosure_id,
        audience=audience,
        purpose="subject-review",
        requested_finding_ids={"RF-REL-1"},
        requested_by_subject=requested_by_subject,
        protection_policy=policy or _protection_policy(),
        execution_context=ExecutionContext.TEST,
        acceptable_authority_classes={"SUBJECT"},
        requested_at=_now(),
    )


def _disclosure_service(tmp_path, plan: GovernedDisclosurePlan):
    approvals = JsonApprovalGrantRepository(tmp_path)
    approvals.save_new(_grant(plan.operation, "APR-DISC-1"))
    records = JsonEnkiRecordRepository(tmp_path)
    transactions = JsonGovernedTransactionRepository(tmp_path)
    service = ExecuteGovernedDisclosure(
        approval_repository=approvals,
        journal=transactions,
        transaction_receipt_repository=transactions,
        disclosure_receipt_writer=records,
    )
    return service, approvals, records, transactions


def test_subject_disclosure_is_separately_authorized_and_receipted(tmp_path) -> None:
    result = _reconciliation_result(tmp_path / "reconciliation")
    plan = _disclosure_plan(result)
    service, approvals, records, _ = _disclosure_service(tmp_path / "disclosure", plan)

    outcome = service.execute(plan, approval_id="APR-DISC-1", now=_now())

    assert outcome.result.receipt.surfaced_finding_ids == ["RF-REL-1"]
    assert outcome.result.receipt.withheld_finding_ids == []
    assert records.get_disclosure_receipt("DISC-1") == outcome.result.receipt
    assert approvals.get_approval(
        "APR-DISC-1"
    ).consumption_status == ApprovalConsumptionStatus.CONSUMED


def test_subject_disclosure_without_subject_request_is_withheld(tmp_path) -> None:
    result = _reconciliation_result(tmp_path / "reconciliation")
    plan = _disclosure_plan(result, requested_by_subject=False)
    service, _, _, _ = _disclosure_service(tmp_path / "disclosure", plan)

    outcome = service.execute(plan, approval_id="APR-DISC-1", now=_now())

    assert outcome.result.receipt.surfaced_finding_ids == []
    assert outcome.result.receipt.withheld_finding_ids == ["RF-REL-1"]
    assert "not requested by the subject" in outcome.result.receipt.decisions[0].reasons[0]


@pytest.mark.parametrize(
    ("policy", "reason_fragment"),
    [
        (
            _protection_policy(consent=DisclosureConsentState.REVOKED),
            "consent state is REVOKED",
        ),
        (
            _protection_policy(
                sensitivity=SensitivityLevel.PRIVATE,
                allowed_audiences={DisclosureAudience.PUBLIC},
            ),
            "PRIVATE material",
        ),
        (
            _protection_policy(
                redaction_required_for={DisclosureAudience.PUBLIC},
            ),
            "redaction is required",
        ),
        (
            _protection_policy(
                revoked_at=_now() - timedelta(seconds=1),
            ),
            "protection policy is revoked",
        ),
    ],
)
def test_protection_policy_withholds_unsafe_public_disclosure(
    tmp_path,
    policy: DisclosureProtectionPolicy,
    reason_fragment: str,
) -> None:
    result = _reconciliation_result(tmp_path / "reconciliation")
    plan = _disclosure_plan(
        result,
        audience=DisclosureAudience.PUBLIC,
        requested_by_subject=False,
        policy=policy,
    )
    service, _, records, _ = _disclosure_service(tmp_path / "disclosure", plan)

    outcome = service.execute(plan, approval_id="APR-DISC-1", now=_now())

    assert outcome.result.receipt.surfaced_finding_ids == []
    assert outcome.result.receipt.withheld_finding_ids == ["RF-REL-1"]
    assert any(
        reason_fragment in reason
        for reason in outcome.result.receipt.decisions[0].reasons
    )
    assert records.get_disclosure_receipt("DISC-1") == outcome.result.receipt


def test_disclosure_recovers_after_receipt_persistence_interruption(tmp_path) -> None:
    result = _reconciliation_result(tmp_path / "reconciliation")
    plan = _disclosure_plan(result)
    service, _, records, _ = _disclosure_service(tmp_path / "disclosure", plan)

    def fail(stage: TransactionStage) -> None:
        if stage == TransactionStage.EFFECT_APPLIED:
            raise OSError("disclosure transaction receipt boundary")

    with pytest.raises(OSError, match="receipt boundary"):
        service.execute(
            plan,
            approval_id="APR-DISC-1",
            now=_now(),
            failure_hook=fail,
        )

    assert records.get_disclosure_receipt("DISC-1") is not None
    recovered = service.execute(plan, approval_id="APR-DISC-1", now=_now())
    assert recovered.transaction_receipt.terminal_state == TransactionTerminalState.RECOVERED
    assert recovered.result.receipt.surfaced_finding_ids == ["RF-REL-1"]


def test_disclosure_approval_hash_mismatch_fails_before_receipt(tmp_path) -> None:
    result = _reconciliation_result(tmp_path / "reconciliation")
    plan = _disclosure_plan(result)
    approvals = JsonApprovalGrantRepository(tmp_path / "disclosure")
    wrong = _grant(plan.operation, "APR-DISC-1").model_copy(
        update={"content_sha256": _hash("wrong")}
    )
    approvals.save_new(wrong)
    records = JsonEnkiRecordRepository(tmp_path / "disclosure")
    transactions = JsonGovernedTransactionRepository(tmp_path / "disclosure")
    service = ExecuteGovernedDisclosure(
        approval_repository=approvals,
        journal=transactions,
        transaction_receipt_repository=transactions,
        disclosure_receipt_writer=records,
    )

    with pytest.raises(PermissionError, match="content hash does not match"):
        service.execute(plan, approval_id="APR-DISC-1", now=_now())

    assert records.get_disclosure_receipt("DISC-1") is None
