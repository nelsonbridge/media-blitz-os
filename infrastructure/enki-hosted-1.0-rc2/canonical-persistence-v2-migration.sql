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
