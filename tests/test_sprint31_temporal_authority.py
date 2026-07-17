from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from nks.application.sprint31_path_manifest import sprint31_temporal_authority_path_manifest
from nks.enki.temporal_authority import (
    LegacyTemporalRecord,
    TemporalAuthorityConflict,
    TemporalAuthorityDisposition,
    TemporalAuthorityEnvelope,
    TemporalAuthorityTimeline,
    migrate_legacy_temporal_record,
)
from nks.governance.approvals import ExecutionContext


T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
T1 = datetime(2026, 2, 1, tzinfo=timezone.utc)
T2 = datetime(2026, 3, 1, tzinfo=timezone.utc)
T3 = datetime(2026, 4, 1, tzinfo=timezone.utc)
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64


def _record(
    record_id: str,
    *,
    content_hash: str = HASH_A,
    disposition: TemporalAuthorityDisposition = TemporalAuthorityDisposition.ACTIVE,
    recorded_at: datetime = T0,
    effective_from: datetime = T0,
    effective_to: datetime | None = None,
    authority_valid_from: datetime = T0,
    authority_valid_to: datetime | None = None,
    superseded_at: datetime | None = None,
    revoked_at: datetime | None = None,
    consumed_at: datetime | None = None,
    retracted_at: datetime | None = None,
    supersedes_record_id: str | None = None,
    subject_id: str = "subject-1",
    domain: str = "general",
    authority_class: str = "canonical-state",
    lineage_parent_ids: tuple[str, ...] = (),
) -> TemporalAuthorityEnvelope:
    return TemporalAuthorityEnvelope(
        record_id=record_id,
        subject_id=subject_id,
        domain=domain,
        authority_class=authority_class,
        content_hash=content_hash,
        schema_version="1",
        recorded_at=recorded_at,
        effective_from=effective_from,
        effective_to=effective_to,
        authority_valid_from=authority_valid_from,
        authority_valid_to=authority_valid_to,
        superseded_at=superseded_at,
        revoked_at=revoked_at,
        consumed_at=consumed_at,
        retracted_at=retracted_at,
        supersedes_record_id=supersedes_record_id,
        lineage_parent_ids=lineage_parent_ids,
        disposition=disposition,
    )


def test_historical_truth_and_current_authority_are_distinct() -> None:
    historical = _record(
        "r1",
        disposition=TemporalAuthorityDisposition.SUPERSEDED,
        authority_valid_to=T1,
        superseded_at=T1,
    )
    current = _record(
        "r2",
        content_hash=HASH_B,
        recorded_at=T1,
        effective_from=T1,
        authority_valid_from=T1,
        supersedes_record_id="r1",
        lineage_parent_ids=("r1",),
    )
    timeline = TemporalAuthorityTimeline([current, historical])

    result = timeline.resolve(effective_at=T2, authority_at=T2)

    assert result.current_record_ids == ("r2",)
    assert result.historical_record_ids == ("r1",)
    assert timeline.records == (current, historical)


def test_recorded_effective_and_authority_time_are_independent() -> None:
    record = _record(
        "future-effective",
        recorded_at=T0,
        effective_from=T2,
        authority_valid_from=T1,
    )
    timeline = TemporalAuthorityTimeline([record])

    before_effective = timeline.resolve(effective_at=T1, authority_at=T2)
    after_effective = timeline.resolve(effective_at=T2, authority_at=T2)

    assert before_effective.current_record_ids == ()
    assert after_effective.current_record_ids == ("future-effective",)


def test_ambiguous_current_authority_fails_closed() -> None:
    timeline = TemporalAuthorityTimeline([_record("r1"), _record("r2", content_hash=HASH_B)])

    with pytest.raises(TemporalAuthorityConflict, match="ambiguous current authority"):
        timeline.resolve(effective_at=T1, authority_at=T1)


def test_invalid_temporal_window_is_rejected() -> None:
    with pytest.raises(ValidationError, match="effective_to cannot precede effective_from"):
        _record("bad-window", effective_from=T2, effective_to=T1)


def test_cross_authority_supersession_is_rejected() -> None:
    predecessor = _record(
        "r1",
        disposition=TemporalAuthorityDisposition.SUPERSEDED,
        authority_valid_to=T1,
        superseded_at=T1,
    )
    successor = _record(
        "r2",
        recorded_at=T1,
        effective_from=T1,
        authority_valid_from=T1,
        supersedes_record_id="r1",
        authority_class="different-authority",
    )

    with pytest.raises(ValueError, match="supersession cannot cross an authority key"):
        TemporalAuthorityTimeline([predecessor, successor])


def test_supersession_cycle_is_rejected() -> None:
    first = _record(
        "r1",
        disposition=TemporalAuthorityDisposition.SUPERSEDED,
        authority_valid_to=T0,
        superseded_at=T0,
        supersedes_record_id="r2",
    )
    second = _record(
        "r2",
        content_hash=HASH_B,
        disposition=TemporalAuthorityDisposition.SUPERSEDED,
        authority_valid_to=T0,
        superseded_at=T0,
        supersedes_record_id="r1",
    )

    with pytest.raises(ValueError, match="supersession cycle detected"):
        TemporalAuthorityTimeline([first, second])


@pytest.mark.parametrize(
    ("disposition", "timestamp_field"),
    [
        (TemporalAuthorityDisposition.REVOKED, "revoked_at"),
        (TemporalAuthorityDisposition.CONSUMED, "consumed_at"),
        (TemporalAuthorityDisposition.RETRACTED, "retracted_at"),
    ],
)
def test_terminal_authority_states_are_explicit(
    disposition: TemporalAuthorityDisposition, timestamp_field: str
) -> None:
    kwargs = {timestamp_field: T1}
    record = _record(
        disposition.value.lower(),
        disposition=disposition,
        authority_valid_to=T1,
        **kwargs,
    )

    assert getattr(record, timestamp_field) == T1
    assert record.is_authoritative_at(T0) is False


def test_terminal_disposition_without_terminal_evidence_is_rejected() -> None:
    with pytest.raises(ValidationError, match="REVOKED disposition requires revoked_at"):
        _record("revoked", disposition=TemporalAuthorityDisposition.REVOKED)


def test_hashes_and_resolution_are_deterministic_across_input_order() -> None:
    r1 = _record(
        "r1",
        disposition=TemporalAuthorityDisposition.SUPERSEDED,
        authority_valid_to=T1,
        superseded_at=T1,
    )
    r2 = _record(
        "r2",
        content_hash=HASH_B,
        recorded_at=T1,
        effective_from=T1,
        authority_valid_from=T1,
        supersedes_record_id="r1",
    )
    first = TemporalAuthorityTimeline([r1, r2])
    second = TemporalAuthorityTimeline([r2, r1])

    assert first.timeline_hash == second.timeline_hash
    assert (
        first.resolve(effective_at=T2, authority_at=T2).resolution_hash
        == second.resolve(effective_at=T2, authority_at=T2).resolution_hash
    )


def test_legacy_migration_preserves_identity_lineage_and_terminal_time() -> None:
    legacy = LegacyTemporalRecord(
        record_id="legacy-1",
        subject_id="subject-1",
        domain="general",
        authority_class="canonical-state",
        content_hash=HASH_A,
        observed_at=T0,
        effective_from=T0,
        status=TemporalAuthorityDisposition.SUPERSEDED,
    )

    migrated = migrate_legacy_temporal_record(
        legacy,
        schema_version="2",
        terminal_at=T1,
        lineage_parent_ids=("source-record",),
    )

    assert migrated.record_id == legacy.record_id
    assert migrated.content_hash == legacy.content_hash
    assert migrated.lineage_parent_ids == ("source-record",)
    assert migrated.superseded_at == T1
    assert migrated.authority_valid_to == T1


def test_legacy_migration_refuses_to_invent_missing_terminal_time() -> None:
    legacy = LegacyTemporalRecord(
        record_id="legacy-revoked",
        subject_id="subject-1",
        domain="general",
        authority_class="approval",
        content_hash=HASH_A,
        observed_at=T0,
        effective_from=T0,
        status=TemporalAuthorityDisposition.REVOKED,
    )

    with pytest.raises(ValueError, match="terminal_at is required"):
        migrate_legacy_temporal_record(legacy, schema_version="2")


SPRINT31_TESTED_PATHS = {
    "historical-truth-preserved",
    "current-authority-resolved",
    "effective-time-separated-from-recorded-time",
    "authority-valid-time-explicit",
    "supersession-chain-reconstructable",
    "revocation-terminal-state-explicit",
    "consumption-terminal-state-explicit",
    "retraction-terminal-state-explicit",
    "deterministic-timeline-hash",
    "deterministic-resolution-hash",
    "legacy-migration-preserves-lineage",
    "ambiguous-current-authority-denied",
    "invalid-temporal-window-denied",
    "cross-authority-supersession-denied",
    "missing-terminal-evidence-denied",
    "supersession-cycle-denied",
}


def test_every_declared_sprint31_path_has_automated_coverage() -> None:
    sprint31_temporal_authority_path_manifest().assert_complete_coverage(SPRINT31_TESTED_PATHS)


def test_sprint31_paths_are_test_only_and_prohibit_authority_escalation() -> None:
    manifest = sprint31_temporal_authority_path_manifest()
    assert manifest.execution_context == ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "historical-rewrite" in path.prohibited_effects
        assert "authority-escalation" in path.prohibited_effects
        assert "unsupported-supersession" in path.prohibited_effects
