# Canonicalization Security Boundary

> **Authority class: Class 3 — security policy and implementation contract.**
> Canonical records and generated authoritative projections remain operationally authoritative. This document defines the rules the runtime must enforce.

## Governing Principle

Ingestion may create evidence candidates. Only an explicitly authorized promotion operation may create a canonical source from feedback.

Provenance identifies origin, not truth. `REAL` means observed rather than manufactured; it does not mean accurate, trustworthy, or proven.

## Sprint 1 Enforcement

The runtime now enforces these immediate integrity controls:

1. Feedback provenance is mandatory and closed to `REAL`, `SYNTHETIC`, or `REPLAY`.
2. Missing or unknown provenance fails schema validation.
3. Every feedback record requires publication lineage and at least one proof boundary.
4. `REAL` feedback cannot carry a simulation scenario identifier.
5. `SYNTHETIC` and `REPLAY` feedback require a scenario identifier.
6. Scenario definitions must contain `SYNTHETIC` feedback and matching scenario identifiers.
7. Replay execution creates a new feedback record classified as `REPLAY`, regardless of the scenario template's source provenance.
8. `SYNTHETIC` and `REPLAY` feedback cannot be promoted into factual source records.
9. `REAL` feedback promotion requires an explicit authorization record bound to the feedback ID and target source ID.
10. Validation failures and rejected promotion attempts create append-only workflow events.
11. Generated feedback views require explicit provenance, lineage, and proof-boundary fields and fail visibly when those fields are missing.

## Provenance Values

- `REAL`: an actual observed input. It may still be false, misleading, mistaken, adversarial, or irrelevant.
- `SYNTHETIC`: manufactured input used for testing, hypothesis generation, or scenario construction.
- `REPLAY`: execution output produced by running a synthetic scenario through the feedback pipeline.

No default provenance exists. Absence is invalid.

## Promotion Authorization

A feedback-to-source promotion authorization contains:

- authorization ID;
- feedback ID;
- target source ID;
- authorizing actor;
- justification;
- explicit `APPROVED` or `DENIED` decision.

Authorization is not inferred from comments, email, platform metadata, prior ingestion, or the presence of a target source identifier.

## Security Events

Implemented failure events:

- `feedback.validation_failed`
- `feedback.replay_validation_failed`
- `feedback.promotion_denied`

Implemented success and execution events:

- `feedback.recorded`
- `feedback.replayed`
- `feedback.promoted_to_source`

Failure events contain reason codes and record hashes or identifiers rather than unnecessary raw content.

## Current Boundary and Remaining Work

Sprint 1 closes silent-trust paths but does not yet implement the complete canonicalization transaction model.

Remaining work includes:

- hash-bound authorizations;
- candidate lifecycle states;
- structured proof-review records;
- promotion receipts;
- a restricted canonical writer;
- atomic or journaled promotion;
- import and migration enforcement;
- repository-audit reconstruction of every canonical creation.

Until those controls exist, feedback promotion remains explicit, human-authorized, review-state source creation. No automatic promotion is permitted.

## Verification

Focused tests cover:

- missing and unknown provenance;
- missing lineage and proof boundaries;
- invalid scenario relationships;
- audited ingestion and replay validation failures;
- unauthorized and denied promotion;
- authorization mismatch;
- forced replay provenance;
- replay promotion rejection;
- fail-closed generated projections.

The full runtime coverage workflow and the canonicalization security workflow must pass before merge.
