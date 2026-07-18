from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from nks.application.governed_transactions import canonical_sha256
from nks.application.physical_canonical_persistence import (
    SCHEMA_V1_SQL,
    SCHEMA_V2_MIGRATION_SQL,
    SCHEMA_V2_ROLLBACK_SQL,
    PhysicalAuthorizationError,
    PhysicalConflictError,
    PhysicalMutationAuthorization,
    SQLiteCanonicalPersistence,
)
from nks.enki.temporal_authority import (
    LegacyTemporalRecord,
    TemporalAuthorityDisposition,
    TemporalAuthorityEnvelope,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_V1_PATH = ROOT / "infrastructure/enki-hosted-1.0-rc2/canonical-persistence-v1.sql"
MIGRATION_V2_PATH = (
    ROOT / "infrastructure/enki-hosted-1.0-rc2/canonical-persistence-v2-migration.sql"
)
ROLLBACK_V2_PATH = (
    ROOT / "infrastructure/enki-hosted-1.0-rc2/canonical-persistence-v2-rollback.sql"
)
T0 = datetime(2026, 7, 18, 0, 0, tzinfo=timezone.utc)
T1 = T0 + timedelta(hours=1)
T2 = T1 + timedelta(hours=1)


def content_hash(marker: str) -> str:
    return canonical_sha256({"marker": marker})


def envelope(
    record_id: str = "REC-1",
    *,
    marker: str = "alpha",
    subject_id: str = "SUBJECT-1",
    domain: str = "operations",
    authority_class: str = "GOVERNED",
    disposition: TemporalAuthorityDisposition = TemporalAuthorityDisposition.ACTIVE,
    recorded_at: datetime = T0,
    effective_from: datetime = T0,
    effective_to: datetime | None = None,
    authority_valid_from: datetime = T0,
    authority_valid_to: datetime | None = None,
    superseded_at: datetime | None = None,
    supersedes_record_id: str | None = None,
) -> TemporalAuthorityEnvelope:
    return TemporalAuthorityEnvelope(
        record_id=record_id,
        subject_id=subject_id,
        domain=domain,
        authority_class=authority_class,
        content_hash=content_hash(marker),
        schema_version="temporal-v1",
        recorded_at=recorded_at,
        effective_from=effective_from,
        effective_to=effective_to,
        authority_valid_from=authority_valid_from,
        authority_valid_to=authority_valid_to,
        superseded_at=superseded_at,
        supersedes_record_id=supersedes_record_id,
        disposition=disposition,
    )


def authorization(
    tenant_id: str,
    record: TemporalAuthorityEnvelope,
    *,
    auth_id: str | None = None,
    expires_at: datetime = T2,
    revoked_at: datetime | None = None,
) -> PhysicalMutationAuthorization:
    return PhysicalMutationAuthorization(
        authorization_id=auth_id or f"AUTH-{tenant_id}-{record.record_id}",
        tenant_id=tenant_id,
        record_id=record.record_id,
        content_hash=record.content_hash,
        issued_at=T0 - timedelta(minutes=1),
        expires_at=expires_at,
        revoked_at=revoked_at,
    )


def store() -> SQLiteCanonicalPersistence:
    persistence = SQLiteCanonicalPersistence.memory()
    persistence.initialize_v1(applied_at=T0)
    return persistence


def test_repository_sql_artifacts_match_executable_schema_contracts():
    assert SCHEMA_V1_PATH.read_text(encoding="utf-8").strip() == SCHEMA_V1_SQL
    assert MIGRATION_V2_PATH.read_text(encoding="utf-8").strip() == SCHEMA_V2_MIGRATION_SQL
    assert ROLLBACK_V2_PATH.read_text(encoding="utf-8").strip() == SCHEMA_V2_ROLLBACK_SQL


def test_governed_write_physically_preserves_all_temporal_authority_coordinates():
    persistence = store()
    record = envelope()

    receipt = persistence.write_canonical(
        "TENANT-A",
        record,
        authorization=authorization("TENANT-A", record),
        transaction_id="TX-001",
        now=T1,
    )
    reconstructed = persistence.reconstruct("TENANT-A")

    assert receipt.status == "COMMITTED"
    assert reconstructed.timeline == (record,)
    physical = reconstructed.timeline[0]
    assert physical.recorded_at == record.recorded_at
    assert physical.effective_from == record.effective_from
    assert physical.effective_to == record.effective_to
    assert physical.authority_valid_from == record.authority_valid_from
    assert physical.authority_valid_to == record.authority_valid_to
    assert physical.envelope_hash == record.envelope_hash
    assert persistence.current_authority_record_ids("TENANT-A") == ("REC-1",)


def test_direct_sql_canonical_insert_without_governed_guard_fails_closed():
    persistence = store()

    with pytest.raises(sqlite3.IntegrityError, match="GOVERNED_MUTATION_REQUIRED"):
        persistence.connection.execute(
            """
            INSERT INTO canonical_records(
                tenant_id, record_id, subject_id, domain, authority_class,
                content_hash, schema_version, recorded_at, effective_from,
                effective_to, authority_valid_from, authority_valid_to,
                superseded_at, revoked_at, consumed_at, retracted_at,
                supersedes_record_id, lineage_parent_ids_json, disposition,
                envelope_sha256
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "TENANT-A",
                "BYPASS-1",
                "SUBJECT-1",
                "operations",
                "GOVERNED",
                content_hash("bypass"),
                "temporal-v1",
                T0.isoformat(),
                T0.isoformat(),
                None,
                T0.isoformat(),
                None,
                None,
                None,
                None,
                None,
                None,
                "[]",
                "ACTIVE",
                "sha256:" + "0" * 64,
            ),
        )


def test_wrong_tenant_wrong_record_wrong_hash_expiry_and_revocation_are_denied():
    record = envelope()

    cases = [
        authorization("TENANT-B", record),
        PhysicalMutationAuthorization(
            authorization_id="AUTH-WRONG-RECORD",
            tenant_id="TENANT-A",
            record_id="REC-2",
            content_hash=record.content_hash,
            issued_at=T0 - timedelta(minutes=1),
            expires_at=T2,
        ),
        PhysicalMutationAuthorization(
            authorization_id="AUTH-WRONG-HASH",
            tenant_id="TENANT-A",
            record_id=record.record_id,
            content_hash=content_hash("other"),
            issued_at=T0 - timedelta(minutes=1),
            expires_at=T2,
        ),
        authorization("TENANT-A", record, expires_at=T1),
        authorization("TENANT-A", record, revoked_at=T1 - timedelta(minutes=1)),
    ]

    for index, invalid in enumerate(cases):
        persistence = store()
        with pytest.raises(PhysicalAuthorizationError, match="physical mutation denied"):
            persistence.write_canonical(
                "TENANT-A",
                record,
                authorization=invalid,
                transaction_id=f"TX-DENY-{index}",
                now=T1,
            )
        assert persistence.reconstruct("TENANT-A").timeline == ()


def test_transaction_reservation_receipt_and_events_are_reconstructable():
    persistence = store()
    record = envelope()
    persistence.write_canonical(
        "TENANT-A",
        record,
        authorization=authorization("TENANT-A", record),
        transaction_id="TX-JOURNAL",
        now=T1,
    )

    reconstructed = persistence.reconstruct("TENANT-A")
    events = persistence.connection.execute(
        "SELECT stage FROM physical_transaction_events WHERE transaction_id = ? ORDER BY event_id",
        ("TX-JOURNAL",),
    ).fetchall()
    reservation = persistence.connection.execute(
        "SELECT status, consumed_at FROM physical_reservations WHERE transaction_id = ?",
        ("TX-JOURNAL",),
    ).fetchone()

    assert reconstructed.transaction_ids == ("TX-JOURNAL",)
    assert len(reconstructed.reservation_ids) == 1
    assert len(reconstructed.receipt_ids) == 1
    assert [row["stage"] for row in events] == ["PLANNED", "RESERVED", "COMMITTED"]
    assert reservation["status"] == "CONSUMED"
    assert reservation["consumed_at"] == T1.isoformat()
    assert reconstructed.reconstruction_sha256.startswith("sha256:")


def test_exact_retry_returns_same_terminal_receipt_without_duplicate_effect():
    persistence = store()
    record = envelope()
    auth = authorization("TENANT-A", record)

    first = persistence.write_canonical(
        "TENANT-A",
        record,
        authorization=auth,
        transaction_id="TX-IDEMPOTENT",
        now=T1,
    )
    second = persistence.write_canonical(
        "TENANT-A",
        record,
        authorization=auth,
        transaction_id="TX-DIFFERENT-RETRY-ID",
        now=T1,
    )

    assert first == second
    assert persistence.connection.execute(
        "SELECT COUNT(*) AS count FROM canonical_records"
    ).fetchone()["count"] == 1
    assert persistence.connection.execute(
        "SELECT COUNT(*) AS count FROM physical_receipts"
    ).fetchone()["count"] == 1


def test_divergent_duplicate_is_denied_and_conflict_is_durably_reconstructable():
    persistence = store()
    original = envelope()
    persistence.write_canonical(
        "TENANT-A",
        original,
        authorization=authorization("TENANT-A", original),
        transaction_id="TX-ORIGINAL",
        now=T1,
    )
    divergent = envelope(marker="changed")

    with pytest.raises(PhysicalConflictError, match="physical canonical conflict"):
        persistence.write_canonical(
            "TENANT-A",
            divergent,
            authorization=authorization("TENANT-A", divergent),
            transaction_id="TX-DIVERGENT",
            now=T2,
        )

    reconstructed = persistence.reconstruct("TENANT-A")
    assert reconstructed.timeline == (original,)
    assert len(reconstructed.conflict_ids) == 1
    conflict = persistence.connection.execute(
        "SELECT reason_code FROM physical_conflicts"
    ).fetchone()
    assert conflict["reason_code"] == "DIVERGENT_DUPLICATE_RECORD_ID"


def test_cross_tenant_same_record_id_is_physically_isolated():
    persistence = store()
    tenant_a = envelope(marker="tenant-a")
    tenant_b = envelope(marker="tenant-b")

    persistence.write_canonical(
        "TENANT-A",
        tenant_a,
        authorization=authorization("TENANT-A", tenant_a),
        transaction_id="TX-A",
        now=T1,
    )
    persistence.write_canonical(
        "TENANT-B",
        tenant_b,
        authorization=authorization("TENANT-B", tenant_b),
        transaction_id="TX-B",
        now=T1,
    )

    assert persistence.reconstruct("TENANT-A").timeline == (tenant_a,)
    assert persistence.reconstruct("TENANT-B").timeline == (tenant_b,)
    assert persistence.canonical_fingerprint("TENANT-A") != persistence.canonical_fingerprint("TENANT-B")
    assert persistence.current_authority_record_ids("TENANT-A") == ("REC-1",)
    assert persistence.current_authority_record_ids("TENANT-B") == ("REC-1",)


def test_cross_tenant_supersession_cannot_reach_foreign_predecessor():
    persistence = store()
    predecessor = envelope(
        "REC-OLD",
        marker="old",
        disposition=TemporalAuthorityDisposition.SUPERSEDED,
        authority_valid_to=T1,
        superseded_at=T1,
    )
    persistence.write_canonical(
        "TENANT-A",
        predecessor,
        authorization=authorization("TENANT-A", predecessor),
        transaction_id="TX-OLD",
        now=T1,
    )
    successor = envelope(
        "REC-NEW",
        marker="new",
        recorded_at=T1,
        authority_valid_from=T1,
        supersedes_record_id="REC-OLD",
    )

    with pytest.raises(PhysicalConflictError):
        persistence.write_canonical(
            "TENANT-B",
            successor,
            authorization=authorization("TENANT-B", successor),
            transaction_id="TX-CROSS-TENANT",
            now=T2,
        )

    assert persistence.reconstruct("TENANT-B").timeline == ()


def test_valid_supersession_preserves_history_and_projects_only_successor_as_current():
    persistence = store()
    predecessor = envelope(
        "REC-OLD",
        marker="old",
        disposition=TemporalAuthorityDisposition.SUPERSEDED,
        authority_valid_to=T1,
        superseded_at=T1,
    )
    successor = envelope(
        "REC-NEW",
        marker="new",
        recorded_at=T1,
        authority_valid_from=T1,
        supersedes_record_id="REC-OLD",
    )

    persistence.write_canonical(
        "TENANT-A",
        predecessor,
        authorization=authorization("TENANT-A", predecessor),
        transaction_id="TX-OLD",
        now=T1,
    )
    persistence.write_canonical(
        "TENANT-A",
        successor,
        authorization=authorization("TENANT-A", successor),
        transaction_id="TX-NEW",
        now=T2,
    )

    reconstructed = persistence.reconstruct("TENANT-A")
    assert {item.record_id for item in reconstructed.timeline} == {"REC-OLD", "REC-NEW"}
    assert persistence.current_authority_record_ids("TENANT-A") == ("REC-NEW",)


def test_ambiguous_active_authority_fails_closed_and_is_journaled():
    persistence = store()
    first = envelope("REC-A", marker="a")
    second = envelope("REC-B", marker="b")
    persistence.write_canonical(
        "TENANT-A",
        first,
        authorization=authorization("TENANT-A", first),
        transaction_id="TX-AUTH-A",
        now=T1,
    )

    with pytest.raises(PhysicalConflictError):
        persistence.write_canonical(
            "TENANT-A",
            second,
            authorization=authorization("TENANT-A", second),
            transaction_id="TX-AUTH-B",
            now=T2,
        )

    assert persistence.current_authority_record_ids("TENANT-A") == ("REC-A",)
    reason = persistence.connection.execute(
        "SELECT reason_code FROM physical_conflicts"
    ).fetchone()["reason_code"]
    assert reason == "AMBIGUOUS_CURRENT_AUTHORITY"


def test_legacy_migration_preserves_identifiers_content_hash_and_time():
    persistence = store()
    legacy = LegacyTemporalRecord(
        record_id="LEGACY-1",
        subject_id="SUBJECT-LEGACY",
        domain="operations",
        authority_class="GOVERNED",
        content_hash=content_hash("legacy"),
        observed_at=T0,
        effective_from=T0 - timedelta(days=1),
        status=TemporalAuthorityDisposition.ACTIVE,
    )

    receipts = persistence.migrate_legacy_records(
        "TENANT-A",
        (legacy,),
        schema_version="temporal-v1",
        authorization_factory=lambda tenant, record: authorization(tenant, record),
        now=T1,
    )
    migrated = persistence.reconstruct("TENANT-A").timeline[0]

    assert len(receipts) == 1
    assert migrated.record_id == legacy.record_id
    assert migrated.subject_id == legacy.subject_id
    assert migrated.content_hash == legacy.content_hash
    assert migrated.recorded_at == legacy.observed_at
    assert migrated.effective_from == legacy.effective_from
    assert migrated.authority_valid_from == legacy.observed_at


def test_schema_v2_migration_preserves_canonical_fingerprint_and_adds_indexes():
    persistence = store()
    record = envelope()
    persistence.write_canonical(
        "TENANT-A",
        record,
        authorization=authorization("TENANT-A", record),
        transaction_id="TX-BEFORE-MIGRATION",
        now=T1,
    )
    before = persistence.canonical_fingerprint()

    receipt = persistence.migrate_to_v2(migration_id="MIGRATION-V2", applied_at=T2)

    assert persistence.current_schema_version() == 2
    assert receipt.pre_canonical_sha256 == before
    assert receipt.post_canonical_sha256 == before
    assert receipt.pre_schema_sha256 != receipt.post_schema_sha256
    indexes = {
        row["name"]
        for row in persistence.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    }
    assert {
        "idx_canonical_temporal_lookup",
        "idx_canonical_recorded_at",
        "idx_canonical_supersedes",
        "idx_transaction_tenant_record",
    }.issubset(indexes)


def test_schema_v2_rollback_restores_exact_prior_schema_and_canonical_fingerprints():
    persistence = store()
    record = envelope()
    persistence.write_canonical(
        "TENANT-A",
        record,
        authorization=authorization("TENANT-A", record),
        transaction_id="TX-ROLLBACK",
        now=T1,
    )
    initial_schema = persistence.schema_fingerprint()
    initial_canonical = persistence.canonical_fingerprint()
    persistence.migrate_to_v2(migration_id="MIGRATION-ROLLBACK", applied_at=T2)

    rollback = persistence.rollback_v2(
        migration_id="MIGRATION-ROLLBACK",
        rolled_back_at=T2 + timedelta(minutes=1),
    )

    assert persistence.current_schema_version() == 1
    assert rollback.restored_schema_sha256 == initial_schema
    assert rollback.restored_canonical_sha256 == initial_canonical
    assert persistence.schema_fingerprint() == initial_schema
    assert persistence.canonical_fingerprint() == initial_canonical
    migration = persistence.connection.execute(
        "SELECT rolled_back_at, rollback_schema_sha256, rollback_canonical_sha256 FROM schema_migrations WHERE migration_id = ?",
        ("MIGRATION-ROLLBACK",),
    ).fetchone()
    assert migration["rolled_back_at"] is not None
    assert migration["rollback_schema_sha256"] == initial_schema
    assert migration["rollback_canonical_sha256"] == initial_canonical
