"""Physical canonical persistence and migration contracts for Enki Sprint 40.

The SQLite adapter is a deterministic TEST double for the selected PostgreSQL
canonical-store role. It proves physical schema, transaction, reservation, receipt,
conflict, temporal-lineage, migration, rollback, and cross-tenant isolation semantics
without claiming that a live Neon database has been provisioned or certified.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.enki.temporal_authority import (
    LegacyTemporalRecord,
    TemporalAuthorityDisposition,
    TemporalAuthorityEnvelope,
    TemporalAuthorityTimeline,
    migrate_legacy_temporal_record,
)
from nks.governance.approvals import ExecutionContext


SCHEMA_VERSION_1 = 1
SCHEMA_VERSION_2 = 2
TARGET_SCHEMA_VERSION = SCHEMA_VERSION_2


SCHEMA_V1_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY,
    schema_sha256 TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mutation_guard (
    transaction_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    record_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    authorization_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS canonical_records (
    tenant_id TEXT NOT NULL,
    record_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    domain TEXT NOT NULL,
    authority_class TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    authority_valid_from TEXT NOT NULL,
    authority_valid_to TEXT,
    superseded_at TEXT,
    revoked_at TEXT,
    consumed_at TEXT,
    retracted_at TEXT,
    supersedes_record_id TEXT,
    lineage_parent_ids_json TEXT NOT NULL,
    disposition TEXT NOT NULL,
    envelope_sha256 TEXT NOT NULL,
    PRIMARY KEY (tenant_id, record_id)
);

CREATE TABLE IF NOT EXISTS current_authority (
    tenant_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    domain TEXT NOT NULL,
    authority_class TEXT NOT NULL,
    record_id TEXT NOT NULL,
    envelope_sha256 TEXT NOT NULL,
    PRIMARY KEY (tenant_id, subject_id, domain, authority_class),
    FOREIGN KEY (tenant_id, record_id)
      REFERENCES canonical_records(tenant_id, record_id)
);

CREATE TABLE IF NOT EXISTS physical_transactions (
    transaction_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    record_id TEXT NOT NULL,
    authorization_id TEXT NOT NULL,
    plan_sha256 TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    committed_at TEXT
);

CREATE TABLE IF NOT EXISTS physical_transaction_events (
    event_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    event_sha256 TEXT NOT NULL,
    FOREIGN KEY (transaction_id) REFERENCES physical_transactions(transaction_id)
);

CREATE TABLE IF NOT EXISTS physical_reservations (
    reservation_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    authority_key_sha256 TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    consumed_at TEXT,
    FOREIGN KEY (transaction_id) REFERENCES physical_transactions(transaction_id)
);

CREATE TABLE IF NOT EXISTS physical_receipts (
    receipt_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    record_id TEXT NOT NULL,
    input_sha256 TEXT NOT NULL,
    output_sha256 TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    receipt_sha256 TEXT NOT NULL,
    UNIQUE (tenant_id, record_id),
    FOREIGN KEY (transaction_id) REFERENCES physical_transactions(transaction_id)
);

CREATE TABLE IF NOT EXISTS physical_conflicts (
    conflict_id TEXT PRIMARY KEY,
    tenant_id_sha256 TEXT NOT NULL,
    authority_key_sha256 TEXT NOT NULL,
    attempted_record_id_sha256 TEXT NOT NULL,
    existing_record_id_sha256 TEXT,
    reason_code TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    conflict_sha256 TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_id TEXT PRIMARY KEY,
    from_version INTEGER NOT NULL,
    to_version INTEGER NOT NULL,
    pre_schema_sha256 TEXT NOT NULL,
    post_schema_sha256 TEXT NOT NULL,
    pre_canonical_sha256 TEXT NOT NULL,
    post_canonical_sha256 TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    rolled_back_at TEXT,
    rollback_schema_sha256 TEXT,
    rollback_canonical_sha256 TEXT
);

CREATE TRIGGER IF NOT EXISTS canonical_records_require_governed_guard
BEFORE INSERT ON canonical_records
BEGIN
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1 FROM mutation_guard
        WHERE tenant_id = NEW.tenant_id
          AND record_id = NEW.record_id
          AND content_hash = NEW.content_hash
    ) THEN RAISE(ABORT, 'GOVERNED_MUTATION_REQUIRED') END;
END;
""".strip()


SCHEMA_V2_MIGRATION_SQL = """
CREATE INDEX IF NOT EXISTS idx_canonical_temporal_lookup
ON canonical_records (
    tenant_id,
    subject_id,
    domain,
    authority_class,
    effective_from,
    authority_valid_from
);

CREATE INDEX IF NOT EXISTS idx_canonical_recorded_at
ON canonical_records (tenant_id, recorded_at);

CREATE INDEX IF NOT EXISTS idx_canonical_supersedes
ON canonical_records (tenant_id, supersedes_record_id);

CREATE INDEX IF NOT EXISTS idx_transaction_tenant_record
ON physical_transactions (tenant_id, record_id);
""".strip()


SCHEMA_V2_ROLLBACK_SQL = """
DROP INDEX IF EXISTS idx_transaction_tenant_record;
DROP INDEX IF EXISTS idx_canonical_supersedes;
DROP INDEX IF EXISTS idx_canonical_recorded_at;
DROP INDEX IF EXISTS idx_canonical_temporal_lookup;
""".strip()


class PhysicalPersistenceError(RuntimeError):
    """Base fail-closed physical persistence error."""


class PhysicalAuthorizationError(PhysicalPersistenceError):
    pass


class PhysicalConflictError(PhysicalPersistenceError):
    pass


class PhysicalMigrationError(PhysicalPersistenceError):
    pass


class PhysicalTransactionStatus(StrEnum):
    PLANNED = "PLANNED"
    RESERVED = "RESERVED"
    COMMITTED = "COMMITTED"


class PhysicalReservationStatus(StrEnum):
    RESERVED = "RESERVED"
    CONSUMED = "CONSUMED"


class PhysicalMutationAuthorization(BaseModel):
    """Exact TEST authority for one canonical physical mutation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    record_id: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    authority_class: Literal["GOVERNED_CANONICAL_WRITER"] = "GOVERNED_CANONICAL_WRITER"
    execution_context: Literal[ExecutionContext.TEST] = ExecutionContext.TEST
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None

    @model_validator(mode="after")
    def validate_lifecycle(self) -> "PhysicalMutationAuthorization":
        if self.expires_at <= self.issued_at:
            raise ValueError("physical mutation authorization expiry must follow issuance")
        if self.revoked_at is not None and self.revoked_at < self.issued_at:
            raise ValueError("physical mutation authorization revocation cannot precede issuance")
        return self


class PhysicalMutationReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: str
    transaction_id: str
    tenant_id: str
    record_id: str
    input_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    output_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    status: Literal["COMMITTED"] = "COMMITTED"
    created_at: datetime
    receipt_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "PhysicalMutationReceipt":
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"receipt_sha256"})
        )
        if self.receipt_sha256 != expected:
            raise ValueError("physical mutation receipt hash is invalid")
        return self


class PhysicalConflictRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    conflict_id: str
    tenant_id_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    authority_key_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    attempted_record_id_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    existing_record_id_sha256: str | None = Field(
        default=None, pattern=r"^sha256:[0-9a-f]{64}$"
    )
    reason_code: str
    occurred_at: datetime
    conflict_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "PhysicalConflictRecord":
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"conflict_sha256"})
        )
        if self.conflict_sha256 != expected:
            raise ValueError("physical conflict hash is invalid")
        return self


class SchemaMigrationReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    migration_id: str
    from_version: int
    to_version: int
    pre_schema_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    post_schema_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    pre_canonical_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    post_canonical_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    applied_at: datetime


class SchemaRollbackReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    migration_id: str
    restored_schema_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    restored_canonical_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    rolled_back_at: datetime


class PhysicalReconstruction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: str
    timeline: tuple[TemporalAuthorityEnvelope, ...]
    timeline_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    transaction_ids: tuple[str, ...]
    reservation_ids: tuple[str, ...]
    receipt_ids: tuple[str, ...]
    conflict_ids: tuple[str, ...]
    reconstruction_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "PhysicalReconstruction":
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"reconstruction_sha256"})
        )
        if self.reconstruction_sha256 != expected:
            raise ValueError("physical reconstruction hash is invalid")
        return self


class SQLiteCanonicalPersistence:
    """SQLite TEST double for the definitive physical canonical-store mapping."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")

    @classmethod
    def memory(cls) -> "SQLiteCanonicalPersistence":
        return cls(sqlite3.connect(":memory:"))

    @classmethod
    def file(cls, path: Path) -> "SQLiteCanonicalPersistence":
        return cls(sqlite3.connect(path))

    @property
    def connection(self) -> sqlite3.Connection:
        """Exposed for forensic TEST inspection, not as a governed mutation path."""
        return self._connection

    @staticmethod
    def _iso(value: datetime | None) -> str | None:
        return None if value is None else value.isoformat()

    @staticmethod
    def _load_time(value: str | None) -> datetime | None:
        return None if value is None else datetime.fromisoformat(value)

    def initialize_v1(self, *, applied_at: datetime) -> str:
        self._connection.executescript(SCHEMA_V1_SQL)
        schema_hash = self.schema_fingerprint()
        self._connection.execute(
            "INSERT OR REPLACE INTO schema_versions(version, schema_sha256, applied_at) VALUES (?, ?, ?)",
            (SCHEMA_VERSION_1, schema_hash, applied_at.isoformat()),
        )
        self._connection.commit()
        return schema_hash

    def current_schema_version(self) -> int:
        row = self._connection.execute(
            "SELECT MAX(version) AS version FROM schema_versions"
        ).fetchone()
        if row is None or row["version"] is None:
            raise PhysicalMigrationError("physical schema is not initialized")
        return int(row["version"])

    def schema_fingerprint(self) -> str:
        rows = self._connection.execute(
            """
            SELECT type, name, tbl_name, sql
            FROM sqlite_master
            WHERE name NOT LIKE 'sqlite_%'
            ORDER BY type, name
            """
        ).fetchall()
        return canonical_sha256([dict(row) for row in rows])

    def canonical_fingerprint(self, tenant_id: str | None = None) -> str:
        if tenant_id is None:
            rows = self._connection.execute(
                "SELECT * FROM canonical_records ORDER BY tenant_id, record_id"
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT * FROM canonical_records WHERE tenant_id = ? ORDER BY record_id",
                (tenant_id,),
            ).fetchall()
        return canonical_sha256([dict(row) for row in rows])

    def _assert_authorization(
        self,
        tenant_id: str,
        envelope: TemporalAuthorityEnvelope,
        authorization: PhysicalMutationAuthorization,
        *,
        now: datetime,
    ) -> None:
        if authorization.execution_context != ExecutionContext.TEST:
            raise PhysicalAuthorizationError("physical mutation denied")
        if authorization.tenant_id != tenant_id:
            raise PhysicalAuthorizationError("physical mutation denied")
        if authorization.record_id != envelope.record_id:
            raise PhysicalAuthorizationError("physical mutation denied")
        if authorization.content_hash != envelope.content_hash:
            raise PhysicalAuthorizationError("physical mutation denied")
        if authorization.expires_at <= now:
            raise PhysicalAuthorizationError("physical mutation denied")
        if authorization.revoked_at is not None and authorization.revoked_at <= now:
            raise PhysicalAuthorizationError("physical mutation denied")

    @staticmethod
    def _authority_key_sha256(envelope: TemporalAuthorityEnvelope) -> str:
        return canonical_sha256(envelope.authority_key)

    def _record_conflict(
        self,
        *,
        tenant_id: str,
        envelope: TemporalAuthorityEnvelope,
        existing_record_id: str | None,
        reason_code: str,
        now: datetime,
    ) -> PhysicalConflictRecord:
        sequence = self._connection.execute(
            "SELECT COUNT(*) AS count FROM physical_conflicts"
        ).fetchone()["count"] + 1
        payload = {
            "conflict_id": f"PHY-CONFLICT-{sequence:06d}",
            "tenant_id_sha256": canonical_sha256(tenant_id),
            "authority_key_sha256": self._authority_key_sha256(envelope),
            "attempted_record_id_sha256": canonical_sha256(envelope.record_id),
            "existing_record_id_sha256": (
                canonical_sha256(existing_record_id)
                if existing_record_id is not None
                else None
            ),
            "reason_code": reason_code,
            "occurred_at": now,
        }
        conflict = PhysicalConflictRecord(
            **payload,
            conflict_sha256=canonical_sha256(payload),
        )
        self._connection.execute(
            """
            INSERT INTO physical_conflicts(
                conflict_id, tenant_id_sha256, authority_key_sha256,
                attempted_record_id_sha256, existing_record_id_sha256,
                reason_code, occurred_at, conflict_sha256
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conflict.conflict_id,
                conflict.tenant_id_sha256,
                conflict.authority_key_sha256,
                conflict.attempted_record_id_sha256,
                conflict.existing_record_id_sha256,
                conflict.reason_code,
                conflict.occurred_at.isoformat(),
                conflict.conflict_sha256,
            ),
        )
        self._connection.commit()
        return conflict

    def _existing_envelope(
        self, tenant_id: str, record_id: str
    ) -> TemporalAuthorityEnvelope | None:
        row = self._connection.execute(
            "SELECT * FROM canonical_records WHERE tenant_id = ? AND record_id = ?",
            (tenant_id, record_id),
        ).fetchone()
        return None if row is None else self._row_to_envelope(row)

    def _row_to_envelope(self, row: sqlite3.Row) -> TemporalAuthorityEnvelope:
        return TemporalAuthorityEnvelope(
            record_id=row["record_id"],
            subject_id=row["subject_id"],
            domain=row["domain"],
            authority_class=row["authority_class"],
            content_hash=row["content_hash"],
            schema_version=row["schema_version"],
            recorded_at=self._load_time(row["recorded_at"]),
            effective_from=self._load_time(row["effective_from"]),
            effective_to=self._load_time(row["effective_to"]),
            authority_valid_from=self._load_time(row["authority_valid_from"]),
            authority_valid_to=self._load_time(row["authority_valid_to"]),
            superseded_at=self._load_time(row["superseded_at"]),
            revoked_at=self._load_time(row["revoked_at"]),
            consumed_at=self._load_time(row["consumed_at"]),
            retracted_at=self._load_time(row["retracted_at"]),
            supersedes_record_id=row["supersedes_record_id"],
            lineage_parent_ids=tuple(json.loads(row["lineage_parent_ids_json"])),
            disposition=TemporalAuthorityDisposition(row["disposition"]),
        )

    def _receipt_for_record(
        self, tenant_id: str, record_id: str
    ) -> PhysicalMutationReceipt | None:
        row = self._connection.execute(
            "SELECT * FROM physical_receipts WHERE tenant_id = ? AND record_id = ?",
            (tenant_id, record_id),
        ).fetchone()
        if row is None:
            return None
        return PhysicalMutationReceipt(
            receipt_id=row["receipt_id"],
            transaction_id=row["transaction_id"],
            tenant_id=row["tenant_id"],
            record_id=row["record_id"],
            input_sha256=row["input_sha256"],
            output_sha256=row["output_sha256"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            receipt_sha256=row["receipt_sha256"],
        )

    def _validate_supersession(
        self,
        tenant_id: str,
        envelope: TemporalAuthorityEnvelope,
        *,
        now: datetime,
    ) -> None:
        predecessor_id = envelope.supersedes_record_id
        if predecessor_id is None:
            return
        predecessor = self._existing_envelope(tenant_id, predecessor_id)
        if predecessor is None:
            self._record_conflict(
                tenant_id=tenant_id,
                envelope=envelope,
                existing_record_id=None,
                reason_code="SUPERSESSION_PREDECESSOR_MISSING_IN_TENANT",
                now=now,
            )
            raise PhysicalConflictError("physical canonical conflict")
        try:
            TemporalAuthorityTimeline((predecessor, envelope))
        except ValueError:
            self._record_conflict(
                tenant_id=tenant_id,
                envelope=envelope,
                existing_record_id=predecessor_id,
                reason_code="SUPERSESSION_TEMPORAL_LINEAGE_INVALID",
                now=now,
            )
            raise PhysicalConflictError("physical canonical conflict") from None

    def write_canonical(
        self,
        tenant_id: str,
        envelope: TemporalAuthorityEnvelope,
        *,
        authorization: PhysicalMutationAuthorization,
        transaction_id: str,
        now: datetime,
    ) -> PhysicalMutationReceipt:
        """Atomically persist one exact canonical record through the governed path."""

        self._assert_authorization(tenant_id, envelope, authorization, now=now)
        existing = self._existing_envelope(tenant_id, envelope.record_id)
        if existing is not None:
            if existing.envelope_hash == envelope.envelope_hash:
                receipt = self._receipt_for_record(tenant_id, envelope.record_id)
                if receipt is None:
                    raise PhysicalPersistenceError("idempotent record lacks terminal receipt")
                return receipt
            self._record_conflict(
                tenant_id=tenant_id,
                envelope=envelope,
                existing_record_id=envelope.record_id,
                reason_code="DIVERGENT_DUPLICATE_RECORD_ID",
                now=now,
            )
            raise PhysicalConflictError("physical canonical conflict")

        self._validate_supersession(tenant_id, envelope, now=now)

        if envelope.disposition == TemporalAuthorityDisposition.ACTIVE:
            current = self._connection.execute(
                """
                SELECT record_id FROM current_authority
                WHERE tenant_id = ? AND subject_id = ? AND domain = ? AND authority_class = ?
                """,
                (tenant_id, *envelope.authority_key),
            ).fetchone()
            if current is not None and current["record_id"] != envelope.supersedes_record_id:
                self._record_conflict(
                    tenant_id=tenant_id,
                    envelope=envelope,
                    existing_record_id=current["record_id"],
                    reason_code="AMBIGUOUS_CURRENT_AUTHORITY",
                    now=now,
                )
                raise PhysicalConflictError("physical canonical conflict")

        plan = {
            "transaction_id": transaction_id,
            "tenant_id": tenant_id,
            "record_id": envelope.record_id,
            "authorization_id": authorization.authorization_id,
            "envelope_sha256": envelope.envelope_hash,
        }
        plan_sha256 = canonical_sha256(plan)
        reservation_id = f"PHY-RES-{plan_sha256.removeprefix('sha256:')[:24]}"
        receipt_id = f"PHY-RCP-{plan_sha256.removeprefix('sha256:')[:24]}"
        authority_key_sha256 = self._authority_key_sha256(envelope)

        try:
            self._connection.execute("BEGIN IMMEDIATE")
            self._connection.execute(
                """
                INSERT INTO physical_transactions(
                    transaction_id, tenant_id, record_id, authorization_id,
                    plan_sha256, status, created_at, committed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    transaction_id,
                    tenant_id,
                    envelope.record_id,
                    authorization.authorization_id,
                    plan_sha256,
                    PhysicalTransactionStatus.PLANNED.value,
                    now.isoformat(),
                ),
            )
            self._insert_event(transaction_id, "PLANNED", now, plan_sha256)
            self._connection.execute(
                """
                INSERT INTO physical_reservations(
                    reservation_id, transaction_id, tenant_id, authority_key_sha256,
                    status, created_at, consumed_at
                ) VALUES (?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    reservation_id,
                    transaction_id,
                    tenant_id,
                    authority_key_sha256,
                    PhysicalReservationStatus.RESERVED.value,
                    now.isoformat(),
                ),
            )
            self._connection.execute(
                "UPDATE physical_transactions SET status = ? WHERE transaction_id = ?",
                (PhysicalTransactionStatus.RESERVED.value, transaction_id),
            )
            self._insert_event(
                transaction_id,
                "RESERVED",
                now,
                canonical_sha256(reservation_id),
            )
            self._connection.execute(
                """
                INSERT INTO mutation_guard(
                    transaction_id, tenant_id, record_id, content_hash, authorization_id
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    transaction_id,
                    tenant_id,
                    envelope.record_id,
                    envelope.content_hash,
                    authorization.authorization_id,
                ),
            )
            self._connection.execute(
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
                    tenant_id,
                    envelope.record_id,
                    envelope.subject_id,
                    envelope.domain,
                    envelope.authority_class,
                    envelope.content_hash,
                    envelope.schema_version,
                    self._iso(envelope.recorded_at),
                    self._iso(envelope.effective_from),
                    self._iso(envelope.effective_to),
                    self._iso(envelope.authority_valid_from),
                    self._iso(envelope.authority_valid_to),
                    self._iso(envelope.superseded_at),
                    self._iso(envelope.revoked_at),
                    self._iso(envelope.consumed_at),
                    self._iso(envelope.retracted_at),
                    envelope.supersedes_record_id,
                    json.dumps(list(envelope.lineage_parent_ids), separators=(",", ":")),
                    envelope.disposition.value,
                    envelope.envelope_hash,
                ),
            )
            self._connection.execute(
                "DELETE FROM mutation_guard WHERE transaction_id = ?",
                (transaction_id,),
            )
            if envelope.disposition == TemporalAuthorityDisposition.ACTIVE:
                self._connection.execute(
                    """
                    INSERT OR REPLACE INTO current_authority(
                        tenant_id, subject_id, domain, authority_class,
                        record_id, envelope_sha256
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tenant_id,
                        envelope.subject_id,
                        envelope.domain,
                        envelope.authority_class,
                        envelope.record_id,
                        envelope.envelope_hash,
                    ),
                )
            self._connection.execute(
                """
                UPDATE physical_reservations
                SET status = ?, consumed_at = ?
                WHERE reservation_id = ?
                """,
                (
                    PhysicalReservationStatus.CONSUMED.value,
                    now.isoformat(),
                    reservation_id,
                ),
            )
            output_sha256 = canonical_sha256(
                {
                    "tenant_id": tenant_id,
                    "record_id": envelope.record_id,
                    "envelope_sha256": envelope.envelope_hash,
                }
            )
            receipt_payload = {
                "receipt_id": receipt_id,
                "transaction_id": transaction_id,
                "tenant_id": tenant_id,
                "record_id": envelope.record_id,
                "input_sha256": plan_sha256,
                "output_sha256": output_sha256,
                "status": "COMMITTED",
                "created_at": now,
            }
            receipt = PhysicalMutationReceipt(
                **receipt_payload,
                receipt_sha256=canonical_sha256(receipt_payload),
            )
            self._connection.execute(
                """
                INSERT INTO physical_receipts(
                    receipt_id, transaction_id, tenant_id, record_id,
                    input_sha256, output_sha256, status, created_at, receipt_sha256
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.receipt_id,
                    receipt.transaction_id,
                    receipt.tenant_id,
                    receipt.record_id,
                    receipt.input_sha256,
                    receipt.output_sha256,
                    receipt.status,
                    receipt.created_at.isoformat(),
                    receipt.receipt_sha256,
                ),
            )
            self._connection.execute(
                """
                UPDATE physical_transactions
                SET status = ?, committed_at = ?
                WHERE transaction_id = ?
                """,
                (
                    PhysicalTransactionStatus.COMMITTED.value,
                    now.isoformat(),
                    transaction_id,
                ),
            )
            self._insert_event(
                transaction_id,
                "COMMITTED",
                now,
                receipt.receipt_sha256,
            )
            self._connection.commit()
            return receipt
        except sqlite3.Error as exc:
            self._connection.rollback()
            raise PhysicalPersistenceError("physical canonical transaction failed") from exc

    def _insert_event(
        self,
        transaction_id: str,
        stage: str,
        occurred_at: datetime,
        payload_sha256: str,
    ) -> None:
        count = self._connection.execute(
            "SELECT COUNT(*) AS count FROM physical_transaction_events WHERE transaction_id = ?",
            (transaction_id,),
        ).fetchone()["count"]
        payload = {
            "event_id": f"PHY-EVT-{transaction_id}-{count + 1:03d}",
            "transaction_id": transaction_id,
            "stage": stage,
            "occurred_at": occurred_at,
            "payload_sha256": payload_sha256,
        }
        self._connection.execute(
            """
            INSERT INTO physical_transaction_events(
                event_id, transaction_id, stage, occurred_at,
                payload_sha256, event_sha256
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload["event_id"],
                transaction_id,
                stage,
                occurred_at.isoformat(),
                payload_sha256,
                canonical_sha256(payload),
            ),
        )

    def migrate_to_v2(self, *, migration_id: str, applied_at: datetime) -> SchemaMigrationReceipt:
        if self.current_schema_version() != SCHEMA_VERSION_1:
            raise PhysicalMigrationError("schema migration requires version 1")
        pre_schema = self.schema_fingerprint()
        pre_canonical = self.canonical_fingerprint()
        try:
            self._connection.executescript(SCHEMA_V2_MIGRATION_SQL)
            post_schema = self.schema_fingerprint()
            post_canonical = self.canonical_fingerprint()
            if pre_canonical != post_canonical:
                raise PhysicalMigrationError("schema migration changed canonical fingerprint")
            self._connection.execute(
                "INSERT INTO schema_versions(version, schema_sha256, applied_at) VALUES (?, ?, ?)",
                (SCHEMA_VERSION_2, post_schema, applied_at.isoformat()),
            )
            self._connection.execute(
                """
                INSERT INTO schema_migrations(
                    migration_id, from_version, to_version, pre_schema_sha256,
                    post_schema_sha256, pre_canonical_sha256, post_canonical_sha256,
                    applied_at, rolled_back_at, rollback_schema_sha256,
                    rollback_canonical_sha256
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL)
                """,
                (
                    migration_id,
                    SCHEMA_VERSION_1,
                    SCHEMA_VERSION_2,
                    pre_schema,
                    post_schema,
                    pre_canonical,
                    post_canonical,
                    applied_at.isoformat(),
                ),
            )
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise
        return SchemaMigrationReceipt(
            migration_id=migration_id,
            from_version=SCHEMA_VERSION_1,
            to_version=SCHEMA_VERSION_2,
            pre_schema_sha256=pre_schema,
            post_schema_sha256=post_schema,
            pre_canonical_sha256=pre_canonical,
            post_canonical_sha256=post_canonical,
            applied_at=applied_at,
        )

    def rollback_v2(
        self, *, migration_id: str, rolled_back_at: datetime
    ) -> SchemaRollbackReceipt:
        row = self._connection.execute(
            "SELECT * FROM schema_migrations WHERE migration_id = ?",
            (migration_id,),
        ).fetchone()
        if row is None or row["rolled_back_at"] is not None:
            raise PhysicalMigrationError("migration is not available for rollback")
        if self.current_schema_version() != SCHEMA_VERSION_2:
            raise PhysicalMigrationError("rollback requires schema version 2")
        expected_schema = row["pre_schema_sha256"]
        expected_canonical = row["pre_canonical_sha256"]
        try:
            self._connection.executescript(SCHEMA_V2_ROLLBACK_SQL)
            self._connection.execute(
                "DELETE FROM schema_versions WHERE version = ?",
                (SCHEMA_VERSION_2,),
            )
            restored_schema = self.schema_fingerprint()
            restored_canonical = self.canonical_fingerprint()
            if restored_schema != expected_schema:
                raise PhysicalMigrationError("rollback did not restore prior schema fingerprint")
            if restored_canonical != expected_canonical:
                raise PhysicalMigrationError("rollback did not restore canonical fingerprint")
            self._connection.execute(
                """
                UPDATE schema_migrations
                SET rolled_back_at = ?, rollback_schema_sha256 = ?,
                    rollback_canonical_sha256 = ?
                WHERE migration_id = ?
                """,
                (
                    rolled_back_at.isoformat(),
                    restored_schema,
                    restored_canonical,
                    migration_id,
                ),
            )
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise
        return SchemaRollbackReceipt(
            migration_id=migration_id,
            restored_schema_sha256=restored_schema,
            restored_canonical_sha256=restored_canonical,
            rolled_back_at=rolled_back_at,
        )

    def migrate_legacy_records(
        self,
        tenant_id: str,
        records: Iterable[LegacyTemporalRecord],
        *,
        schema_version: str,
        authorization_factory,
        now: datetime,
        terminal_times: dict[str, datetime] | None = None,
    ) -> tuple[PhysicalMutationReceipt, ...]:
        receipts: list[PhysicalMutationReceipt] = []
        terminals = terminal_times or {}
        for index, legacy in enumerate(records, start=1):
            terminal = terminals.get(legacy.record_id)
            envelope = migrate_legacy_temporal_record(
                legacy,
                schema_version=schema_version,
                terminal_at=terminal,
            )
            authorization = authorization_factory(tenant_id, envelope)
            receipts.append(
                self.write_canonical(
                    tenant_id,
                    envelope,
                    authorization=authorization,
                    transaction_id=f"MIGRATE-{legacy.record_id}-{index:03d}",
                    now=now,
                )
            )
        return tuple(receipts)

    def reconstruct(self, tenant_id: str) -> PhysicalReconstruction:
        rows = self._connection.execute(
            "SELECT * FROM canonical_records WHERE tenant_id = ? ORDER BY recorded_at, record_id",
            (tenant_id,),
        ).fetchall()
        timeline = tuple(self._row_to_envelope(row) for row in rows)
        if timeline:
            TemporalAuthorityTimeline(timeline)
        transaction_ids = tuple(
            row["transaction_id"]
            for row in self._connection.execute(
                "SELECT transaction_id FROM physical_transactions WHERE tenant_id = ? ORDER BY transaction_id",
                (tenant_id,),
            ).fetchall()
        )
        reservation_ids = tuple(
            row["reservation_id"]
            for row in self._connection.execute(
                "SELECT reservation_id FROM physical_reservations WHERE tenant_id = ? ORDER BY reservation_id",
                (tenant_id,),
            ).fetchall()
        )
        receipt_ids = tuple(
            row["receipt_id"]
            for row in self._connection.execute(
                "SELECT receipt_id FROM physical_receipts WHERE tenant_id = ? ORDER BY receipt_id",
                (tenant_id,),
            ).fetchall()
        )
        tenant_hash = canonical_sha256(tenant_id)
        conflict_ids = tuple(
            row["conflict_id"]
            for row in self._connection.execute(
                "SELECT conflict_id FROM physical_conflicts WHERE tenant_id_sha256 = ? ORDER BY conflict_id",
                (tenant_hash,),
            ).fetchall()
        )
        payload = {
            "tenant_id": tenant_id,
            "timeline": timeline,
            "timeline_sha256": canonical_sha256(timeline),
            "transaction_ids": transaction_ids,
            "reservation_ids": reservation_ids,
            "receipt_ids": receipt_ids,
            "conflict_ids": conflict_ids,
        }
        return PhysicalReconstruction(
            **payload,
            reconstruction_sha256=canonical_sha256(payload),
        )

    def current_authority_record_ids(self, tenant_id: str) -> tuple[str, ...]:
        return tuple(
            row["record_id"]
            for row in self._connection.execute(
                "SELECT record_id FROM current_authority WHERE tenant_id = ? ORDER BY record_id",
                (tenant_id,),
            ).fetchall()
        )
