from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from nks.adapters.approval_grants import JsonApprovalGrantRepository
from nks.adapters.governed_transactions import JsonGovernedTransactionRepository
from nks.application.governed_transactions import (
    GovernedTransactionExecutor,
    TransactionStage,
    TransactionTerminalState,
)
from nks.application.work_control_amendment import (
    AtomicWorkControlAmendmentRepository,
    EvidenceQualification,
    QualifiedCompletionEvidence,
    WorkControlAmendmentPlan,
    build_completion_amendment,
    execute_governed_work_control_amendment,
)
from nks.domain.work_control import BacklogItem, EvidenceKind, SprintRecord, WorkEvidence, WorkStatus
from nks.governance.approvals import (
    ApprovalConsumptionStatus,
    ApprovalDecision,
    ApprovalGrant,
    ExecutionContext,
)


NOW = datetime(2026, 7, 14, 17, 0, tzinfo=timezone.utc)


def _records() -> tuple[SprintRecord, BacklogItem]:
    sprint = SprintRecord(
        sprint_id="NKS-SPR-099",
        sequence=99,
        title="Disposable TEST sprint",
        objective="Prove governed completion without mutating repository authority.",
        status=WorkStatus.PLANNED,
        work_item_ids=["BL-099"],
        exit_criteria=["Exact evidence is required"],
        evidence=[],
        updated_at=NOW - timedelta(hours=1),
    )
    item = BacklogItem(
        work_item_id="BL-099",
        title="Disposable TEST work item",
        description="TEST-only work-control amendment fixture.",
        status=WorkStatus.PLANNED,
        sprint_id=sprint.sprint_id,
        acceptance_criteria=["Exact evidence is required"],
        evidence=[],
        updated_at=NOW - timedelta(hours=1),
    )
    return sprint, item


def _binding(name: str, qualification: EvidenceQualification) -> QualifiedCompletionEvidence:
    kind = EvidenceKind.TEST_RUN
    if qualification == EvidenceQualification.IMPLEMENTATION:
        kind = EvidenceKind.COMMIT
    elif qualification == EvidenceQualification.AUTHORITY:
        kind = EvidenceKind.HUMAN_DECISION
    return QualifiedCompletionEvidence(
        evidence=WorkEvidence(
            evidence_id=f"E-{name}",
            kind=kind,
            reference=f"https://example.invalid/{name}",
            description=f"Qualifying {qualification.value} evidence.",
        ),
        qualification=qualification,
        artifact_sha256="sha256:" + (name.encode().hex() * 64)[:64],
    )


def _evidence() -> list[QualifiedCompletionEvidence]:
    return [
        _binding("implementation", EvidenceQualification.IMPLEMENTATION),
        _binding("coverage", EvidenceQualification.PATH_COVERAGE),
        _binding("validation", EvidenceQualification.VALIDATION),
        _binding("authority", EvidenceQualification.AUTHORITY),
    ]


def _amendment() -> WorkControlAmendmentPlan:
    sprint, item = _records()
    return build_completion_amendment(
        amendment_id="AMEND-1",
        transaction_id="TX-AMEND-1",
        current_sprint=sprint,
        current_work_item=item,
        evidence=_evidence(),
        acceptable_authority_classes={"HUMAN_ORIGIN_AUTHORITY"},
        requested_at=NOW,
    )


def _executor(tmp_path):
    approvals = JsonApprovalGrantRepository(tmp_path)
    transactions = JsonGovernedTransactionRepository(tmp_path)
    executor = GovernedTransactionExecutor(
        approval_repository=approvals,
        journal=transactions,
        receipt_repository=transactions,
    )
    return approvals, transactions, executor


def _grant(amendment: WorkControlAmendmentPlan) -> ApprovalGrant:
    return ApprovalGrant(
        approval_id="APPROVAL-AMEND-1",
        decision=ApprovalDecision.APPROVED,
        execution_context=ExecutionContext.TEST,
        permitted_actions={"work-control:amend"},
        subject_id=amendment.target_sprint.sprint_id,
        content_sha256=amendment.plan_sha256,
        authorized_by="HUMAN-ORIGIN-AUTHORITY",
        authority_class="HUMAN_ORIGIN_AUTHORITY",
        issued_at=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(hours=1),
    )


def test_completion_requires_all_four_qualification_classes() -> None:
    sprint, item = _records()
    with pytest.raises(ValidationError, match="implementation, path coverage, validation, and authority"):
        build_completion_amendment(
            amendment_id="AMEND-1",
            transaction_id="TX-AMEND-1",
            current_sprint=sprint,
            current_work_item=item,
            evidence=_evidence()[:-1],
            acceptable_authority_classes={"HUMAN_ORIGIN_AUTHORITY"},
            requested_at=NOW,
        )


def test_governed_completion_consumes_exact_authority_and_updates_pair(tmp_path) -> None:
    amendment = _amendment()
    sprint, item = _records()
    repository = AtomicWorkControlAmendmentRepository(tmp_path)
    repository.seed(sprint, item)
    approvals, transactions, executor = _executor(tmp_path)
    approvals.save_new(_grant(amendment))

    receipt = execute_governed_work_control_amendment(
        amendment,
        approval_id="APPROVAL-AMEND-1",
        transaction_executor=executor,
        repository=repository,
        now=NOW,
    )
    assert receipt.terminal_state == TransactionTerminalState.COMMITTED
    assert repository.get_sprint(sprint.sprint_id).status == WorkStatus.COMPLETE
    assert repository.get_work_item(item.work_item_id).status == WorkStatus.COMPLETE
    assert approvals.get_approval("APPROVAL-AMEND-1").consumption_status == ApprovalConsumptionStatus.CONSUMED
    assert transactions.get_receipt(amendment.transaction_id) == receipt


def test_stale_before_hash_fails_closed(tmp_path) -> None:
    amendment = _amendment()
    sprint, item = _records()
    repository = AtomicWorkControlAmendmentRepository(tmp_path)
    repository.seed(sprint.model_copy(update={"title": "stale mutation"}), item)
    with pytest.raises(RuntimeError, match="stale or conflicts"):
        repository.apply(amendment)


def test_failure_before_consumption_releases_reservation_and_leaves_records_planned(tmp_path) -> None:
    amendment = _amendment()
    sprint, item = _records()
    repository = AtomicWorkControlAmendmentRepository(tmp_path)
    repository.seed(sprint, item)
    approvals, transactions, executor = _executor(tmp_path)
    approvals.save_new(_grant(amendment))

    def fail(stage: TransactionStage) -> None:
        if stage == TransactionStage.APPROVAL_RESERVED:
            raise RuntimeError("injected-before-consumption")

    with pytest.raises(RuntimeError, match="injected-before-consumption"):
        execute_governed_work_control_amendment(
            amendment,
            approval_id="APPROVAL-AMEND-1",
            transaction_executor=executor,
            repository=repository,
            now=NOW,
            failure_hook=fail,
        )
    assert repository.get_sprint(sprint.sprint_id).status == WorkStatus.PLANNED
    assert repository.get_work_item(item.work_item_id).status == WorkStatus.PLANNED
    assert approvals.get_approval("APPROVAL-AMEND-1").consumption_status == ApprovalConsumptionStatus.AVAILABLE
    assert transactions.get_receipt(amendment.transaction_id).terminal_state == TransactionTerminalState.ROLLED_BACK


def test_partial_two_record_write_recovers_by_same_consumed_transaction(tmp_path) -> None:
    amendment = _amendment()
    sprint, item = _records()
    raised = False

    def fail_once(stage: str) -> None:
        nonlocal raised
        if stage == "after-sprint-replace" and not raised:
            raised = True
            raise RuntimeError("injected-partial-work-control-write")

    repository = AtomicWorkControlAmendmentRepository(tmp_path, failure_hook=fail_once)
    repository.seed(sprint, item)
    approvals, _transactions, executor = _executor(tmp_path)
    approvals.save_new(_grant(amendment))

    with pytest.raises(RuntimeError, match="partial-work-control-write"):
        execute_governed_work_control_amendment(
            amendment,
            approval_id="APPROVAL-AMEND-1",
            transaction_executor=executor,
            repository=repository,
            now=NOW,
        )
    assert repository.get_sprint(sprint.sprint_id).status == WorkStatus.COMPLETE
    assert repository.get_work_item(item.work_item_id).status == WorkStatus.PLANNED

    recovered = execute_governed_work_control_amendment(
        amendment,
        approval_id="APPROVAL-AMEND-1",
        transaction_executor=executor,
        repository=repository,
        now=NOW,
    )
    assert recovered.terminal_state == TransactionTerminalState.RECOVERED
    assert recovered.exact_retry is True
    assert repository.get_work_item(item.work_item_id).status == WorkStatus.COMPLETE


def test_failure_after_consumption_before_apply_recovers_exactly(tmp_path) -> None:
    amendment = _amendment()
    sprint, item = _records()
    repository = AtomicWorkControlAmendmentRepository(tmp_path)
    repository.seed(sprint, item)
    approvals, _transactions, executor = _executor(tmp_path)
    approvals.save_new(_grant(amendment))

    def fail(stage: TransactionStage) -> None:
        if stage == TransactionStage.APPROVAL_CONSUMED:
            raise RuntimeError("injected-after-consumption")

    with pytest.raises(RuntimeError, match="after-consumption"):
        execute_governed_work_control_amendment(
            amendment,
            approval_id="APPROVAL-AMEND-1",
            transaction_executor=executor,
            repository=repository,
            now=NOW,
            failure_hook=fail,
        )
    recovered = execute_governed_work_control_amendment(
        amendment,
        approval_id="APPROVAL-AMEND-1",
        transaction_executor=executor,
        repository=repository,
        now=NOW,
    )
    assert recovered.terminal_state == TransactionTerminalState.RECOVERED
    assert repository.get_sprint(sprint.sprint_id).status == WorkStatus.COMPLETE
