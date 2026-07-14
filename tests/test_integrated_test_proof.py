from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from nks.application.forensic_contracts import ReconstructionStatus
from nks.application.governed_transactions import (
    GovernedOperationPlan,
    GovernedTransactionEvent,
    GovernedTransactionExecutor,
    GovernedTransactionReceipt,
    TransactionStage,
    TransactionTerminalState,
    canonical_sha256,
)
from nks.application.integrated_test_proof import (
    AdaptiveLoopReceipt,
    EnkiReleaseCandidate,
    FeedbackDisposition,
    FeedbackEnvelope,
    FeedbackProcessor,
    FeedbackProvenance,
    HumanReleaseDecisionOption,
    HumanReleaseDecisionRequest,
    IntegratedTestProofRunner,
    NoEffectProofAdapter,
    ProofLaneKind,
    ProofLanePlan,
    build_release_candidate,
)
from nks.enki.contracts import SubjectRef
from nks.governance.approvals import (
    ApprovalConsumptionStatus,
    ApprovalDecision,
    ApprovalGrant,
    ExecutionContext,
)


def _now() -> datetime:
    return datetime(2026, 7, 14, 13, 30, tzinfo=timezone.utc)


def _hash(value: object) -> str:
    return canonical_sha256(value)


def _publication_lane() -> ProofLanePlan:
    return ProofLanePlan(
        lane_id="LANE-PUBLICATION-001",
        lane_kind=ProofLaneKind.PUBLICATION,
        subject=SubjectRef(subject_id="PUB-001", subject_type="PUBLICATION"),
        domain="media-publication",
        purpose="internal-publication-shaped-proof",
        artifact_hashes={
            "content": _hash("content"),
            "visual:hero": _hash("hero"),
            "visual:carousel": _hash("carousel"),
            "configuration": _hash("config"),
            "identity": _hash("identity"),
            "byline": _hash("byline"),
            "brand": _hash("brand"),
            "channel": _hash("channel"),
            "review": _hash("review"),
        },
        requested_at=_now(),
    )


def _nonpublication_lane() -> ProofLanePlan:
    return ProofLanePlan(
        lane_id="LANE-ORGANIZATION-001",
        lane_kind=ProofLaneKind.NONPUBLICATION,
        subject=SubjectRef(subject_id="ORG-001", subject_type="ORGANIZATION"),
        domain="operating-model",
        purpose="internal-adaptive-proof",
        artifact_hashes={"payload": _hash("organization-payload")},
        requested_at=_now(),
    )


def _feedback(
    feedback_id: str,
    *,
    target: str = "PUB-001",
    content: str = "useful feedback",
    provenance: FeedbackProvenance = FeedbackProvenance.SYNTHETIC_TEST,
    context: ExecutionContext = ExecutionContext.TEST,
    replay_of: str | None = None,
    metadata: dict[str, object] | None = None,
) -> FeedbackEnvelope:
    return FeedbackEnvelope(
        feedback_id=feedback_id,
        provenance=provenance,
        execution_context=context,
        source_id=f"SOURCE-{feedback_id}",
        target_subject_id=target,
        content=content,
        content_sha256=_hash(content),
        received_at=_now(),
        authority_class="TEST-HARNESS",
        replay_of=replay_of,
        metadata=metadata or {},
    )


class MemoryApprovalRepository:
    def __init__(self) -> None:
        self.grants: dict[str, ApprovalGrant] = {}

    def save(self, grant: ApprovalGrant) -> None:
        self.grants[grant.approval_id] = grant

    def get_approval(self, approval_id: str) -> ApprovalGrant | None:
        return self.grants.get(approval_id)

    def compare_and_swap_approval(
        self,
        expected: ApprovalGrant,
        replacement: ApprovalGrant,
    ) -> bool:
        current = self.grants.get(expected.approval_id)
        if current != expected:
            return False
        self.grants[expected.approval_id] = replacement
        return True


class MemoryJournal:
    def __init__(self) -> None:
        self.events: list[GovernedTransactionEvent] = []

    def append_event(self, event: GovernedTransactionEvent) -> None:
        existing = next((item for item in self.events if item.event_id == event.event_id), None)
        if existing is not None and existing != event:
            raise RuntimeError("event conflict")
        if existing is None:
            self.events.append(event)

    def list_events(self, transaction_id: str) -> list[GovernedTransactionEvent]:
        return [item for item in self.events if item.transaction_id == transaction_id]


class MemoryReceiptRepository:
    def __init__(self) -> None:
        self.receipts: dict[str, GovernedTransactionReceipt] = {}

    def get_receipt(self, transaction_id: str) -> GovernedTransactionReceipt | None:
        return self.receipts.get(transaction_id)

    def append_receipt(self, receipt: GovernedTransactionReceipt) -> None:
        existing = self.receipts.get(receipt.transaction_id)
        if existing is not None and existing != receipt:
            raise RuntimeError("receipt conflict")
        self.receipts[receipt.transaction_id] = receipt


def _grant(
    lane: ProofLanePlan,
    transaction_id: str,
    approval_id: str,
    *,
    context: ExecutionContext = ExecutionContext.TEST,
) -> ApprovalGrant:
    plan = IntegratedTestProofRunner.operation_plan(
        lane,
        transaction_id=transaction_id,
        acceptable_authority_classes={"TEST-HARNESS"},
    )
    return ApprovalGrant(
        approval_id=approval_id,
        decision=ApprovalDecision.APPROVED,
        execution_context=context,
        permitted_actions={plan.action},
        subject_id=plan.subject_id,
        content_sha256=plan.content_sha256,
        authorized_by="SPRINT-13-TEST-HARNESS",
        authority_class="TEST-HARNESS",
        issued_at=_now() - timedelta(minutes=5),
        expires_at=_now() + timedelta(hours=1),
    )


def _runner(
    grants: list[ApprovalGrant],
) -> tuple[
    IntegratedTestProofRunner,
    MemoryApprovalRepository,
    MemoryJournal,
    MemoryReceiptRepository,
]:
    approvals = MemoryApprovalRepository()
    for grant in grants:
        approvals.save(grant)
    journal = MemoryJournal()
    receipts = MemoryReceiptRepository()
    executor = GovernedTransactionExecutor(
        approval_repository=approvals,
        journal=journal,
        receipt_repository=receipts,
    )
    return IntegratedTestProofRunner(executor), approvals, journal, receipts


def _release_artifacts() -> dict[str, str]:
    return {
        "calibration-report": _hash("calibration"),
        "threat-model": _hash("threat-model"),
        "runbook": _hash("runbook"),
        "known-limitations": _hash("limitations"),
        "rollback-package": _hash("rollback"),
        "release-notes": _hash("release-notes"),
        "evidence-manifest": _hash("evidence-manifest"),
    }


def test_two_adaptive_test_loops_build_hash_bound_release_candidate() -> None:
    publication = _publication_lane()
    organization = _nonpublication_lane()
    runner, approvals, _, _ = _runner(
        [
            _grant(publication, "TX-PUB", "APR-PUB"),
            _grant(organization, "TX-ORG", "APR-ORG"),
        ]
    )

    publication_receipt = runner.run(
        publication,
        transaction_id="TX-PUB",
        approval_id="APR-PUB",
        acceptable_authority_classes={"TEST-HARNESS"},
        feedback=[
            _feedback("FB-SYNTHETIC"),
            _feedback(
                "FB-REPLAY",
                content="replayed evidence",
                provenance=FeedbackProvenance.REPLAY_TEST,
                replay_of="FB-ORIGINAL",
            ),
        ],
    )
    organization_receipt = runner.run(
        organization,
        transaction_id="TX-ORG",
        approval_id="APR-ORG",
        acceptable_authority_classes={"TEST-HARNESS"},
        feedback=[
            _feedback(
                "FB-CONTROLLED-REAL",
                target="ORG-001",
                content="controlled human response",
                provenance=FeedbackProvenance.CONTROLLED_REAL_TEST,
            )
        ],
    )

    for receipt in (publication_receipt, organization_receipt):
        assert receipt.transaction_receipt.terminal_state == TransactionTerminalState.COMMITTED
        assert receipt.reconstruction.status == ReconstructionStatus.COMPLETE
        assert receipt.external_effect is False
        assert receipt.distribution is not None
        assert receipt.distribution.external_effect is False

    assert publication_receipt.calibration is not None
    assert publication_receipt.calibration.provenance_counts == {
        FeedbackProvenance.REPLAY_TEST.value: 1,
        FeedbackProvenance.SYNTHETIC_TEST.value: 1,
    }
    assert organization_receipt.calibration is not None
    assert organization_receipt.calibration.provenance_counts == {
        FeedbackProvenance.CONTROLLED_REAL_TEST.value: 1
    }
    assert approvals.grants["APR-PUB"].consumption_status == ApprovalConsumptionStatus.CONSUMED
    assert approvals.grants["APR-ORG"].consumption_status == ApprovalConsumptionStatus.CONSUMED

    candidate, decision_request = build_release_candidate(
        [publication_receipt, organization_receipt],
        candidate_id="ENKI-0.1.0-RC1",
        version="0.1.0-rc1",
        source_commit_sha="a" * 40,
        artifact_hashes=_release_artifacts(),
        created_at=_now(),
    )

    assert candidate.external_effect is False
    assert candidate.manifest.source_commit_sha == "a" * 40
    assert candidate.candidate_sha256 == _hash(candidate.manifest)
    assert decision_request.decision is None
    assert set(decision_request.options) == set(HumanReleaseDecisionOption)


def test_lane_contracts_fail_closed_on_missing_artifacts_and_production_context() -> None:
    publication_payload = _publication_lane().model_dump(mode="python")
    publication_payload["artifact_hashes"] = {"content": _hash("content")}
    with pytest.raises(ValidationError, match="missing artifacts"):
        ProofLanePlan.model_validate(publication_payload)

    no_visual = _publication_lane().model_dump(mode="python")
    no_visual["artifact_hashes"] = {
        key: value
        for key, value in no_visual["artifact_hashes"].items()
        if not key.startswith("visual:")
    }
    with pytest.raises(ValidationError, match="at least one visual"):
        ProofLanePlan.model_validate(no_visual)

    nonpublication = _nonpublication_lane().model_dump(mode="python")
    nonpublication["artifact_hashes"] = {"other": _hash("other")}
    with pytest.raises(ValidationError, match="requires a payload"):
        ProofLanePlan.model_validate(nonpublication)

    production = _publication_lane().model_dump(mode="python")
    production["execution_context"] = ExecutionContext.PRODUCTION
    with pytest.raises(ValidationError, match="TEST-only"):
        ProofLanePlan.model_validate(production)


def test_no_effect_adapter_has_no_transport_surface_and_rejects_tamper() -> None:
    lane = _publication_lane()
    adapter = NoEffectProofAdapter(lane)
    plan = IntegratedTestProofRunner.operation_plan(
        lane,
        transaction_id="TX-PUB",
        acceptable_authority_classes={"TEST-HARNESS"},
    )

    first = adapter.apply(plan)
    second = adapter.apply(plan)
    assert first == second
    assert adapter.effect_count == 1
    assert not hasattr(adapter, "transport")
    assert not hasattr(adapter, "credentials")
    assert not hasattr(adapter, "endpoint")
    assert not hasattr(adapter, "callback")

    tampered = plan.model_copy(update={"content_sha256": _hash("tampered")})
    with pytest.raises(PermissionError, match="content"):
        adapter.apply(tampered)

    production = plan.model_copy(update={"execution_context": ExecutionContext.PRODUCTION})
    with pytest.raises(PermissionError, match="context"):
        adapter.apply(production)


def test_feedback_taxonomy_is_attributable_deduplicated_and_context_bound() -> None:
    processor = FeedbackProcessor()
    target = "PUB-001"

    accepted = processor.process(target, _feedback("FB-1", content="accepted"))
    duplicate_id = processor.process(target, _feedback("FB-1", content="accepted"))
    conflict_id = processor.process(target, _feedback("FB-1", content="changed"))
    duplicate_content = processor.process(target, _feedback("FB-2", content="accepted"))
    replay_missing = processor.process(
        target,
        _feedback(
            "FB-3",
            content="replay without origin",
            provenance=FeedbackProvenance.REPLAY_TEST,
        ),
    )
    irrelevant = processor.process(
        target,
        _feedback("FB-4", content="irrelevant", metadata={"relevant": False}),
    )
    contradictory = processor.process(
        target,
        _feedback("FB-5", content="contradiction", metadata={"contradictory": True}),
    )
    adversarial = processor.process(
        target,
        _feedback("FB-6", content="attack", metadata={"adversarial": True}),
    )
    unauthorized = processor.process(
        target,
        _feedback("FB-7", content="production", context=ExecutionContext.PRODUCTION),
    )
    mismatched = processor.process(
        target,
        _feedback("FB-8", target="OTHER", content="wrong subject"),
    )
    malformed = processor.process(target, _feedback("FB-9", content="   "))
    zero = processor.process_batch(target, [], zero_response=True)

    assert accepted.disposition == FeedbackDisposition.ACCEPTED
    assert duplicate_id.disposition == FeedbackDisposition.DUPLICATE
    assert conflict_id.disposition == FeedbackDisposition.CONFLICT
    assert duplicate_content.disposition == FeedbackDisposition.DUPLICATE
    assert replay_missing.disposition == FeedbackDisposition.MALFORMED
    assert irrelevant.disposition == FeedbackDisposition.IRRELEVANT
    assert contradictory.disposition == FeedbackDisposition.CONTRADICTORY
    assert adversarial.disposition == FeedbackDisposition.ADVERSARIAL
    assert unauthorized.disposition == FeedbackDisposition.UNAUTHORIZED
    assert mismatched.disposition == FeedbackDisposition.MISMATCHED
    assert malformed.disposition == FeedbackDisposition.MALFORMED
    assert zero[0].disposition == FeedbackDisposition.ZERO_RESPONSE

    with pytest.raises(ValueError, match="zero_response"):
        processor.process_batch(target, [_feedback("FB-10")], zero_response=True)


def test_interruption_after_effect_recovers_without_duplicate_distribution() -> None:
    lane = _publication_lane()
    runner, approvals, journal, receipts = _runner(
        [_grant(lane, "TX-RECOVER", "APR-RECOVER")]
    )

    def fail(stage: TransactionStage) -> None:
        if stage == TransactionStage.EFFECT_APPLIED:
            raise OSError("injected after no-effect distribution")

    with pytest.raises(OSError, match="injected"):
        runner.run(
            lane,
            transaction_id="TX-RECOVER",
            approval_id="APR-RECOVER",
            acceptable_authority_classes={"TEST-HARNESS"},
            feedback=[_feedback("FB-RECOVER")],
            failure_hook=fail,
        )

    assert runner.effect_count("TX-RECOVER") == 1
    assert receipts.get_receipt("TX-RECOVER") is None
    assert approvals.grants["APR-RECOVER"].consumption_status == ApprovalConsumptionStatus.CONSUMED
    assert TransactionStage.RECOVERY_REQUIRED in {
        item.stage for item in journal.list_events("TX-RECOVER")
    }

    recovered = runner.run(
        lane,
        transaction_id="TX-RECOVER",
        approval_id="APR-RECOVER",
        acceptable_authority_classes={"TEST-HARNESS"},
        feedback=[_feedback("FB-RECOVER")],
    )
    assert recovered.transaction_receipt.terminal_state == TransactionTerminalState.RECOVERED
    assert recovered.transaction_receipt.exact_retry is True
    assert recovered.reconstruction.status == ReconstructionStatus.COMPLETE
    assert runner.effect_count("TX-RECOVER") == 1


def test_interruption_before_consumption_rolls_back_without_effect() -> None:
    lane = _nonpublication_lane()
    runner, approvals, journal, receipts = _runner(
        [_grant(lane, "TX-ROLLBACK", "APR-ROLLBACK")]
    )

    def fail(stage: TransactionStage) -> None:
        if stage == TransactionStage.APPROVAL_RESERVED:
            raise OSError("injected before authority consumption")

    with pytest.raises(OSError, match="injected"):
        runner.run(
            lane,
            transaction_id="TX-ROLLBACK",
            approval_id="APR-ROLLBACK",
            acceptable_authority_classes={"TEST-HARNESS"},
            failure_hook=fail,
        )

    assert approvals.grants["APR-ROLLBACK"].consumption_status == ApprovalConsumptionStatus.AVAILABLE
    assert receipts.get_receipt("TX-ROLLBACK") is not None
    assert receipts.get_receipt("TX-ROLLBACK").terminal_state == TransactionTerminalState.ROLLED_BACK
    assert runner.effect_count("TX-ROLLBACK") == 0
    assert TransactionStage.ROLLED_BACK in {
        item.stage for item in journal.list_events("TX-ROLLBACK")
    }

    rolled_back = runner.run(
        lane,
        transaction_id="TX-ROLLBACK",
        approval_id="APR-ROLLBACK",
        acceptable_authority_classes={"TEST-HARNESS"},
    )
    assert rolled_back.transaction_receipt.terminal_state == TransactionTerminalState.ROLLED_BACK
    assert rolled_back.reconstruction.status == ReconstructionStatus.ROLLED_BACK
    assert rolled_back.distribution is None


def test_test_approval_cannot_be_replaced_by_production_authority() -> None:
    lane = _publication_lane()
    runner, approvals, _, _ = _runner(
        [
            _grant(
                lane,
                "TX-CONTEXT",
                "APR-CONTEXT",
                context=ExecutionContext.PRODUCTION,
            )
        ]
    )

    with pytest.raises(PermissionError, match="execution context does not match"):
        runner.run(
            lane,
            transaction_id="TX-CONTEXT",
            approval_id="APR-CONTEXT",
            acceptable_authority_classes={"TEST-HARNESS"},
        )
    assert approvals.grants["APR-CONTEXT"].consumption_status == ApprovalConsumptionStatus.AVAILABLE


def test_release_candidate_rejects_missing_evidence_bad_commit_and_tamper() -> None:
    publication = _publication_lane()
    organization = _nonpublication_lane()
    runner, _, _, _ = _runner(
        [
            _grant(publication, "TX-PUB-RC", "APR-PUB-RC"),
            _grant(organization, "TX-ORG-RC", "APR-ORG-RC"),
        ]
    )
    loops = [
        runner.run(
            publication,
            transaction_id="TX-PUB-RC",
            approval_id="APR-PUB-RC",
            acceptable_authority_classes={"TEST-HARNESS"},
            zero_response=True,
        ),
        runner.run(
            organization,
            transaction_id="TX-ORG-RC",
            approval_id="APR-ORG-RC",
            acceptable_authority_classes={"TEST-HARNESS"},
            zero_response=True,
        ),
    ]

    with pytest.raises(ValueError, match="at least two"):
        build_release_candidate(
            loops[:1],
            candidate_id="RC",
            version="0.1.0-rc1",
            source_commit_sha="a" * 40,
            artifact_hashes=_release_artifacts(),
            created_at=_now(),
        )

    missing = _release_artifacts()
    missing.pop("threat-model")
    with pytest.raises(ValidationError, match="missing artifacts"):
        build_release_candidate(
            loops,
            candidate_id="RC",
            version="0.1.0-rc1",
            source_commit_sha="a" * 40,
            artifact_hashes=missing,
            created_at=_now(),
        )

    with pytest.raises(ValidationError, match="source_commit_sha"):
        build_release_candidate(
            loops,
            candidate_id="RC",
            version="0.1.0-rc1",
            source_commit_sha="short",
            artifact_hashes=_release_artifacts(),
            created_at=_now(),
        )

    candidate, request = build_release_candidate(
        loops,
        candidate_id="RC",
        version="0.1.0-rc1",
        source_commit_sha="a" * 40,
        artifact_hashes=_release_artifacts(),
        created_at=_now(),
    )
    with pytest.raises(ValidationError, match="hash does not match"):
        EnkiReleaseCandidate(
            manifest=candidate.manifest,
            candidate_sha256=_hash("tampered"),
        )

    with pytest.raises(ValidationError, match="cannot self-issue"):
        HumanReleaseDecisionRequest(
            candidate_id=request.candidate_id,
            candidate_sha256=request.candidate_sha256,
            options=request.options,
            requested_at=request.requested_at,
            decision=HumanReleaseDecisionOption.APPROVE,
            decided_by="system",
        )


def test_loop_receipt_rejects_hash_tampering() -> None:
    publication = _publication_lane()
    runner, _, _, _ = _runner([_grant(publication, "TX-HASH", "APR-HASH")])
    receipt = runner.run(
        publication,
        transaction_id="TX-HASH",
        approval_id="APR-HASH",
        acceptable_authority_classes={"TEST-HARNESS"},
        zero_response=True,
    )

    payload = receipt.model_dump(mode="python")
    payload["loop_sha256"] = _hash("tampered")
    with pytest.raises(ValidationError, match="loop receipt hash"):
        AdaptiveLoopReceipt.model_validate(payload)
