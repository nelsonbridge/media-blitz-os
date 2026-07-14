"""Integrated internal TEST proof and release-candidate construction.

Sprint 13 composes the existing approval, transaction, reconstruction, and
no-effect boundaries into repeatable downstream-consumer proofs.  The module
never creates a production capability: every executable path is TEST-only and
all external-effect claims fail closed.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from typing import Callable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.forensic_contracts import (
    ForensicRecord,
    ReconstructionRequest,
    ReconstructionResult,
    ReconstructionStatus,
)
from nks.application.forensic_reconstruct import reconstruct_operation
from nks.application.governed_transactions import (
    FailureHook,
    GovernedOperationAdapter,
    GovernedOperationPlan,
    GovernedOperationResult,
    GovernedTransactionExecutor,
    GovernedTransactionReceipt,
    TransactionTerminalState,
    canonical_sha256,
)
from nks.enki.contracts import SubjectRef
from nks.governance.approvals import ExecutionContext


_HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class ProofLaneKind(StrEnum):
    PUBLICATION = "PUBLICATION"
    NONPUBLICATION = "NONPUBLICATION"


class FeedbackProvenance(StrEnum):
    SYNTHETIC_TEST = "SYNTHETIC/TEST"
    REPLAY_TEST = "REPLAY/TEST"
    CONTROLLED_REAL_TEST = "CONTROLLED_REAL/TEST"


class FeedbackDisposition(StrEnum):
    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"
    IRRELEVANT = "IRRELEVANT"
    MALFORMED = "MALFORMED"
    CONTRADICTORY = "CONTRADICTORY"
    ADVERSARIAL = "ADVERSARIAL"
    UNAUTHORIZED = "UNAUTHORIZED"
    MISMATCHED = "MISMATCHED"
    CONFLICT = "CONFLICT"
    ZERO_RESPONSE = "ZERO_RESPONSE"


class ReleaseCandidateStatus(StrEnum):
    READY_FOR_HUMAN_DECISION = "READY_FOR_HUMAN_DECISION"


class HumanReleaseDecisionOption(StrEnum):
    APPROVE = "APPROVE"
    APPROVE_WITH_CONDITIONS = "APPROVE_WITH_CONDITIONS"
    DEFER = "DEFER"
    REJECT = "REJECT"


class ProofLanePlan(BaseModel):
    """Exact, hash-bound input for one integrated TEST loop."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    lane_id: str = Field(min_length=1)
    lane_kind: ProofLaneKind
    subject: SubjectRef
    domain: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    artifact_hashes: dict[str, str] = Field(min_length=1)
    requested_at: datetime
    execution_context: ExecutionContext = ExecutionContext.TEST
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_test_lane(self) -> "ProofLanePlan":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("integrated proof lanes are TEST-only")
        invalid = sorted(
            key for key, value in self.artifact_hashes.items() if not _HASH_PATTERN.fullmatch(value)
        )
        if invalid:
            raise ValueError(f"artifact hashes are invalid: {invalid}")
        if self.lane_kind == ProofLaneKind.PUBLICATION:
            required = {
                "content",
                "configuration",
                "identity",
                "byline",
                "brand",
                "channel",
                "review",
            }
            missing = sorted(required - set(self.artifact_hashes))
            if missing:
                raise ValueError(f"publication proof is missing artifacts: {missing}")
            if not any(key.startswith("visual:") for key in self.artifact_hashes):
                raise ValueError("publication proof requires at least one visual hash")
        elif "payload" not in self.artifact_hashes:
            raise ValueError("nonpublication proof requires a payload hash")
        return self

    @property
    def plan_sha256(self) -> str:
        return canonical_sha256(self)


class FeedbackEnvelope(BaseModel):
    """One attributable feedback input presented to a TEST loop."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    feedback_id: str = Field(min_length=1)
    provenance: FeedbackProvenance
    execution_context: ExecutionContext
    source_id: str = Field(min_length=1)
    target_subject_id: str = Field(min_length=1)
    content: str
    content_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    received_at: datetime
    authority_class: str = Field(min_length=1)
    replay_of: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_content_hash(self) -> "FeedbackEnvelope":
        if self.content_sha256 != canonical_sha256(self.content):
            raise ValueError("feedback content hash does not match content")
        return self


class FeedbackEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    feedback_id: str | None = None
    provenance: FeedbackProvenance | None = None
    disposition: FeedbackDisposition
    reasons: list[str] = Field(default_factory=list)
    content_sha256: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")


class FeedbackProcessor:
    """Deterministically classify, attribute, and deduplicate TEST feedback."""

    def __init__(self) -> None:
        self._by_id: dict[str, str] = {}
        self._accepted_hashes: set[str] = set()

    def process(
        self,
        target_subject_id: str,
        envelope: FeedbackEnvelope,
    ) -> FeedbackEvaluation:
        existing = self._by_id.get(envelope.feedback_id)
        if existing is not None:
            if existing == envelope.content_sha256:
                return FeedbackEvaluation(
                    feedback_id=envelope.feedback_id,
                    provenance=envelope.provenance,
                    disposition=FeedbackDisposition.DUPLICATE,
                    reasons=["feedback id was already observed with identical content"],
                    content_sha256=envelope.content_sha256,
                )
            return FeedbackEvaluation(
                feedback_id=envelope.feedback_id,
                provenance=envelope.provenance,
                disposition=FeedbackDisposition.CONFLICT,
                reasons=["feedback id was reused with different immutable content"],
                content_sha256=envelope.content_sha256,
            )

        self._by_id[envelope.feedback_id] = envelope.content_sha256
        checks: list[tuple[bool, FeedbackDisposition, str]] = [
            (
                envelope.execution_context != ExecutionContext.TEST,
                FeedbackDisposition.UNAUTHORIZED,
                "feedback execution context is not TEST",
            ),
            (
                envelope.target_subject_id != target_subject_id,
                FeedbackDisposition.MISMATCHED,
                "feedback target does not match the proof subject",
            ),
            (
                not envelope.content.strip(),
                FeedbackDisposition.MALFORMED,
                "feedback content is empty",
            ),
            (
                envelope.provenance == FeedbackProvenance.REPLAY_TEST
                and not envelope.replay_of,
                FeedbackDisposition.MALFORMED,
                "replay feedback does not identify its original record",
            ),
            (
                bool(envelope.metadata.get("adversarial")),
                FeedbackDisposition.ADVERSARIAL,
                "feedback is marked as an adversarial test case",
            ),
            (
                envelope.metadata.get("relevant") is False,
                FeedbackDisposition.IRRELEVANT,
                "feedback is outside the declared purpose or subject",
            ),
            (
                bool(envelope.metadata.get("contradictory")),
                FeedbackDisposition.CONTRADICTORY,
                "feedback contradicts an existing governed interpretation",
            ),
            (
                envelope.content_sha256 in self._accepted_hashes,
                FeedbackDisposition.DUPLICATE,
                "identical feedback content was already accepted",
            ),
        ]
        for condition, disposition, reason in checks:
            if condition:
                return FeedbackEvaluation(
                    feedback_id=envelope.feedback_id,
                    provenance=envelope.provenance,
                    disposition=disposition,
                    reasons=[reason],
                    content_sha256=envelope.content_sha256,
                )

        self._accepted_hashes.add(envelope.content_sha256)
        return FeedbackEvaluation(
            feedback_id=envelope.feedback_id,
            provenance=envelope.provenance,
            disposition=FeedbackDisposition.ACCEPTED,
            reasons=["feedback is attributable, relevant, unique, and TEST-scoped"],
            content_sha256=envelope.content_sha256,
        )

    def process_batch(
        self,
        target_subject_id: str,
        feedback: list[FeedbackEnvelope],
        *,
        zero_response: bool = False,
    ) -> list[FeedbackEvaluation]:
        if zero_response and feedback:
            raise ValueError("zero_response cannot be combined with feedback records")
        if zero_response:
            return [
                FeedbackEvaluation(
                    disposition=FeedbackDisposition.ZERO_RESPONSE,
                    reasons=["the observation window produced no feedback"],
                )
            ]
        return [self.process(target_subject_id, item) for item in feedback]


class NoEffectDistributionReceipt(BaseModel):
    """Immutable proof that a production-shaped dispatch caused no external effect."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    distribution_id: str = Field(min_length=1)
    lane_id: str = Field(min_length=1)
    plan_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    execution_context: ExecutionContext
    adapter_id: str = Field(min_length=1)
    external_effect: bool
    recorded_at: datetime
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_no_effect(self) -> "NoEffectDistributionReceipt":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("no-effect proof receipts must be TEST-scoped")
        if self.external_effect:
            raise ValueError("TEST distribution receipts cannot claim an external effect")
        return self


class NoEffectProofAdapter(GovernedOperationAdapter):
    """Idempotent adapter with no transport, credential, endpoint, or callback surface."""

    adapter_id = "enki-integrated-no-effect/v1"
    capabilities = frozenset({"build-package", "record-no-effect-receipt"})

    def __init__(self, lane: ProofLanePlan) -> None:
        self._lane = lane
        self._receipts: dict[str, NoEffectDistributionReceipt] = {}
        self._plan_hashes: dict[str, str] = {}

    def apply(self, plan: GovernedOperationPlan) -> GovernedOperationResult:
        expected_action = f"enki:test-proof:{self._lane.lane_kind.value.lower()}"
        checks = {
            "action": plan.action == expected_action,
            "subject": plan.subject_id == self._lane.subject.subject_id,
            "content": plan.content_sha256 == self._lane.plan_sha256,
            "context": plan.execution_context == ExecutionContext.TEST,
            "lane context": self._lane.execution_context == ExecutionContext.TEST,
        }
        for name, valid in checks.items():
            if not valid:
                raise PermissionError(f"proof operation {name} does not match TEST lane")

        existing_hash = self._plan_hashes.get(plan.transaction_id)
        if existing_hash is not None and existing_hash != plan.plan_sha256:
            raise RuntimeError("proof transaction was replayed with a different plan")
        self._plan_hashes[plan.transaction_id] = plan.plan_sha256

        receipt = self._receipts.get(plan.transaction_id)
        if receipt is None:
            receipt = NoEffectDistributionReceipt(
                distribution_id=f"DIST-{plan.transaction_id}",
                lane_id=self._lane.lane_id,
                plan_sha256=self._lane.plan_sha256,
                execution_context=ExecutionContext.TEST,
                adapter_id=self.adapter_id,
                external_effect=False,
                recorded_at=self._lane.requested_at,
                metadata={
                    "lane_kind": self._lane.lane_kind.value,
                    "artifact_count": len(self._lane.artifact_hashes),
                },
            )
            self._receipts[plan.transaction_id] = receipt

        return GovernedOperationResult(
            output_sha256=canonical_sha256(receipt),
            metadata={
                "distribution_id": receipt.distribution_id,
                "external_effect": False,
                "adapter_id": self.adapter_id,
            },
        )

    def get_receipt(self, transaction_id: str) -> NoEffectDistributionReceipt | None:
        return self._receipts.get(transaction_id)

    @property
    def effect_count(self) -> int:
        return len(self._receipts)


class CalibrationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    lane_id: str
    accepted: int
    deferred_or_withheld: int
    zero_response: bool
    provenance_counts: dict[str, int]
    feedback_evidence_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    calibration_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @classmethod
    def create(
        cls,
        lane_id: str,
        evaluations: list[FeedbackEvaluation],
    ) -> "CalibrationReport":
        accepted = sum(item.disposition == FeedbackDisposition.ACCEPTED for item in evaluations)
        provenance_counts: dict[str, int] = {}
        for item in evaluations:
            if item.provenance is not None:
                provenance_counts[item.provenance.value] = (
                    provenance_counts.get(item.provenance.value, 0) + 1
                )
        payload = {
            "lane_id": lane_id,
            "evaluations": evaluations,
            "accepted": accepted,
            "provenance_counts": provenance_counts,
        }
        feedback_hash = canonical_sha256(evaluations)
        return cls(
            lane_id=lane_id,
            accepted=accepted,
            deferred_or_withheld=len(evaluations) - accepted,
            zero_response=any(
                item.disposition == FeedbackDisposition.ZERO_RESPONSE for item in evaluations
            ),
            provenance_counts=provenance_counts,
            feedback_evidence_sha256=feedback_hash,
            calibration_sha256=canonical_sha256(payload),
        )


class AdaptiveLoopReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    loop_id: str
    lane_kind: ProofLaneKind
    subject: SubjectRef
    execution_context: ExecutionContext
    lane_plan_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    distribution: NoEffectDistributionReceipt | None
    transaction_receipt: GovernedTransactionReceipt
    feedback: list[FeedbackEvaluation]
    calibration: CalibrationReport | None
    reconstruction: ReconstructionResult
    external_effect: bool
    loop_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_loop_boundary(self) -> "AdaptiveLoopReceipt":
        if self.execution_context != ExecutionContext.TEST or self.external_effect:
            raise ValueError("integrated loop receipts must remain no-effect TEST records")
        payload = self.model_dump(mode="python", exclude={"loop_sha256"})
        if self.loop_sha256 != canonical_sha256(payload):
            raise ValueError("integrated loop receipt hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "AdaptiveLoopReceipt":
        payload = dict(values)
        payload["loop_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class IntegratedTestProofRunner:
    """Execute and reconstruct exact TEST lanes through no-effect adapters."""

    def __init__(
        self,
        transaction_executor: GovernedTransactionExecutor,
        *,
        feedback_processor: FeedbackProcessor | None = None,
    ) -> None:
        self._transactions = transaction_executor
        self._feedback = feedback_processor or FeedbackProcessor()
        self._adapters: dict[str, NoEffectProofAdapter] = {}
        self._lane_hashes: dict[str, str] = {}

    @staticmethod
    def operation_plan(
        lane: ProofLanePlan,
        *,
        transaction_id: str,
        acceptable_authority_classes: set[str],
    ) -> GovernedOperationPlan:
        return GovernedOperationPlan(
            operation_id=f"integrated-test-proof:{lane.lane_id}",
            transaction_id=transaction_id,
            action=f"enki:test-proof:{lane.lane_kind.value.lower()}",
            subject_id=lane.subject.subject_id,
            content_sha256=lane.plan_sha256,
            execution_context=ExecutionContext.TEST,
            acceptable_authority_classes=acceptable_authority_classes,
            requested_at=lane.requested_at,
            metadata={
                "lane_id": lane.lane_id,
                "lane_kind": lane.lane_kind.value,
                "domain": lane.domain,
                "purpose": lane.purpose,
            },
        )

    def _adapter(self, lane: ProofLanePlan, transaction_id: str) -> NoEffectProofAdapter:
        existing_hash = self._lane_hashes.get(transaction_id)
        if existing_hash is not None and existing_hash != lane.plan_sha256:
            raise RuntimeError("proof transaction is already bound to another lane plan")
        self._lane_hashes[transaction_id] = lane.plan_sha256
        return self._adapters.setdefault(transaction_id, NoEffectProofAdapter(lane))

    @staticmethod
    def _records(
        lane: ProofLanePlan,
        operation_plan: GovernedOperationPlan,
        transaction_receipt: GovernedTransactionReceipt,
        distribution: NoEffectDistributionReceipt | None,
        feedback: list[FeedbackEvaluation],
        calibration: CalibrationReport | None,
    ) -> list[ForensicRecord]:
        common = {
            "operation_family": "integrated-test-proof",
            "operation_id": operation_plan.operation_id,
            "transaction_id": operation_plan.transaction_id,
            "execution_context": ExecutionContext.TEST,
            "authority_class": "TEST-HARNESS",
            "recorded_at": lane.requested_at,
        }
        records = [
            ForensicRecord.create(
                record_id=f"{operation_plan.transaction_id}:plan",
                record_type="operation-plan",
                payload={"plan_sha256": operation_plan.plan_sha256},
                **common,
            ),
            ForensicRecord.create(
                record_id=f"{operation_plan.transaction_id}:transaction-receipt",
                record_type="transaction-receipt",
                payload={
                    "plan_sha256": operation_plan.plan_sha256,
                    "terminal_state": transaction_receipt.terminal_state.value,
                    "output_sha256": transaction_receipt.output_sha256,
                    "approval_id": transaction_receipt.approval_id,
                },
                **common,
            ),
        ]
        if distribution is not None:
            records.extend(
                [
                    ForensicRecord.create(
                        record_id=f"{operation_plan.transaction_id}:approval",
                        record_type="approval-consumed",
                        payload={
                            "plan_sha256": operation_plan.plan_sha256,
                            "approval_id": transaction_receipt.approval_id,
                        },
                        **common,
                    ),
                    ForensicRecord.create(
                        record_id=f"{operation_plan.transaction_id}:effect",
                        record_type="effect",
                        payload={
                            "plan_sha256": operation_plan.plan_sha256,
                            "distribution": distribution,
                        },
                        **common,
                    ),
                    ForensicRecord.create(
                        record_id=f"{operation_plan.transaction_id}:feedback",
                        record_type="feedback-batch",
                        payload={
                            "plan_sha256": operation_plan.plan_sha256,
                            "evaluations": feedback,
                        },
                        **common,
                    ),
                    ForensicRecord.create(
                        record_id=f"{operation_plan.transaction_id}:output",
                        record_type="operation-output",
                        payload={
                            "plan_sha256": operation_plan.plan_sha256,
                            "calibration": calibration,
                        },
                        **common,
                    ),
                ]
            )
        return records

    def run(
        self,
        lane: ProofLanePlan,
        *,
        transaction_id: str,
        approval_id: str,
        acceptable_authority_classes: set[str],
        feedback: list[FeedbackEnvelope] | None = None,
        zero_response: bool = False,
        now: datetime | None = None,
        failure_hook: FailureHook | None = None,
    ) -> AdaptiveLoopReceipt:
        operation_plan = self.operation_plan(
            lane,
            transaction_id=transaction_id,
            acceptable_authority_classes=acceptable_authority_classes,
        )
        adapter = self._adapter(lane, transaction_id)
        transaction_receipt = self._transactions.execute(
            operation_plan,
            approval_id=approval_id,
            adapter=adapter,
            now=now or lane.requested_at,
            failure_hook=failure_hook,
        )
        distribution = adapter.get_receipt(transaction_id)

        evaluations: list[FeedbackEvaluation] = []
        calibration: CalibrationReport | None = None
        if transaction_receipt.terminal_state in {
            TransactionTerminalState.COMMITTED,
            TransactionTerminalState.RECOVERED,
        }:
            if distribution is None:
                raise RuntimeError("completed proof transaction has no no-effect receipt")
            evaluations = self._feedback.process_batch(
                lane.subject.subject_id,
                feedback or [],
                zero_response=zero_response,
            )
            calibration = CalibrationReport.create(lane.lane_id, evaluations)

        records = self._records(
            lane,
            operation_plan,
            transaction_receipt,
            distribution,
            evaluations,
            calibration,
        )
        required = {"operation-plan", "transaction-receipt"}
        if distribution is not None:
            required |= {
                "approval-consumed",
                "effect",
                "feedback-batch",
                "operation-output",
            }
        reconstruction = reconstruct_operation(
            ReconstructionRequest(
                operation_family="integrated-test-proof",
                operation_id=operation_plan.operation_id,
                transaction_id=transaction_id,
                execution_context=ExecutionContext.TEST,
                required_record_types=required,
                acceptable_authority_classes={"TEST-HARNESS"},
                expected_plan_sha256=operation_plan.plan_sha256,
                expected_output_sha256=transaction_receipt.output_sha256,
            ),
            records,
        )
        expected_status = (
            ReconstructionStatus.ROLLED_BACK
            if transaction_receipt.terminal_state == TransactionTerminalState.ROLLED_BACK
            else ReconstructionStatus.COMPLETE
        )
        if reconstruction.status != expected_status:
            raise RuntimeError(
                f"integrated proof reconstruction is {reconstruction.status}, expected {expected_status}"
            )

        return AdaptiveLoopReceipt.create(
            loop_id=lane.lane_id,
            lane_kind=lane.lane_kind,
            subject=lane.subject,
            execution_context=ExecutionContext.TEST,
            lane_plan_sha256=lane.plan_sha256,
            distribution=distribution,
            transaction_receipt=transaction_receipt,
            feedback=evaluations,
            calibration=calibration,
            reconstruction=reconstruction,
            external_effect=False,
        )

    def effect_count(self, transaction_id: str) -> int:
        adapter = self._adapters.get(transaction_id)
        return adapter.effect_count if adapter is not None else 0


class ReleaseEvidenceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    source_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    loop_receipt_hashes: list[str] = Field(min_length=2)
    artifact_hashes: dict[str, str]
    created_at: datetime
    execution_context: ExecutionContext = ExecutionContext.TEST

    @model_validator(mode="after")
    def validate_manifest(self) -> "ReleaseEvidenceManifest":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("the internal release candidate is TEST-only")
        if not _COMMIT_PATTERN.fullmatch(self.source_commit_sha):
            raise ValueError("source commit sha must be an exact 40-character hash")
        if len(self.loop_receipt_hashes) != len(set(self.loop_receipt_hashes)):
            raise ValueError("release evidence loops must be distinct")
        if any(not _HASH_PATTERN.fullmatch(value) for value in self.loop_receipt_hashes):
            raise ValueError("loop receipt hashes must be sha256 values")
        required = {
            "calibration-report",
            "threat-model",
            "runbook",
            "known-limitations",
            "rollback-package",
            "release-notes",
            "evidence-manifest",
        }
        missing = sorted(required - set(self.artifact_hashes))
        if missing:
            raise ValueError(f"release evidence is missing artifacts: {missing}")
        invalid = sorted(
            key for key, value in self.artifact_hashes.items() if not _HASH_PATTERN.fullmatch(value)
        )
        if invalid:
            raise ValueError(f"release artifact hashes are invalid: {invalid}")
        return self


class EnkiReleaseCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    manifest: ReleaseEvidenceManifest
    candidate_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    status: ReleaseCandidateStatus = ReleaseCandidateStatus.READY_FOR_HUMAN_DECISION
    external_effect: bool = False

    @model_validator(mode="after")
    def validate_candidate(self) -> "EnkiReleaseCandidate":
        if self.external_effect:
            raise ValueError("an internal TEST release candidate cannot claim an external effect")
        if self.candidate_sha256 != canonical_sha256(self.manifest):
            raise ValueError("release candidate hash does not match its evidence manifest")
        return self


class HumanReleaseDecisionRequest(BaseModel):
    """Decision package prepared for, but never issued by, the system."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str
    candidate_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    options: list[HumanReleaseDecisionOption]
    requested_at: datetime
    decision: HumanReleaseDecisionOption | None = None
    decided_by: str | None = None

    @model_validator(mode="after")
    def prohibit_self_decision(self) -> "HumanReleaseDecisionRequest":
        if self.decision is not None or self.decided_by is not None:
            raise ValueError("release decision requests cannot self-issue a decision")
        if set(self.options) != set(HumanReleaseDecisionOption):
            raise ValueError("release decision request must present every governed option")
        return self


def build_release_candidate(
    loops: list[AdaptiveLoopReceipt],
    *,
    candidate_id: str,
    version: str,
    source_commit_sha: str,
    artifact_hashes: dict[str, str],
    created_at: datetime,
) -> tuple[EnkiReleaseCandidate, HumanReleaseDecisionRequest]:
    """Bind complete no-effect TEST proof to one exact release candidate."""

    if len(loops) < 2:
        raise ValueError("release candidate requires at least two adaptive TEST loops")
    kinds = {loop.lane_kind for loop in loops}
    if not {ProofLaneKind.PUBLICATION, ProofLaneKind.NONPUBLICATION} <= kinds:
        raise ValueError("release candidate requires publication and nonpublication lanes")
    for loop in loops:
        if loop.execution_context != ExecutionContext.TEST or loop.external_effect:
            raise ValueError("release loops must be no-effect TEST records")
        if loop.reconstruction.status != ReconstructionStatus.COMPLETE:
            raise ValueError("release loops must reconstruct as COMPLETE")
        if loop.transaction_receipt.terminal_state not in {
            TransactionTerminalState.COMMITTED,
            TransactionTerminalState.RECOVERED,
        }:
            raise ValueError("release loops must be committed or exactly recovered")

    manifest = ReleaseEvidenceManifest(
        candidate_id=candidate_id,
        version=version,
        source_commit_sha=source_commit_sha,
        loop_receipt_hashes=sorted(loop.loop_sha256 for loop in loops),
        artifact_hashes=dict(sorted(artifact_hashes.items())),
        created_at=created_at,
    )
    candidate = EnkiReleaseCandidate(
        manifest=manifest,
        candidate_sha256=canonical_sha256(manifest),
    )
    decision_request = HumanReleaseDecisionRequest(
        candidate_id=candidate_id,
        candidate_sha256=candidate.candidate_sha256,
        options=list(HumanReleaseDecisionOption),
        requested_at=created_at,
    )
    return candidate, decision_request
