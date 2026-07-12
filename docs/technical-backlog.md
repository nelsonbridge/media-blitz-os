# Technical Backlog

> Authority class: Class 3 active execution plan. Implementation status is evidenced by canonical records, merged code, generated projections, tests, receipts, and workflow results—not by this document alone.

Last reconciled: 2026-07-12

## Purpose

Govern the next implementation sequence for the Nelson Knowledge System while preserving portability, explicit authority, human agency, reconstructable lineage, and platform-neutral domain logic.

## Status Vocabulary

- **Complete** — implemented and evidenced on `sandbox`.
- **Partial** — useful implementation exists; acceptance criteria remain.
- **Active** — assigned to the current sprint.
- **Planned** — sequenced in the eleven-sprint roadmap.
- **Blocked: Human Decision** — engineering is complete enough that explicit human approval is required.
- **Superseded** — replaced by a later architectural decision.

## Reconciled Foundation

| Prior item | Status | Evidence / remaining condition |
|---|---|---|
| TB-001 Package boundaries | Complete | Domain, application, adapter, CLI, audit, and view layers exist. |
| TB-002 Canonical schemas | Partial | Core Pydantic models exist; schema versioning and newer record-family registration remain. |
| TB-003 Repository interfaces | Partial | Neutral services/adapters exist; interface consistency and restricted canonical writer remain. |
| TB-004 Filesystem adapter | Complete | Local deterministic persistence and portable bundles exist. |
| TB-005 GitHub adapter | Partial | Adapter exists; equivalent contract suite against filesystem remains. |
| TB-006 Drive adapter contract | Partial | Contract and projection role exist; durable queued synchronization remains. |
| TB-007 State machines | Partial | Publication, provenance, replay, and human-state constraints exist; generic transition engine remains. |
| TB-008 Governance as code | Complete | Readiness, approval, authority, provenance, and promotion validators are executable. |
| TB-009 Event/audit model | Partial | Append-only events exist; full workflow reconstruction remains. |
| TB-010 Generated views | Complete | Generated authority manifest and deterministic projections exist. |
| TB-011 Runtime CLI | Partial | Operational commands exist; human-state/GAK and transaction commands remain. |
| TB-012 Functional harness | Partial | Deterministic tests exist; complete live source-to-feedback vertical slice remains. |
| TB-013 Integration contracts | Partial | Social and selected adapter tests exist; broader contract parity remains. |
| TB-014 Export/migration | Partial | Checksummed export/import exists; migration enforcement for new record families remains. |
| TB-015 Database runway | Planned | Repository mapping and migration proof remain. |
| TB-016 Orchestrator independence | Complete | Application services are callable outside Actions; workflows are secondary. |
| TB-017 Dependency extraction | Partial | Portability design exists; clean-room extraction test remains. |
| TB-018 Provenance/promotion security | Complete — Sprint 1 boundary | `REAL | SYNTHETIC | REPLAY`, authorization, replay isolation, and failure events are enforced. |
| TB-019 Runtime validation hardening | Partial | Immediate fail-closed gates exist; transactional promotion and restricted writing remain. |

## Active Backlog

### BL-001 — Schema-Aware Canonical Identity
**Status:** Active — Sprint 1

Reapply the valid work from closed PR #7 onto current `sandbox`.

Acceptance criteria:
- Record identity resolves through an explicit collection contract.
- `request_id`, `event_id`, `registry_id`, human-state IDs, and future knowledge-state IDs are recognized without imposing a false universal field.
- Duplicate identity detection remains global.
- Repository audit reports zero unexplained identity findings.
- Regression tests cover missing and duplicate IDs.

### BL-002 — Backlog and Roadmap as Generated State
**Status:** Planned — Sprint 2

Create canonical backlog/sprint records and deterministic human-readable projections.

Acceptance criteria:
- Work status is machine-readable.
- Completion requires linked implementation evidence.
- Generated backlog and roadmap drift fails CI.
- Narrative plans cannot declare implementation complete without evidence.

### BL-003 — Publication 000001 Human Gate and Live Cycle
**Status:** Blocked: Human Decision / Planned — Sprint 3

Acceptance criteria:
- Visual review decision recorded.
- Publication approval recorded separately.
- Publication receipt and external URL persisted.
- Approved social derivatives dispatched or manual receipts recorded.
- Real feedback captured with provenance and lineage.
- No approval is inferred from rendering or test success.

### BL-004 — Restricted Canonical Writer
**Status:** Planned — Sprint 4

Acceptance criteria:
- Only one application boundary may create or mutate canonical source state.
- Direct adapter writes are rejected or isolated to recovery/migration procedures.
- Authorization binds feedback ID, exact content hash, target source ID, proof review, actor, and decision.
- Idempotency is enforced.

### BL-005 — Journaled Promotion and Receipts
**Status:** Planned — Sprint 5

Acceptance criteria:
- Promotion is atomic or journaled and recoverable.
- Partial operations cannot leave inconsistent source, event, authorization, or receipt state.
- Immutable promotion receipts capture input/output hashes and transaction lineage.
- Audit detects incomplete or replayed transactions.

### BL-006 — Temporal Human-State Production Integration
**Status:** Planned — Sprint 6

Acceptance criteria:
- CLI commands, canonical collection registration, generated indexes, authority manifest entries, workflow events, privacy redaction, revocation receipts, and evaluation fixtures are implemented.
- Historical observations remain immutable.
- Current behavioral authority is resolved independently from historical truth.
- Model-ingestion scope remains separate from canonicalization.

### BL-007 — Governed Adaptive Knowledge Core
**Status:** Planned — Sprint 7

Acceptance criteria:
- Generic `KnowledgeState`, governed subject, domain, context, confidence, validity, and authority models exist.
- Human-state semantics can map onto the generic core without losing human-agency protections.
- Prediction remains outside canonical state.

### BL-008 — Generic Transition Engine
**Status:** Planned — Sprint 8

Acceptance criteria:
- Supports correction, refinement, expansion, restriction, supersession, reversal, retraction, context shift, confidence change, merge, split, and deprecation.
- Invalid transitions fail explicitly.
- Transition lineage is reconstructable and context-scoped.
- Inference remains distinguishable from explicit declaration.

### BL-009 — Governed Interpretation and Model Feedback
**Status:** Planned — Sprint 9

Acceptance criteria:
- `ResolveInterpretation(subject, domain, context, scope, authority)` returns current interpretation, history, uncertainty, limitations, and behavior instructions.
- Model-feedback publication is content-hash-bound, scoped, redactable, expirable, revocable, and receipted.
- Superseded state cannot continue controlling behavior.

### BL-010 — Forensic Audit and Clean-Room Portability
**Status:** Planned — Sprint 10

Acceptance criteria:
- Every canonical creation is reconstructable.
- Imports and migrations cannot bypass provenance or authority gates.
- Clean filesystem initialization, validation, manufacture, export, import, and reconciliation pass without GitHub or network access.
- Filesystem and GitHub adapter contract behavior is equivalent except for adapter metadata.

### BL-011 — Operational Proof and Release Candidate
**Status:** Planned — Sprint 11

Acceptance criteria:
- At least one complete observation-to-publication-to-real-feedback-to-governed-evolution loop is recorded.
- Security, authority, portability, and model-behavior regression suites pass.
- Release documentation reflects actual system identity: Nelson Knowledge System as implementation, Knowledge Manufacturing / Governed Adaptive Knowledge as architecture, Media Blitz as an application program.
- A versioned release candidate is produced with known limitations.

## Cross-Cutting Backlog

- Detect undeclared status-like files and contradictory narrative claims.
- Require generator or canonical-input changes for authoritative projection changes.
- Add schema versions, migration fixtures, and deprecation policy.
- Raise coverage expectations for security-critical modules.
- Normalize repository naming and README system boundaries.
- Complete the Agile manuscript evidence and publication package after the first live publication cycle.
- Consolidate duplicate or placeholder corpus assets before ingestion.

## Release Guardrails

No release may claim production-grade adaptive knowledge until:

1. canonical identity findings are zero or explicitly waived;
2. promotion is restricted, hash-bound, receipted, and recoverable;
3. human evolution can alter current behavior without rewriting history;
4. model ingestion is independently scoped and revocable;
5. one real feedback loop is completed;
6. every canonical creation is forensically reconstructable;
7. clean-room portability passes.

## Execution Rule

When the user says `Execute`, continue through the active sprint and immediately begin the next unblocked sprint. Stop only for an explicit human approval gate, unavailable external capability, failed invariant that requires user choice, or a material security ambiguity.