# Canonicalization Security Boundary

> **Authority class: Class 3 — security policy and implementation contract.**
> Canonical records and generated authoritative projections remain operationally authoritative. This document defines the rules the runtime must enforce.

## Governing Principle

Ingestion may create evidence candidates. Only the restricted canonical writer may create canonical source state.

Provenance identifies origin, not truth. `REAL` means observed rather than manufactured; it does not mean accurate, trustworthy, or proven.

## Provenance Enforcement

The runtime enforces these immediate integrity controls:

1. Feedback provenance is mandatory and closed to `REAL`, `SYNTHETIC`, or `REPLAY`.
2. Missing or unknown provenance fails schema validation.
3. Every feedback record requires publication lineage and at least one proof boundary.
4. `REAL` feedback cannot carry a simulation scenario identifier.
5. `SYNTHETIC` and `REPLAY` feedback require a scenario identifier.
6. Scenario definitions must contain `SYNTHETIC` feedback and matching scenario identifiers.
7. Replay execution creates a new feedback record classified as `REPLAY`, regardless of the scenario template's source provenance.
8. `SYNTHETIC` and `REPLAY` feedback cannot be promoted into factual source records.
9. Validation failures and rejected promotion attempts create append-only workflow events.
10. Generated feedback views require explicit provenance, lineage, and proof-boundary fields and fail visibly when those fields are missing.

## Provenance Values

- `REAL`: an actual observed input. It may still be false, misleading, mistaken, adversarial, or irrelevant.
- `SYNTHETIC`: manufactured input used for testing, hypothesis generation, or scenario construction.
- `REPLAY`: execution output produced by running a synthetic scenario through the feedback pipeline.

No default provenance exists. Absence is invalid.

## Restricted Canonical Writer

`RestrictedCanonicalSourceWriter` is the sole ordinary application boundary for creating canonical source records.

The ordinary feedback-promotion path requires:

- `REAL` feedback provenance;
- an eligible structured proof review;
- a proof review bound to the exact current feedback SHA-256;
- an approved promotion authorization;
- authorization bound to the feedback ID, current feedback SHA-256, proof-review ID, target source ID, and deterministic idempotency key;
- authorization and proof review that are neither expired nor revoked;
- an unconflicted target-source reservation.

`IngestFeedback` delegates source creation to this writer. It does not construct or persist a `SourceRecord` itself.

Generic filesystem and GitHub record repositories reject attempts to save `SourceRecord` instances. Other canonical record types retain their existing repository behavior.

## Target Reservation and Idempotency

Before source creation, the writer persists a `CanonicalTargetReservation` containing:

- reservation ID;
- target source ID;
- subject ID;
- exact content SHA-256;
- authorization ID;
- deterministic idempotency key;
- write mode;
- reservation and commitment timestamps.

An exact retry returns the existing governed source. Reusing the same target for different content, authorization, or idempotency intent fails closed.

Sprint 4 establishes reservation and commitment contracts. Sprint 5 will extend them into a complete journaled transaction with recovery receipts and interruption handling.

## Exceptional Write Modes

Migration, disaster recovery, and bootstrap do not bypass the canonical writer. They require a separate `CanonicalMaintenanceAuthorization` bound to:

- a non-`NORMAL` write mode;
- exact proposed source content SHA-256;
- target source ID;
- deterministic idempotency key;
- authorizing actor;
- reason;
- explicit decision;
- authorization timestamp;
- optional expiration and revocation.

Supported modes are:

- `MIGRATION`
- `DISASTER_RECOVERY`
- `BOOTSTRAP`

`NORMAL` cannot be used by a maintenance authorization.

## Security Events

Implemented failure events include:

- `feedback.validation_failed`
- `feedback.replay_validation_failed`
- `feedback.promotion_denied`
- `canonical.write_rejected`

Implemented success and execution events include:

- `feedback.recorded`
- `feedback.replayed`
- `canonical.source_created`

Failure events contain reason codes and governed identifiers rather than unnecessary raw content.

## Audit Reconstruction

The repository audit verifies that:

- every committed reservation resolves to a canonical source;
- source and reservation idempotency keys match;
- source and reservation content hashes match;
- restricted-writer sources identify their reservation;
- feedback-derived sources retain feedback, authorization, proof-review, idempotency, and writer lineage.

A feedback-derived source missing those controls is an audit finding.

## Remaining Transaction Work

Sprint 4 establishes the restricted writer, exact-content authorization, structured proof review, durable target reservation, direct-write prevention, controlled maintenance modes, and reconstructable lineage.

The remaining canonicalization transaction work belongs to Sprint 5:

- journaled multi-record transaction state;
- recovery of interrupted reservations and partial operations;
- immutable promotion receipts as first-class records;
- authorization consumption and replay protection;
- atomic or compensating updates across source, feedback, reservation, event, and receipt state;
- migration and import receipts;
- full forensic reconstruction of transaction outcomes.

No automatic promotion is permitted.

## Verification

Focused tests cover:

- missing and unknown provenance;
- missing lineage and proof boundaries;
- invalid scenario relationships;
- audited ingestion and replay validation failures;
- missing, denied, expired, revoked, and mismatched authorization;
- stale, ineligible, expired, and revoked proof review;
- exact-content hash binding;
- deterministic idempotency;
- target conflicts;
- synthetic and replay promotion rejection;
- generic repository source-write rejection;
- maintenance-mode authorization and content binding;
- canonical reservation audit reconstruction;
- fail-closed generated projections.

The full runtime coverage workflow, canonicalization security workflow, work-control authority workflow, and general CI workflow must pass before merge.
