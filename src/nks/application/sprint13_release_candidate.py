"""Sprint 13 integrated TEST hardening and release-candidate contracts.

This module is intentionally self-contained on top of the Sprint 12 reconstruction and
recovery boundary. It proves release-candidate behavior without creating any production
transport or effect capability.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.sprint12_recovery import validate_portable_package


ExecutionContext = Literal["TEST", "PRODUCTION"]


class ProofLaneKind(StrEnum):
    PUBLICATION = "PUBLICATION"
    NONPUBLICATION = "NONPUBLICATION"


class SubjectClass(StrEnum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    PROJECT = "PROJECT"
    GENERIC = "GENERIC"


class FeedbackProvenance(StrEnum):
    SYNTHETIC_TEST = "SYNTHETIC/TEST"
    REPLAY_TEST = "REPLAY/TEST"
    REAL_TEST = "REAL/TEST"


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


def canonical_sha256(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    elif isinstance(value, list):
        value = [
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in value
        ]
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def file_sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


class ProofLanePlan(BaseModel):
    """Exact TEST-only input to one integrated hardening lane."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    lane_id: str = Field(min_length=1)
    lane_kind: ProofLaneKind
    subject_class: SubjectClass
    subject_id: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    artifact_hashes: dict[str, str] = Field(min_length=1)
    requested_at: datetime
    execution_context: ExecutionContext = "TEST"

    @model_validator(mode="after")
    def validate_lane(self) -> "ProofLanePlan":
        if self.execution_context != "TEST":
            raise ValueError("Sprint 13 proof lanes are TEST-only")
        invalid = [
            key
            for key, value in self.artifact_hashes.items()
            if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71
        ]
        if invalid:
            raise ValueError(f"invalid artifact hash declarations: {sorted(invalid)}")
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


class NoEffectReceipt(BaseModel):
    """Immutable proof that a production-shaped TEST lane caused no external effect."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: str = Field(min_length=1)
    lane_id: str = Field(min_length=1)
    plan_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    execution_context: ExecutionContext
    external_effect: bool
    recorded_at: datetime

    @model_validator(mode="after")
    def validate_no_effect(self) -> "NoEffectReceipt":
        if self.execution_context != "TEST":
            raise ValueError("no-effect receipts must be TEST-scoped")
        if self.external_effect:
            raise ValueError("TEST receipts cannot claim an external effect")
        return self


class FeedbackEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    feedback_id: str = Field(min_length=1)
    provenance: FeedbackProvenance
    execution_context: ExecutionContext = "TEST"
    source_id: str = Field(min_length=1)
    target_subject_id: str = Field(min_length=1)
    content: str
    content_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    received_at: datetime
    replay_of: str | None = None
    relevant: bool = True
    contradictory: bool = False
    adversarial: bool = False

    @model_validator(mode="after")
    def validate_envelope(self) -> "FeedbackEnvelope":
        if self.content_sha256 != canonical_sha256(self.content):
            raise ValueError("feedback content hash does not match content")
        if self.provenance == FeedbackProvenance.REPLAY_TEST and not self.replay_of:
            raise ValueError("REPLAY/TEST feedback must identify replay_of")
        return self


class FeedbackEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    feedback_id: str | None = None
    provenance: FeedbackProvenance | None = None
    disposition: FeedbackDisposition
    reasons: list[str] = Field(default_factory=list)
    content_sha256: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")


class FeedbackProcessor:
    """Deterministically classify, attribute, and de-duplicate TEST feedback."""

    def __init__(self) -> None:
        self._ids: dict[str, str] = {}
        self._accepted_hashes: set[str] = set()

    def process(self, target_subject_id: str, envelope: FeedbackEnvelope) -> FeedbackEvaluation:
        existing = self._ids.get(envelope.feedback_id)
        if existing is not None:
            if existing == envelope.content_sha256:
                return FeedbackEvaluation(
                    feedback_id=envelope.feedback_id,
                    provenance=envelope.provenance,
                    disposition=FeedbackDisposition.DUPLICATE,
                    reasons=["feedback id already observed with identical immutable content"],
                    content_sha256=envelope.content_sha256,
                )
            return FeedbackEvaluation(
                feedback_id=envelope.feedback_id,
                provenance=envelope.provenance,
                disposition=FeedbackDisposition.CONFLICT,
                reasons=["feedback id reused with different immutable content"],
                content_sha256=envelope.content_sha256,
            )

        self._ids[envelope.feedback_id] = envelope.content_sha256
        checks = [
            (
                envelope.execution_context != "TEST",
                FeedbackDisposition.UNAUTHORIZED,
                "feedback execution context is not TEST",
            ),
            (
                envelope.target_subject_id != target_subject_id,
                FeedbackDisposition.MISMATCHED,
                "feedback target does not match proof subject",
            ),
            (
                not envelope.content.strip(),
                FeedbackDisposition.MALFORMED,
                "feedback content is empty",
            ),
            (
                envelope.adversarial,
                FeedbackDisposition.ADVERSARIAL,
                "feedback is marked as adversarial",
            ),
            (
                not envelope.relevant,
                FeedbackDisposition.IRRELEVANT,
                "feedback is outside the declared purpose or subject",
            ),
            (
                envelope.contradictory,
                FeedbackDisposition.CONTRADICTORY,
                "feedback contradicts a governed interpretation",
            ),
            (
                envelope.content_sha256 in self._accepted_hashes,
                FeedbackDisposition.DUPLICATE,
                "identical feedback content already accepted",
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
            reasons=["feedback is attributable, unique, relevant, and TEST-scoped"],
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
                    reasons=["the TEST observation window produced no feedback"],
                )
            ]
        return [self.process(target_subject_id, item) for item in feedback]


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
        zero_response = any(
            item.disposition == FeedbackDisposition.ZERO_RESPONSE for item in evaluations
        )
        counts: dict[str, int] = {}
        for item in evaluations:
            if item.provenance is not None:
                counts[item.provenance.value] = counts.get(item.provenance.value, 0) + 1
        evidence_hash = canonical_sha256(evaluations)
        body = {
            "lane_id": lane_id,
            "accepted": accepted,
            "deferred_or_withheld": len(evaluations) - accepted,
            "zero_response": zero_response,
            "provenance_counts": counts,
            "feedback_evidence_sha256": evidence_hash,
        }
        return cls(
            **body,
            calibration_sha256=canonical_sha256(body),
        )


class TestLoopResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    lane: ProofLanePlan
    receipt: NoEffectReceipt
    evaluations: list[FeedbackEvaluation]
    calibration: CalibrationReport

    @property
    def result_sha256(self) -> str:
        return canonical_sha256(self)


def execute_test_loop(
    lane: ProofLanePlan,
    feedback: list[FeedbackEnvelope],
    *,
    zero_response: bool = False,
) -> TestLoopResult:
    processor = FeedbackProcessor()
    evaluations = processor.process_batch(
        lane.subject_id,
        feedback,
        zero_response=zero_response,
    )
    receipt = NoEffectReceipt(
        receipt_id=f"TEST-RCPT-{lane.lane_id}",
        lane_id=lane.lane_id,
        plan_sha256=lane.plan_sha256,
        execution_context="TEST",
        external_effect=False,
        recorded_at=lane.requested_at,
    )
    return TestLoopResult(
        lane=lane,
        receipt=receipt,
        evaluations=evaluations,
        calibration=CalibrationReport.create(lane.lane_id, evaluations),
    )


class ReleaseEvidenceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    files: dict[str, str]
    manifest_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @classmethod
    def from_paths(cls, paths: list[Path], *, root: Path | None = None) -> "ReleaseEvidenceManifest":
        root = root.resolve() if root is not None else None
        files: dict[str, str] = {}
        for path in sorted(path.resolve() for path in paths):
            key = path.relative_to(root).as_posix() if root is not None else path.name
            files[key] = file_sha256(path)
        return cls(files=files, manifest_sha256=canonical_sha256(files))


class ReleaseCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = Field(min_length=1)
    implementation_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    portable_package_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    evidence_manifest_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    lane_result_sha256s: list[str] = Field(min_length=2)
    subject_classes: list[SubjectClass] = Field(min_length=2)
    feedback_provenance: list[FeedbackProvenance]
    status: ReleaseCandidateStatus = ReleaseCandidateStatus.READY_FOR_HUMAN_DECISION
    production_authorized: bool = False

    @model_validator(mode="after")
    def validate_release_candidate(self) -> "ReleaseCandidate":
        if self.production_authorized:
            raise ValueError("Sprint 13 cannot authorize production")
        if len(set(self.subject_classes)) < 2:
            raise ValueError("release candidate requires at least two distinct subject classes")
        required = {
            FeedbackProvenance.SYNTHETIC_TEST,
            FeedbackProvenance.REPLAY_TEST,
            FeedbackProvenance.REAL_TEST,
        }
        if not required.issubset(set(self.feedback_provenance)):
            raise ValueError("release candidate requires SYNTHETIC/TEST, REPLAY/TEST, and REAL/TEST evidence")
        return self


class ReleaseDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    requested_at: datetime
    requested_from: str = Field(min_length=1)
    options: list[str] = Field(
        default_factory=lambda: ["APPROVE", "APPROVE_WITH_CONDITIONS", "DEFER", "REJECT"]
    )
    decision: None = None


def build_release_candidate(
    *,
    version: str,
    implementation_commit: str,
    portable_archive: Path,
    evidence_manifest: ReleaseEvidenceManifest,
    loop_results: list[TestLoopResult],
) -> ReleaseCandidate:
    validate_portable_package(portable_archive)
    if len(loop_results) < 2:
        raise ValueError("release candidate requires at least two complete TEST loops")
    if not any(item.lane.lane_kind == ProofLaneKind.PUBLICATION for item in loop_results):
        raise ValueError("release candidate requires a publication-shaped TEST loop")
    if not any(item.lane.lane_kind == ProofLaneKind.NONPUBLICATION for item in loop_results):
        raise ValueError("release candidate requires a nonpublication TEST loop")
    if any(item.receipt.external_effect for item in loop_results):
        raise ValueError("release candidate contains an external effect")

    provenance = sorted(
        {
            evaluation.provenance
            for item in loop_results
            for evaluation in item.evaluations
            if evaluation.provenance is not None
        },
        key=lambda value: value.value,
    )
    return ReleaseCandidate(
        version=version,
        implementation_commit=implementation_commit,
        portable_package_sha256=file_sha256(portable_archive),
        evidence_manifest_sha256=evidence_manifest.manifest_sha256,
        lane_result_sha256s=[item.result_sha256 for item in loop_results],
        subject_classes=[item.lane.subject_class for item in loop_results],
        feedback_provenance=provenance,
    )
