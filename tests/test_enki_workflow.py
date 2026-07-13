from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone

from nks.application.enki_workflow import DiscloseAndRecord, ReconcileAndRecord
from nks.enki.contracts import (
    ConfidenceAssertion,
    ConfidenceLevel,
    EvidenceRef,
    ExpressionOrigin,
    Observation,
    ReconciliationRequest,
    ReferenceKind,
    RelationshipAssertion,
    SubjectRef,
    TemporalApplicability,
    TemporalStatus,
)
from nks.enki.disclosure import DisclosureAudience, DisclosureContext
from nks.enki.reconciliation import ReconciliationEngine, RelationshipFindingStrategy


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _request() -> ReconciliationRequest:
    now = datetime(2026, 7, 13, 23, 0, tzinfo=timezone.utc)
    subject = SubjectRef(subject_id="SUBJECT-1", subject_type="PERSON")
    evidence = EvidenceRef(
        evidence_id="E-1",
        source_id="SOURCE-1",
        content_hash=_hash("evidence"),
        observed_at=now,
        provenance_classification="REAL",
    )
    confidence = ConfidenceAssertion(
        level=ConfidenceLevel.HIGH,
        rationale="Supported by attributable evidence.",
        evidence_ids=["E-1"],
    )
    observation = Observation(
        observation_id="OBS-1",
        subject=subject,
        domain="career",
        statement="A decision diverges from the stated objective.",
        content_hash=_hash("A decision diverges from the stated objective."),
        evidence=[evidence],
        observed_at=now,
        applicability=TemporalApplicability(effective_from=date(2026, 1, 1)),
        expression_origin=ExpressionOrigin.OBSERVED,
        confidence=confidence,
        temporal_status=TemporalStatus.CURRENT,
    )
    relationship = RelationshipAssertion(
        relationship_id="REL-1",
        subject=subject,
        domain="career",
        source_kind=ReferenceKind.OBSERVATION,
        source_id="OBS-1",
        target_kind=ReferenceKind.OBJECTIVE,
        target_id="OBJ-1",
        relationship_type="DIVERGES_FROM",
        evidence=[evidence],
        confidence=confidence,
        observed_at=now,
        applicability=TemporalApplicability(effective_from=date(2026, 1, 1)),
    )
    return ReconciliationRequest(
        subject=subject,
        domain="career",
        observations=[observation],
        relationships=[relationship],
        objective_refs=["OBJ-1"],
        priority_refs=[],
        as_of=now,
    )


class FindingMemory:
    def __init__(self) -> None:
        self.findings = []

    def append_findings(self, findings) -> None:
        self.findings.extend(findings)


class ReceiptMemory:
    def __init__(self) -> None:
        self.receipts = []

    def append_disclosure_receipt(self, receipt) -> None:
        self.receipts.append(receipt)


def test_recording_reconciliation_does_not_imply_disclosure() -> None:
    finding_memory = FindingMemory()
    workflow = ReconcileAndRecord(
        ReconciliationEngine(
            RelationshipFindingStrategy(),
            interpretation_version="enki-test/v1",
        ),
        finding_writer=finding_memory,
    )

    result = workflow.execute(_request())

    assert len(result.findings) == 1
    assert finding_memory.findings == result.findings
    assert not hasattr(result, "disclosure")


def test_disclosure_receipt_is_recorded_only_after_separate_evaluation() -> None:
    result = ReconcileAndRecord(
        ReconciliationEngine(
            RelationshipFindingStrategy(),
            interpretation_version="enki-test/v1",
        )
    ).execute(_request())
    receipt_memory = ReceiptMemory()

    disclosure = DiscloseAndRecord(receipt_writer=receipt_memory).execute(
        result,
        DisclosureContext(
            disclosure_id="DISC-1",
            audience=DisclosureAudience.SUBJECT,
            purpose="respond to the subject's request",
            requested_finding_ids={result.findings[0].finding_id},
            requested_by_subject=True,
            policy_version="disclosure-test/v1",
        ),
    )

    assert disclosure.receipt.surfaced_finding_ids == [result.findings[0].finding_id]
    assert receipt_memory.receipts == [disclosure.receipt]
