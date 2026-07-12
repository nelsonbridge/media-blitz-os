from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from nks.adapters.canonicalization import JsonCanonicalSourceStore
from nks.adapters.manual_delivery import JsonFeedbackRepository
from nks.application.canonicalization import (
    CanonicalTargetReservedError,
    CanonicalWriteAuthorizationError,
    CanonicalWriteIntegrityError,
    RestrictedCanonicalSourceWriter,
    feedback_sha256,
    promotion_idempotency_key,
    source_sha256,
)
from nks.domain.canonicalization import (
    CanonicalMaintenanceAuthorization,
    CanonicalWriteMode,
    ReservationStatus,
)
from nks.domain.delivery import (
    FeedbackClassification,
    FeedbackProofReview,
    FeedbackPromotionAuthorization,
    FeedbackProvenance,
    FeedbackRecord,
    PromotionDecision,
    ProofReviewDecision,
)
from nks.domain.models import RecordStatus, SourceRecord, WorkflowEvent

NOW = datetime(2026, 7, 12, 20, 40, tzinfo=timezone.utc)


class MemoryEvents:
    def __init__(self) -> None:
        self.items: list[WorkflowEvent] = []

    def append(self, event: WorkflowEvent) -> None:
        if not any(item.event_id == event.event_id for item in self.items):
            self.items.append(event)

    def list(self) -> list[WorkflowEvent]:
        return list(self.items)


def feedback(
    feedback_id: str = "NKS-FDB-000001",
    *,
    provenance: FeedbackProvenance = FeedbackProvenance.REAL,
) -> FeedbackRecord:
    return FeedbackRecord(
        feedback_id=feedback_id,
        publication_id="NKS-PUB-000001",
        platform="linkedin",
        classification=FeedbackClassification.CORRECTION,
        content="A reader suggests a factual correction.",
        provenance=provenance,
        scenario_id=("SYNTH-000001" if provenance != FeedbackProvenance.REAL else None),
        lineage_ids=["NKS-PUB-000001"],
        proof_boundaries=["Treat the response as an observation, not proof."],
    )


def review_for(
    item: FeedbackRecord,
    *,
    decision: ProofReviewDecision = ProofReviewDecision.ELIGIBLE,
    digest: str | None = None,
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> FeedbackProofReview:
    return FeedbackProofReview(
        review_id=f"NKS-PRV-{item.feedback_id}",
        feedback_id=item.feedback_id,
        feedback_sha256=digest or feedback_sha256(item),
        reviewed_by="S. Michael Nelson",
        reviewed_at=NOW - timedelta(minutes=5),
        decision=decision,
        evidence_ids=[item.publication_id],
        limitations=["Observation requires independent validation before proof use."],
        expires_at=expires_at,
        revoked_at=revoked_at,
    )


def authorization_for(
    item: FeedbackRecord,
    review: FeedbackProofReview,
    *,
    source_id: str = "NKS-SRC-000004",
    decision: PromotionDecision = PromotionDecision.APPROVED,
    feedback_id: str | None = None,
    digest: str | None = None,
    idempotency_key: str | None = None,
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> FeedbackPromotionAuthorization:
    content_hash = digest or feedback_sha256(item)
    authorization_id = f"NKS-AUTH-{item.feedback_id}"
    return FeedbackPromotionAuthorization(
        authorization_id=authorization_id,
        feedback_id=feedback_id or item.feedback_id,
        feedback_sha256=content_hash,
        target_source_id=source_id,
        proof_review_id=review.review_id,
        idempotency_key=idempotency_key
        or promotion_idempotency_key(content_hash, authorization_id, source_id),
        authorized_by="S. Michael Nelson",
        justification="Retain the observed correction as a review-state source.",
        decision=decision,
        authorized_at=NOW - timedelta(minutes=1),
        expires_at=expires_at,
        revoked_at=revoked_at,
    )


def writer_bundle(tmp_path: Path):
    events = MemoryEvents()
    feedback_repository = JsonFeedbackRepository(tmp_path)
    store = JsonCanonicalSourceStore(tmp_path / "records")
    writer = RestrictedCanonicalSourceWriter(
        store=store,
        feedback=feedback_repository,
        events=events,
        clock=lambda: NOW,
    )
    return writer, store, feedback_repository, events


def test_promote_feedback_is_persistent_reconstructable_and_idempotent(tmp_path: Path):
    writer, store, feedback_repository, events = writer_bundle(tmp_path)
    item = feedback()
    feedback_repository.save(item)
    review = review_for(item)
    authorization = authorization_for(item, review)

    first = writer.promote_feedback(
        item,
        source_id="NKS-SRC-000004",
        source_location="records/feedback/NKS-FDB-000001.json",
        authorization=authorization,
        proof_review=review,
    )
    second = writer.promote_feedback(
        item,
        source_id="NKS-SRC-000004",
        source_location="records/feedback/NKS-FDB-000001.json",
        authorization=authorization,
        proof_review=review,
    )

    assert first == second == store.get("NKS-SRC-000004")
    assert first.metadata["canonical_writer"] == "RestrictedCanonicalSourceWriter"
    assert first.metadata["authorization_id"] == authorization.authorization_id
    assert first.metadata["proof_review_id"] == review.review_id
    assert first.metadata["content_sha256"] == feedback_sha256(item)
    assert feedback_repository.get(item.feedback_id).promoted_to_source_id == first.id
    reservation = store.get_reservation(first.id)
    assert reservation is not None
    assert reservation.status == ReservationStatus.COMMITTED
    assert [event.event_type for event in events.list()] == [
        "canonical.source_created"
    ]


def test_changed_feedback_invalidates_review_and_authorization(tmp_path: Path):
    writer, _, _, events = writer_bundle(tmp_path)
    original = feedback()
    review = review_for(original)
    authorization = authorization_for(original, review)
    changed = original.model_copy(update={"content": "The correction changed after review."})

    with pytest.raises(CanonicalWriteAuthorizationError):
        writer.promote_feedback(
            changed,
            source_id="NKS-SRC-000004",
            source_location="records/feedback/NKS-FDB-000001.json",
            authorization=authorization,
            proof_review=review,
        )

    assert events.list()[-1].payload["reason_code"] == "CONTENT_HASH_MISMATCH"


@pytest.mark.parametrize(
    ("review", "reason_code"),
    [
        ("ineligible", "PROOF_REVIEW_INELIGIBLE"),
        ("expired", "PROOF_REVIEW_EXPIRED"),
        ("revoked", "PROOF_REVIEW_REVOKED"),
    ],
)
def test_proof_review_lifecycle_fails_closed(
    tmp_path: Path, review: str, reason_code: str
):
    writer, _, _, events = writer_bundle(tmp_path)
    item = feedback()
    kwargs = {}
    if review == "ineligible":
        kwargs["decision"] = ProofReviewDecision.INELIGIBLE
    elif review == "expired":
        kwargs["expires_at"] = NOW - timedelta(seconds=1)
    else:
        kwargs["revoked_at"] = NOW - timedelta(seconds=1)
    proof_review = review_for(item, **kwargs)
    authorization = authorization_for(item, proof_review)

    with pytest.raises(CanonicalWriteIntegrityError):
        writer.promote_feedback(
            item,
            source_id="NKS-SRC-000004",
            source_location="records/feedback/NKS-FDB-000001.json",
            authorization=authorization,
            proof_review=proof_review,
        )

    assert events.list()[-1].payload["reason_code"] == reason_code


@pytest.mark.parametrize(
    ("authorization_state", "reason_code"),
    [
        ("denied", "AUTHORIZATION_DENIED"),
        ("expired", "AUTHORIZATION_EXPIRED"),
        ("revoked", "AUTHORIZATION_REVOKED"),
    ],
)
def test_authorization_lifecycle_fails_closed(
    tmp_path: Path, authorization_state: str, reason_code: str
):
    writer, _, _, events = writer_bundle(tmp_path)
    item = feedback()
    proof_review = review_for(item)
    kwargs = {}
    if authorization_state == "denied":
        kwargs["decision"] = PromotionDecision.DENIED
    elif authorization_state == "expired":
        kwargs["expires_at"] = NOW - timedelta(seconds=1)
    else:
        kwargs["revoked_at"] = NOW - timedelta(seconds=1)
    authorization = authorization_for(item, proof_review, **kwargs)

    with pytest.raises(CanonicalWriteAuthorizationError):
        writer.promote_feedback(
            item,
            source_id="NKS-SRC-000004",
            source_location="records/feedback/NKS-FDB-000001.json",
            authorization=authorization,
            proof_review=proof_review,
        )

    assert events.list()[-1].payload["reason_code"] == reason_code


@pytest.mark.parametrize(
    "provenance",
    [FeedbackProvenance.SYNTHETIC, FeedbackProvenance.REPLAY],
)
def test_non_real_feedback_cannot_become_factual_source(
    tmp_path: Path, provenance: FeedbackProvenance
):
    writer, _, _, events = writer_bundle(tmp_path)
    item = feedback(provenance=provenance)
    proof_review = review_for(item)
    authorization = authorization_for(item, proof_review)

    with pytest.raises(CanonicalWriteIntegrityError):
        writer.promote_feedback(
            item,
            source_id="NKS-SRC-000004",
            source_location="records/feedback/NKS-FDB-000001.json",
            authorization=authorization,
            proof_review=proof_review,
        )

    assert events.list()[-1].payload["reason_code"] == "PROVENANCE_INELIGIBLE"


def test_conflicting_target_reservation_is_rejected(tmp_path: Path):
    writer, _, _, events = writer_bundle(tmp_path)
    first = feedback("NKS-FDB-000001")
    first_review = review_for(first)
    writer.promote_feedback(
        first,
        source_id="NKS-SRC-000004",
        source_location="records/feedback/NKS-FDB-000001.json",
        authorization=authorization_for(first, first_review),
        proof_review=first_review,
    )

    second = feedback("NKS-FDB-000002")
    second_review = review_for(second)
    with pytest.raises(CanonicalTargetReservedError):
        writer.promote_feedback(
            second,
            source_id="NKS-SRC-000004",
            source_location="records/feedback/NKS-FDB-000002.json",
            authorization=authorization_for(second, second_review),
            proof_review=second_review,
        )

    assert events.list()[-1].payload["reason_code"] == "TARGET_ALREADY_RESERVED"


def test_maintenance_write_requires_explicit_non_normal_authorization(tmp_path: Path):
    writer, store, _, events = writer_bundle(tmp_path)
    source = SourceRecord(
        id="NKS-SRC-LEGACY-000001",
        title="Migrated legacy source",
        status=RecordStatus.REVIEW,
        source_type="legacy-import",
        source_location="legacy/source.json",
    )
    digest = source_sha256(source)
    authorization_id = "NKS-MAINT-000001"
    key = promotion_idempotency_key(digest, authorization_id, source.id)
    authorization = CanonicalMaintenanceAuthorization(
        authorization_id=authorization_id,
        mode=CanonicalWriteMode.MIGRATION,
        target_source_id=source.id,
        source_sha256=digest,
        idempotency_key=key,
        authorized_by="S. Michael Nelson",
        reason="Controlled migration of a pre-boundary source.",
        decision=PromotionDecision.APPROVED,
        authorized_at=NOW - timedelta(minutes=1),
    )

    first = writer.write_maintenance_source(source, authorization=authorization)
    second = writer.write_maintenance_source(source, authorization=authorization)

    assert first == second == store.get(source.id)
    assert first.metadata["canonical_write_mode"] == CanonicalWriteMode.MIGRATION
    assert events.list()[0].payload["mode"] == CanonicalWriteMode.MIGRATION

    with pytest.raises(ValidationError):
        CanonicalMaintenanceAuthorization(
            **authorization.model_dump(),
            mode=CanonicalWriteMode.NORMAL,
        )


def test_maintenance_write_is_bound_to_exact_source_content(tmp_path: Path):
    writer, _, _, events = writer_bundle(tmp_path)
    source = SourceRecord(
        id="NKS-SRC-LEGACY-000001",
        title="Migrated legacy source",
        status=RecordStatus.REVIEW,
        source_type="legacy-import",
        source_location="legacy/source.json",
    )
    digest = "0" * 64
    authorization_id = "NKS-MAINT-000001"
    authorization = CanonicalMaintenanceAuthorization(
        authorization_id=authorization_id,
        mode=CanonicalWriteMode.DISASTER_RECOVERY,
        target_source_id=source.id,
        source_sha256=digest,
        idempotency_key=promotion_idempotency_key(
            digest, authorization_id, source.id
        ),
        authorized_by="S. Michael Nelson",
        reason="Recovery exercise.",
        decision=PromotionDecision.APPROVED,
        authorized_at=NOW - timedelta(minutes=1),
    )

    with pytest.raises(CanonicalWriteAuthorizationError):
        writer.write_maintenance_source(source, authorization=authorization)

    assert (
        events.list()[-1].payload["reason_code"]
        == "MAINTENANCE_CONTENT_HASH_MISMATCH"
    )
