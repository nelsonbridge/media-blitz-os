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
