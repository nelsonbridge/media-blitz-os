# Enki Hosted RC2 Canonical Persistence Mapping

Sprint 40 maps Enki's immutable temporal-authority model into a deterministic physical schema suitable for the selected Neon Postgres canonical-store role.

The repository implementation uses SQLite as a credential-free TEST double. Passing SQLite validation proves the Enki physical mapping and lifecycle semantics; it does **not** claim a Neon instance has been provisioned or that production database controls have been certified.

## Physical canonical state

`canonical_records` stores one immutable row per `(tenant_id, record_id)` and preserves:

- subject and domain;
- authority class;
- content hash and schema version;
- recorded time;
- effective-from and effective-to time;
- authority-valid-from and authority-valid-to time;
- superseded, revoked, consumed, and retracted terminal times;
- supersession linkage;
- lineage parent identifiers;
- terminal/current disposition;
- exact temporal-envelope SHA-256.

Historical rows are never rewritten into current truth. `current_authority` is a separate tenant-scoped projection keyed by `(tenant, subject, domain, authority class)`.

## Governed write path

Canonical inserts are protected by a physical trigger requiring an exact short-lived `mutation_guard` row created only inside the governed adapter transaction. The adapter additionally requires a TEST-scoped `GOVERNED_CANONICAL_WRITER` authorization bound to:

- tenant;
- record identifier;
- exact content hash;
- issuance, expiry, and revocation state.

Direct canonical INSERT statements without the governed guard fail closed with `GOVERNED_MUTATION_REQUIRED`.

## Atomic evidence

One governed write atomically produces:

1. physical transaction plan;
2. append-only transaction events;
3. authority-key reservation;
4. immutable canonical row;
5. current-authority projection where applicable;
6. consumed reservation;
7. terminal mutation receipt.

Exact retry returns the existing terminal receipt. Divergent duplicate identifiers and competing current authority are rejected and recorded as privacy-preserving physical conflict evidence.

## Tenant isolation

Tenant identity is part of every canonical primary key and every current-authority key. Supersession lookup is tenant-scoped. A record in one tenant cannot serve as the predecessor of a record in another tenant.

## Versioned schema migration

- `canonical-persistence-v1.sql` establishes canonical rows, authority projection, transaction/reservation/receipt/conflict journals, migration journal, and the governed-write trigger.
- `canonical-persistence-v2-migration.sql` adds the temporal, recorded-time, supersession, and transaction lookup indexes required by the hosted mapping.
- `canonical-persistence-v2-rollback.sql` removes only those V2 indexes.

The migration engine records pre/post schema and canonical fingerprints. V2 migration must leave the canonical fingerprint unchanged. Rollback must restore both the exact V1 schema fingerprint and the exact pre-migration canonical fingerprint.

## Legacy temporal migration

Legacy records are converted through the existing governed `migrate_legacy_temporal_record` contract, then persisted through the same governed physical mutation path. Missing terminal authority evidence is never invented.

## Reconstruction

Tenant reconstruction returns:

- the exact immutable temporal timeline;
- timeline hash;
- transaction identities;
- reservation identities;
- receipt identities;
- conflict identities;
- deterministic reconstruction hash.

## Production boundary

This package does not authorize:

- a live Neon TEST or production database;
- production credentials or production data;
- managed database row-level security certification;
- network segmentation certification;
- production secrets management;
- production execution.

Those remain separate external capability and production-control gates.
