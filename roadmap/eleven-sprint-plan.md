# Eleven-Sprint Execution Roadmap

> Active execution plan beginning 2026-07-12. Sprint numbering reflects execution order, not calendar duration. A sprint closes only when its acceptance evidence is committed or an explicit human gate is reached.

## Operating Cadence

Each sprint follows the same control loop:

1. Reconcile current canonical and repository state.
2. Implement the narrowest complete vertical slice.
3. Add positive, negative, idempotency, and recovery tests.
4. Regenerate authoritative projections.
5. Run hosted validation.
6. Record completion evidence and immediately begin the next unblocked sprint.

## Sprint 1 — Canonical Identity and Repository Truth

**Objective:** eliminate false audit findings and establish one schema-aware identity registry.

Deliverables:
- collection-aware identifier contract;
- support for request, event, registry, feedback, human-state, policy, receipt, and knowledge-state identifiers;
- duplicate and missing-ID regression tests;
- regenerated repository audit;
- zero unexplained identity findings;
- stale PR reconciliation complete.

Exit condition: canonical census includes every valid record and audit identity findings equal zero.

## Sprint 2 — Canonical Backlog and Roadmap Control Plane

**Objective:** stop manually maintained planning files from masquerading as implementation truth.

Deliverables:
- backlog item and sprint record models;
- filesystem repositories;
- evidence links and status-transition rules;
- deterministic backlog and roadmap views;
- authority-manifest and CI integration;
- migration of this roadmap into canonical records.

Exit condition: roadmap status is generated from evidence-bearing canonical work records.

## Sprint 3 — First Live Publication Cycle

**Objective:** move Publication 000001 through human gates and real-world operation.

Deliverables:
- visual review decision;
- publication approval decision;
- publication and social dispatch receipts;
- real feedback ingestion;
- feedback review and governed disposition;
- end-to-end cycle report.

Human gate: visual and publication approval cannot be automated or inferred.

Exit condition: one real publication-feedback cycle is reconstructable.

## Sprint 4 — Restricted Canonical Writer

**Objective:** create one enforceable boundary for canonical source mutation.

Deliverables:
- canonical writer protocol and implementation;
- prohibited direct-write tests;
- content-hash-bound authorization;
- candidate and proof-review requirements;
- idempotent target reservation;
- explicit recovery/migration exception boundary.

Exit condition: no ordinary application or adapter path can bypass canonicalization policy.

## Sprint 5 — Journaled Promotion Transaction

**Objective:** make canonical promotion atomic, recoverable, and receipted.

Deliverables:
- transaction intent and lifecycle;
- temporary writes and atomic commit;
- rollback/recovery behavior;
- immutable promotion receipt;
- replay/duplicate prevention;
- forensic transaction audit.

Exit condition: interrupted promotion cannot corrupt or ambiguously partially update canonical state.

## Sprint 6 — Temporal Human-State Productionization

**Objective:** finish the first human-evolution subsystem and integrate it into repository authority.

Deliverables:
- CLI operations;
- canonical collection and schema registration;
- generated current/history/transition/policy indexes;
- append-only events;
- privacy redaction;
- policy revocation receipts;
- model-behavior evaluation fixtures;
- audit reconstruction.

Exit condition: a human may evolve, revoke, refine, or contextualize model-facing state without erasing history or losing control.

## Sprint 7 — Governed Adaptive Knowledge Core

**Objective:** generalize temporal state to people, projects, organizations, products, policies, hypotheses, models, and the NKS itself.

Deliverables:
- governed subject model;
- generic knowledge-state model;
- domain/context/validity/confidence/authority semantics;
- mapping layer for human-state records;
- canonical schemas and persistence;
- migration strategy preserving human protections.

Exit condition: generic knowledge evolution is possible without flattening person-specific agency controls.

## Sprint 8 — Generic Transition Engine

**Objective:** govern how any knowledge state evolves.

Deliverables:
- transition state machine;
- correction, refinement, expansion, restriction, supersession, reversal, retraction, context shift, confidence change, merge, split, and deprecation;
- explicit versus inferred authority;
- conflict and concurrent-state handling;
- lineage and transition audit views.

Exit condition: current interpretation can change while historical evidence remains stable and attributable.

## Sprint 9 — Interpretation Resolution and Model Feedback

**Objective:** expose governed adaptive knowledge safely to model behavior.

Deliverables:
- interpretation resolver;
- context and authority matching;
- current-state and historical-context payloads;
- uncertainty and limitations;
- scoped ingestion policy;
- redaction, expiration, revocation, and receipts;
- no cross-domain contamination tests.

Exit condition: models receive authorized patterns of change rather than static profile fields.

## Sprint 10 — Forensic Audit, Migration, and Portability

**Objective:** prove the runtime is reconstructable and portable.

Deliverables:
- creation-path reconstruction for every canonical record;
- import/migration authority enforcement;
- schema migration fixtures;
- clean-room filesystem bootstrap;
- offline validation/manufacture/export/import/reconcile test;
- adapter contract parity;
- database adapter mapping.

Exit condition: the platform can leave GitHub without losing identity, lineage, authority, or behavior.

## Sprint 11 — Operational Proof and Release Candidate

**Objective:** convert the architecture into an evidenced release candidate.

Deliverables:
- repeated complete adaptive loop;
- security and behavior regression report;
- system identity and boundary documentation;
- known-limitations register;
- versioned release candidate;
- post-release operating cadence;
- next-horizon roadmap derived from observed operation rather than speculation.

Exit condition: the NKS has demonstrably governed knowledge evolution under real use.

## Dependencies and Human Gates

- Sprint 3 requires explicit human visual and publication approvals.
- External publishing depends on platform access and credentials; manual receipts remain valid fallback evidence.
- No sprint may auto-promote synthetic or replay data into factual canonical sources.
- Prediction and forecasting remain downstream consumers and are not canonical truth mechanisms.

## Program Success Criterion

The eleven-sprint program succeeds when this loop is operational, governed, and reconstructable:

```text
Observation
    ↓
Governed Knowledge State
    ↓
Authorized Transition
    ↓
Current Interpretation
    ↓
Scoped Model or Human Behavior
    ↓
Real Feedback
    ↓
Governed Evolution
```
