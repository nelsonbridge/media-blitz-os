from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from nks.adapters.approval_grants import JsonApprovalGrantRepository
from nks.adapters.enki_transitions import (
    EnkiTransitionRecordConflictError,
    JsonEnkiTransitionRepository,
)
from nks.adapters.governed_transactions import JsonGovernedTransactionRepository
from nks.application.governed_transactions import (
    GovernedTransactionReceipt,
    RecoveryStrategy,
    TransactionStage,
    TransactionTerminalState,
)
from nks.enki.contracts import SubjectRef
from nks.enki.transitions import (
    ConflictKind,
    ExecuteGovernedTransition,
    GovernedTransitionPlan,
    StateSnapshot,
    TransitionConflictError,
    TransitionPayload,
    TransitionReconstructionStatus,
    TransitionRecord,
    TransitionType,
    reconstruct_transition,
)
from nks.governance.approvals import (
    ApprovalConsumptionStatus,
    ApprovalDecision,
    ApprovalGrant,
    ExecutionContext,
)


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime(2026, 7, 14, 10, 0, tzinfo=timezone.utc)


def _subject(subject_type: str = "PROJECT") -> SubjectRef:
    return SubjectRef(subject_id=f"{subject_type}-1", subject_type=subject_type)


def _snapshot(
    state_id: str,
    *,
    subject: SubjectRef | None = None,
    content: str | None = None,
    context: list[str] | None = None,
) -> StateSnapshot:
    subject = subject or _subject()
    return StateSnapshot(
        state_id=state_id,
        subject=subject,
        domain="operations",
        content_sha256=_hash(content or state_id),
        observation_ids=[f"OBS-{state_id}"],
        relationship_ids=[],
        context=context or ["current"],
        temporal_status="CURRENT",
    )


def _payload(
    transition_type: TransitionType,
    from_states: list[StateSnapshot],
    to_states: list[StateSnapshot] | None = None,
    *,
    transition_id: str = "TR-1",
    authority_class: str = "SUBJECT",
    accepted_conflicts: set[ConflictKind] | None = None,
    subject: SubjectRef | None = None,
    required_context: set[str] | None = None,
) -> TransitionPayload:
    subject = subject or from_states[0].subject
    return TransitionPayload(
        transition_id=transition_id,
        transition_type=transition_type,
        subject=subject,
        domain="operations",
        from_states=from_states,
        to_states=to_states or [],
        reason=f"Execute {transition_type.value.lower()} transition.",
        evidence_ids=["E-1"],
        provenance_classification="REAL",
        authority_class=authority_class,
        interpretation_version="transition-test/v1",
        required_context=required_context or {"current"},
        accepted_conflicts=accepted_conflicts or set(),
        occurred_at=_now(),
    )


def _plan(
    payload: TransitionPayload,
    *,
    transaction_id: str = "TX-TR-1",
    context: ExecutionContext = ExecutionContext.TEST,
) -> GovernedTransitionPlan:
    return GovernedTransitionPlan.create(
        transaction_id=transaction_id,
        payload=payload,
        execution_context=context,
    )


def _grant(
    plan: GovernedTransitionPlan,
    *,
    approval_id: str = "APR-TR-1",
    context: ExecutionContext | None = None,
    authority_class: str | None = None,
) -> ApprovalGrant:
    return ApprovalGrant(
        approval_id=approval_id,
        decision=ApprovalDecision.APPROVED,
        execution_context=context or plan.operation.execution_context,
        permitted_actions={plan.operation.action},
        subject_id=plan.operation.subject_id,
        content_sha256=plan.operation.content_sha256,
        authorized_by=plan.operation.subject_id,
        authority_class=authority_class or plan.payload.authority_class,
        issued_at=_now() - timedelta(minutes=5),
        expires_at=_now() + timedelta(hours=1),
    )


def _service(tmp_path, plan: GovernedTransitionPlan):
    transitions = JsonEnkiTransitionRepository(tmp_path)
    for snapshot in plan.payload.from_states:
        transitions.append_seed_snapshot(snapshot)
    approvals = JsonApprovalGrantRepository(tmp_path)
    approvals.save_new(_grant(plan))
    transactions = JsonGovernedTransactionRepository(tmp_path)
    service = ExecuteGovernedTransition(
        transition_repository=transitions,
        state_reader=transitions,
        approval_repository=approvals,
        journal=transactions,
        receipt_repository=transactions,
    )
    return service, transitions, approvals, transactions


@pytest.mark.parametrize(
    "transition_type",
    [
        TransitionType.CORRECTION,
        TransitionType.REFINEMENT,
        TransitionType.SUPERSESSION,
        TransitionType.REVERSAL,
        TransitionType.EXPANSION,
        TransitionType.RESTRICTION,
        TransitionType.CONFIDENCE_CHANGE,
        TransitionType.CONTEXT_SHIFT,
    ],
)
def test_one_to_one_transition_types_commit(
    tmp_path,
    transition_type: TransitionType,
) -> None:
    source = _snapshot("A")
    target = _snapshot("B")
    plan = _plan(_payload(transition_type, [source], [target]))
    service, transitions, approvals, transactions = _service(tmp_path, plan)

    outcome = service.execute(plan, approval_id="APR-TR-1", now=_now())

    assert outcome.transaction_receipt.terminal_state == TransactionTerminalState.COMMITTED
    assert outcome.transition.before_sha256 == plan.payload.before_sha256
    assert outcome.transition.after_sha256 == plan.payload.after_sha256
    assert transitions.get_transition("TR-1") == outcome.transition
    assert transitions.get_snapshot("B") == target
    assert approvals.get_approval(
        "APR-TR-1"
    ).consumption_status == ApprovalConsumptionStatus.CONSUMED
    assert transactions.get_receipt("TX-TR-1") == outcome.transaction_receipt


@pytest.mark.parametrize(
    "transition_type",
    [TransitionType.RETRACTION, TransitionType.DEPRECATION],
)
def test_terminal_transition_types_commit_without_to_state(
    tmp_path,
    transition_type: TransitionType,
) -> None:
    source = _snapshot("A")
    plan = _plan(_payload(transition_type, [source]))
    service, transitions, _, _ = _service(tmp_path, plan)

    outcome = service.execute(plan, approval_id="APR-TR-1", now=_now())

    assert outcome.transition.to_states == []
    assert outcome.transition.after_sha256 == plan.payload.after_sha256
    assert transitions.get_transition("TR-1") == outcome.transition


def test_merge_transition_requires_multiple_sources_and_one_target(tmp_path) -> None:
    source_a = _snapshot("A")
    source_b = _snapshot("B")
    target = _snapshot("C")
    plan = _plan(_payload(TransitionType.MERGE, [source_a, source_b], [target]))
    service, transitions, _, _ = _service(tmp_path, plan)

    outcome = service.execute(plan, approval_id="APR-TR-1", now=_now())

    assert [state.state_id for state in outcome.transition.from_states] == ["A", "B"]
    assert transitions.get_snapshot("C") == target


def test_split_transition_requires_one_source_and_multiple_targets(tmp_path) -> None:
    source = _snapshot("A")
    target_b = _snapshot("B")
    target_c = _snapshot("C")
    plan = _plan(_payload(TransitionType.SPLIT, [source], [target_b, target_c]))
    service, transitions, _, _ = _service(tmp_path, plan)

    outcome = service.execute(plan, approval_id="APR-TR-1", now=_now())

    assert [state.state_id for state in outcome.transition.to_states] == ["B", "C"]
    assert transitions.get_snapshot("B") == target_b
    assert transitions.get_snapshot("C") == target_c


@pytest.mark.parametrize(
    ("transition_type", "from_count", "to_count", "message"),
    [
        (TransitionType.MERGE, 1, 1, "MERGE requires"),
        (TransitionType.SPLIT, 1, 1, "SPLIT requires"),
        (TransitionType.CORRECTION, 2, 1, "CORRECTION requires"),
        (TransitionType.RETRACTION, 1, 1, "RETRACTION cannot"),
    ],
)
def test_transition_cardinality_fails_closed(
    transition_type: TransitionType,
    from_count: int,
    to_count: int,
    message: str,
) -> None:
    from_states = [_snapshot(chr(ord("A") + index)) for index in range(from_count)]
    to_states = [
        _snapshot(chr(ord("X") + index)) for index in range(to_count)
    ]
    with pytest.raises(ValidationError, match=message):
        _payload(transition_type, from_states, to_states)


def test_unknown_from_state_fails_before_authority_consumption(tmp_path) -> None:
    source = _snapshot("A")
    target = _snapshot("B")
    plan = _plan(_payload(TransitionType.REFINEMENT, [source], [target]))
    transitions = JsonEnkiTransitionRepository(tmp_path)
    approvals = JsonApprovalGrantRepository(tmp_path)
    approvals.save_new(_grant(plan))
    transactions = JsonGovernedTransactionRepository(tmp_path)
    service = ExecuteGovernedTransition(
        transition_repository=transitions,
        state_reader=transitions,
        approval_repository=approvals,
        journal=transactions,
        receipt_repository=transactions,
    )

    with pytest.raises(ValueError, match="unknown from-state"):
        service.execute(plan, approval_id="APR-TR-1", now=_now())

    assert approvals.get_approval(
        "APR-TR-1"
    ).consumption_status == ApprovalConsumptionStatus.AVAILABLE


def test_stale_before_hash_is_rejected(tmp_path) -> None:
    actual = _snapshot("A", content="current")
    stale = _snapshot("A", content="stale")
    target = _snapshot("B")
    plan = _plan(_payload(TransitionType.REFINEMENT, [stale], [target]))
    service, transitions, approvals, _ = _service(tmp_path, plan)
    transitions.append_seed_snapshot(actual)

    with pytest.raises(TransitionConflictError) as exc:
        service.execute(plan, approval_id="APR-TR-1", now=_now())

    assert exc.value.conflicts == {ConflictKind.STALE_INPUT}
    assert approvals.get_approval(
        "APR-TR-1"
    ).consumption_status == ApprovalConsumptionStatus.AVAILABLE


def _execute_first_transition(tmp_path, *, authority_class: str = "SUBJECT"):
    source = _snapshot("A")
    target = _snapshot("B")
    first = _plan(
        _payload(
            TransitionType.REFINEMENT,
            [source],
            [target],
            transition_id="TR-1",
            authority_class=authority_class,
        ),
        transaction_id="TX-TR-1",
    )
    service, transitions, approvals, transactions = _service(tmp_path, first)
    service.execute(first, approval_id="APR-TR-1", now=_now())
    return source, target, transitions, approvals, transactions


def test_unaccepted_branch_fails_closed(tmp_path) -> None:
    source, _, transitions, approvals, transactions = _execute_first_transition(tmp_path)
    target_c = _snapshot("C")
    second = _plan(
        _payload(
            TransitionType.REFINEMENT,
            [source],
            [target_c],
            transition_id="TR-2",
        ),
        transaction_id="TX-TR-2",
    )
    approvals.save_new(_grant(second, approval_id="APR-TR-2"))
    service = ExecuteGovernedTransition(
        transition_repository=transitions,
        state_reader=transitions,
        approval_repository=approvals,
        journal=transactions,
        receipt_repository=transactions,
    )

    with pytest.raises(TransitionConflictError) as exc:
        service.execute(second, approval_id="APR-TR-2", now=_now())

    assert exc.value.conflicts == {ConflictKind.BRANCH}


def test_explicit_branch_is_recorded_not_silently_collapsed(tmp_path) -> None:
    source, _, transitions, approvals, transactions = _execute_first_transition(tmp_path)
    target_c = _snapshot("C")
    second = _plan(
        _payload(
            TransitionType.REFINEMENT,
            [source],
            [target_c],
            transition_id="TR-2",
            accepted_conflicts={ConflictKind.BRANCH},
        ),
        transaction_id="TX-TR-2",
    )
    approvals.save_new(_grant(second, approval_id="APR-TR-2"))
    service = ExecuteGovernedTransition(
        transition_repository=transitions,
        state_reader=transitions,
        approval_repository=approvals,
        journal=transactions,
        receipt_repository=transactions,
    )

    outcome = service.execute(second, approval_id="APR-TR-2", now=_now())

    assert outcome.transition.detected_conflicts == {ConflictKind.BRANCH}
    assert {item.transition_id for item in transitions.list_transitions(_subject(), "operations")} == {
        "TR-1",
        "TR-2",
    }


def test_explicit_overlap_is_recorded(tmp_path) -> None:
    source, target, transitions, approvals, transactions = _execute_first_transition(tmp_path)
    second = _plan(
        _payload(
            TransitionType.REFINEMENT,
            [source],
            [target],
            transition_id="TR-2",
            accepted_conflicts={ConflictKind.OVERLAP},
        ),
        transaction_id="TX-TR-2",
    )
    approvals.save_new(_grant(second, approval_id="APR-TR-2"))
    service = ExecuteGovernedTransition(
        transition_repository=transitions,
        state_reader=transitions,
        approval_repository=approvals,
        journal=transactions,
        receipt_repository=transactions,
    )

    outcome = service.execute(second, approval_id="APR-TR-2", now=_now())

    assert outcome.transition.detected_conflicts == {ConflictKind.OVERLAP}


def test_competing_authority_requires_explicit_branch_and_authority_conflict(tmp_path) -> None:
    source, _, transitions, approvals, transactions = _execute_first_transition(tmp_path)
    target_c = _snapshot("C")
    second = _plan(
        _payload(
            TransitionType.REFINEMENT,
            [source],
            [target_c],
            transition_id="TR-2",
            authority_class="STEWARD",
            accepted_conflicts={ConflictKind.BRANCH},
        ),
        transaction_id="TX-TR-2",
    )
    approvals.save_new(
        _grant(
            second,
            approval_id="APR-TR-2",
            authority_class="STEWARD",
        )
    )
    service = ExecuteGovernedTransition(
        transition_repository=transitions,
        state_reader=transitions,
        approval_repository=approvals,
        journal=transactions,
        receipt_repository=transactions,
    )

    with pytest.raises(TransitionConflictError) as exc:
        service.execute(second, approval_id="APR-TR-2", now=_now())
    assert exc.value.conflicts == {ConflictKind.AUTHORITY_CONFLICT}

    accepted = second.payload.model_copy(
        update={
            "transition_id": "TR-3",
            "accepted_conflicts": {
                ConflictKind.BRANCH,
                ConflictKind.AUTHORITY_CONFLICT,
            },
        }
    )
    accepted_plan = _plan(accepted, transaction_id="TX-TR-3")
    approvals.save_new(
        _grant(
            accepted_plan,
            approval_id="APR-TR-3",
            authority_class="STEWARD",
        )
    )
    outcome = service.execute(accepted_plan, approval_id="APR-TR-3", now=_now())
    assert outcome.transition.detected_conflicts == {
        ConflictKind.BRANCH,
        ConflictKind.AUTHORITY_CONFLICT,
    }


def test_cycle_is_unconditionally_rejected(tmp_path) -> None:
    _, target_b, transitions, approvals, transactions = _execute_first_transition(tmp_path)
    target_a = transitions.get_snapshot("A")
    assert target_a is not None
    cycle = _plan(
        _payload(
            TransitionType.REVERSAL,
            [target_b],
            [target_a],
            transition_id="TR-CYCLE",
        ),
        transaction_id="TX-CYCLE",
    )
    approvals.save_new(_grant(cycle, approval_id="APR-CYCLE"))
    service = ExecuteGovernedTransition(
        transition_repository=transitions,
        state_reader=transitions,
        approval_repository=approvals,
        journal=transactions,
        receipt_repository=transactions,
    )

    with pytest.raises(TransitionConflictError) as exc:
        service.execute(cycle, approval_id="APR-CYCLE", now=_now())

    assert ConflictKind.CYCLE in exc.value.conflicts


def test_existing_state_id_with_different_content_is_contradiction(tmp_path) -> None:
    source = _snapshot("A")
    existing_target = _snapshot("B", content="existing")
    proposed_target = _snapshot("B", content="different")
    plan = _plan(_payload(TransitionType.CORRECTION, [source], [proposed_target]))
    service, transitions, _, _ = _service(tmp_path, plan)
    transitions.append_seed_snapshot(existing_target)

    with pytest.raises(TransitionConflictError) as exc:
        service.execute(plan, approval_id="APR-TR-1", now=_now())

    assert exc.value.conflicts == {ConflictKind.CONTRADICTION}


def test_required_context_mismatch_is_rejected_during_plan_creation() -> None:
    source = _snapshot("A", context=["former"])
    target = _snapshot("B", context=["former"])
    with pytest.raises(ValidationError, match="context does not satisfy"):
        _payload(
            TransitionType.CONTEXT_SHIFT,
            [source],
            [target],
            required_context={"current"},
        )


def test_test_transition_cannot_consume_production_approval(tmp_path) -> None:
    source = _snapshot("A")
    target = _snapshot("B")
    plan = _plan(_payload(TransitionType.REFINEMENT, [source], [target]))
    transitions = JsonEnkiTransitionRepository(tmp_path)
    transitions.append_seed_snapshot(source)
    approvals = JsonApprovalGrantRepository(tmp_path)
    approvals.save_new(_grant(plan, context=ExecutionContext.PRODUCTION))
    transactions = JsonGovernedTransactionRepository(tmp_path)
    service = ExecuteGovernedTransition(
        transition_repository=transitions,
        state_reader=transitions,
        approval_repository=approvals,
        journal=transactions,
        receipt_repository=transactions,
    )

    with pytest.raises(PermissionError, match="execution context does not match"):
        service.execute(plan, approval_id="APR-TR-1", now=_now())

    assert transitions.get_transition("TR-1") is None


def test_plan_hash_tampering_is_rejected() -> None:
    source = _snapshot("A")
    target = _snapshot("B")
    plan = _plan(_payload(TransitionType.REFINEMENT, [source], [target]))
    tampered_operation = plan.operation.model_copy(
        update={"content_sha256": _hash("tampered")}
    )
    with pytest.raises(ValidationError, match="content hash does not match"):
        GovernedTransitionPlan(operation=tampered_operation, payload=plan.payload)


def test_interruption_after_transition_persistence_recovers_exactly(tmp_path) -> None:
    source = _snapshot("A")
    target = _snapshot("B")
    plan = _plan(_payload(TransitionType.REFINEMENT, [source], [target]))
    service, transitions, approvals, transactions = _service(tmp_path, plan)

    def fail(stage: TransactionStage) -> None:
        if stage == TransactionStage.EFFECT_APPLIED:
            raise OSError("transition receipt boundary")

    with pytest.raises(OSError, match="receipt boundary"):
        service.execute(
            plan,
            approval_id="APR-TR-1",
            now=_now(),
            failure_hook=fail,
        )

    assert transitions.get_transition("TR-1") is not None
    assert transactions.get_receipt("TX-TR-1") is None
    assert approvals.get_approval(
        "APR-TR-1"
    ).consumption_status == ApprovalConsumptionStatus.CONSUMED

    recovered = service.execute(plan, approval_id="APR-TR-1", now=_now())
    assert recovered.transaction_receipt.terminal_state == TransactionTerminalState.RECOVERED
    assert recovered.transaction_receipt.exact_retry is True
    assert len(transitions.list_transitions(_subject(), "operations")) == 1


def test_transition_id_cannot_be_replayed_under_another_transaction(tmp_path) -> None:
    source = _snapshot("A")
    target = _snapshot("B")
    plan = _plan(_payload(TransitionType.REFINEMENT, [source], [target]))
    service, _, approvals, _ = _service(tmp_path, plan)
    service.execute(plan, approval_id="APR-TR-1", now=_now())

    replay = _plan(plan.payload, transaction_id="TX-OTHER")
    approvals.save_new(_grant(replay, approval_id="APR-OTHER"))
    with pytest.raises(RuntimeError, match="different transaction"):
        service.execute(replay, approval_id="APR-OTHER", now=_now())


def test_transition_repository_rejects_immutable_record_conflicts(tmp_path) -> None:
    repository = JsonEnkiTransitionRepository(tmp_path)
    snapshot = _snapshot("A")
    repository.append_seed_snapshot(snapshot)
    changed = snapshot.model_copy(update={"content_sha256": _hash("changed")})
    with pytest.raises(EnkiTransitionRecordConflictError):
        repository.append_seed_snapshot(changed)


def test_person_subject_uses_generic_transition_engine(tmp_path) -> None:
    person = _subject("PERSON")
    source = _snapshot("PERSON-STATE-1", subject=person)
    target = _snapshot("PERSON-STATE-2", subject=person)
    plan = _plan(
        _payload(
            TransitionType.CORRECTION,
            [source],
            [target],
            subject=person,
        )
    )
    service, transitions, _, _ = _service(tmp_path, plan)

    outcome = service.execute(plan, approval_id="APR-TR-1", now=_now())

    assert outcome.transition.subject.subject_type == "PERSON"
    assert transitions.get_snapshot("PERSON-STATE-2") == target


def test_reconstruction_statuses_are_deterministic(tmp_path) -> None:
    source = _snapshot("A")
    target = _snapshot("B")
    plan = _plan(_payload(TransitionType.REFINEMENT, [source], [target]))
    service, transitions, _, transactions = _service(tmp_path, plan)
    outcome = service.execute(plan, approval_id="APR-TR-1", now=_now())

    complete = reconstruct_transition(
        plan,
        record=outcome.transition,
        receipt=outcome.transaction_receipt,
    )
    assert complete.status == TransitionReconstructionStatus.COMPLETE

    incomplete = reconstruct_transition(plan, record=None, receipt=None)
    assert incomplete.status == TransitionReconstructionStatus.INCOMPLETE

    repairable = reconstruct_transition(
        plan,
        record=outcome.transition,
        receipt=None,
    )
    assert repairable.status == TransitionReconstructionStatus.REPAIRABLE

    receipt_without_record = reconstruct_transition(
        plan,
        record=None,
        receipt=outcome.transaction_receipt,
    )
    assert receipt_without_record.status == TransitionReconstructionStatus.CONFLICT

    tampered_record = outcome.transition.model_copy(
        update={"after_sha256": _hash("tampered")}
    )
    conflict = reconstruct_transition(
        plan,
        record=tampered_record,
        receipt=outcome.transaction_receipt,
    )
    assert conflict.status == TransitionReconstructionStatus.CONFLICT

    rolled_back_receipt = GovernedTransactionReceipt(
        receipt_id="GTR-ROLLBACK",
        operation_id="enki-transition",
        transaction_id=plan.operation.transaction_id,
        plan_sha256=plan.operation.plan_sha256,
        approval_id="APR-TR-1",
        execution_context=ExecutionContext.TEST,
        terminal_state=TransactionTerminalState.ROLLED_BACK,
        recovery_strategy=RecoveryStrategy.RELEASE_RESERVATION,
        output_sha256=None,
        recorded_at=_now(),
    )
    rolled_back = reconstruct_transition(
        plan,
        record=None,
        receipt=rolled_back_receipt,
    )
    assert rolled_back.status == TransitionReconstructionStatus.ROLLED_BACK

    assert transitions.get_transition("TR-1") is not None
    assert transactions.get_receipt("TX-TR-1") is not None
