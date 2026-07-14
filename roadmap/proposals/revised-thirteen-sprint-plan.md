# Revised Thirteen-Sprint Execution Plan

> **Authority class: Class 3 — proposed roadmap revision.**
> This proposal does not alter canonical sprint status. Accepted changes must be promoted through the governed work-control path, followed by deterministic regeneration of the canonical roadmap and backlog.

- Proposed date: 2026-07-13
- Target: complete the internal execution sequence through Sprint 13 today where exit evidence supports completion
- Governing constraint: no sprint may be marked complete merely to satisfy the date target

## Why the roadmap is being refactored

The existing roadmap combines several independently governable concerns inside large sequential sprints and treats the first live publication cycle as though it were a critical-path prerequisite for internal platform work.

Sprint 3 dependency analysis demonstrated a more accurate structure:

1. independently manufactured and reviewed objects;
2. object-specific authority;
3. explicit convergence only at the point of external effect;
4. manual or automated adapters treated as replaceable execution mechanisms;
5. external validation treated as evidence, not as permission to continue unrelated internal construction.

The revised plan applies that modular pattern to the remaining roadmap.

## Governing revisions

1. **Sprints 1, 2, and 4 remain historically complete.** Their scope and evidence are not rewritten.
2. **Sprint 3 remains open as a parallel external-validation lane.** It no longer blocks Sprints 5–13.
3. **Sprints 5–11 are decomposed and extended through Sprint 13.** Each sprint owns one primary governed capability and one reviewable evidence boundary.
4. **Internal release-candidate proof and external production proof are separated.** Sprint 13 may establish an internally complete release candidate without falsely claiming that Sprint 3's public publication and REAL-feedback cycle has occurred.
5. **Canonical completion remains evidence-bearing.** Planning approval authorizes the revised roadmap; it does not pre-approve implementation completion.

## Execution topology

```text
Historical foundation
S1 ── S2 ── S4
              │
              v
Internal construction lane
S5 ── S6 ── S7 ── S8 ── S9 ── S10 ── S11 ── S12 ── S13

Parallel external-validation lane
S3: content + visuals + configuration → production approval → publication → receipts → REAL feedback

Convergence milestone
S3 complete + S13 complete = internally hardened system with demonstrated external cycle
```

Sprint 3 may consume any stable capability produced by the internal lane, but absence of a publishing adapter, visual approval, account configuration, or public response cannot halt unrelated internal work.

---

# Preserved Sprints

## Sprint 1 — Canonical identity and repository truth

- ID: `NKS-SPR-001`
- Status: preserved as `complete`
- Revision: none

## Sprint 2 — Canonical backlog and roadmap control plane

- ID: `NKS-SPR-002`
- Status: preserved as `complete`
- Revision: none

## Sprint 3 — First live publication and REAL-feedback proof

- ID: `NKS-SPR-003`
- Status: remains open until external evidence exists
- Lane: parallel external validation

### Revised objective

Complete Publication 000001 through independently reviewed content, visuals, publication configuration, explicit production authorization, external publication, receipts, attributable REAL feedback, governed disposition, and an end-to-end cycle report.

### Dependency rule

Sprint 3 is not a prerequisite for Sprints 5–13. Its internal components proceed independently and converge only before the authorized external effect.

### Exit criteria

- Content decision is recorded and bound to the exact body hash.
- Visual decision is recorded and bound to the exact manifest hash.
- Channel, identity, byline, and brand configuration are recorded.
- Final production publication approval is explicit and hash-bound.
- Publication and applicable social-distribution receipts exist.
- Attributable REAL feedback is ingested with publication lineage.
- Feedback disposition and end-to-end cycle report exist.

## Sprint 4 — Restricted canonical writer

- ID: `NKS-SPR-004`
- Status: preserved as `complete`
- Revision: none

---

# Revised Internal Construction Lane

## Sprint 5 — Context-Bound Approval and Transaction Foundation

- ID: `NKS-SPR-005`
- Primary capability: authority and transaction integrity

### Objective

Establish one fail-closed approval lifecycle and transaction foundation for canonical mutation, migration, disclosure, model use, and external effects.

### Scope

- TEST and PRODUCTION execution contexts.
- Approval grants bound to action, subject, exact content hash, authority class, validity, revocation, transaction, and execution context.
- AVAILABLE → RESERVED → CONSUMED lifecycle with exact-retry semantics.
- Journaled operations, immutable receipts, rollback release, interruption recovery, and idempotency.
- Policy isolation and adapter-level capability isolation.
- Legacy Boolean approval fields classified as compatibility inputs, never independent authority.

### Exit criteria

- TEST authority cannot satisfy a PRODUCTION gate or produce a production effect.
- Interrupted operations converge to one committed transaction or one documented rollback.
- Approval reservation and consumption are durable, reconstructable, and exact-retry safe.
- Ambiguous, stale, revoked, expired, mismatched, or cross-context authority fails closed.
- Implementation evidence and validation results are attached to the sprint record.

### Review gate

Confirm the authority model before any later sprint consumes it.

---

## Sprint 6 — Enki Cognitive-Core Boundary and Generic Contracts

- ID: `NKS-SPR-006`
- Primary capability: bounded cognitive and reconciliation kernel

### Objective

Formalize Enki as a product-neutral cognitive and reconciliation core with explicit constitutional boundaries and stable ports.

### Scope

- Subject, evidence, observation, relationship, context, temporal applicability, confidence, finding, disclosure, result, and receipt contracts.
- Persistence- and product-neutral reader and writer ports.
- Constitutional traceability from invariant to contract, service, test, and receipt field.
- Dependency tests preventing Person Object, Organization Object, EOA/V8, clinical, maturity, profile, and product ontologies from becoming Enki core.
- Explicit preservation of user-owned objectives, priorities, choices, values, accountability, and outcomes.

### Exit criteria

- Core imports no product package and requires no complete Person or Organization object.
- Core cannot silently substitute user objectives or priorities.
- Raw evidence and observations remain preservable for reinterpretation.
- Relationship and interpretation strategies are versionable and replaceable.
- Architecture decision and executable boundary tests pass.

### Review gate

Confirm that the bounded context reflects Enki's constitutional role before generic state is persisted through it.

---

## Sprint 7 — Generic Observation, Relationship, and State-Write Substrate

- ID: `NKS-SPR-007`
- Primary capability: governed state creation across subject classes

### Objective

Implement one append-only, schema-governed substrate for observations, relationship assertions, and generic state creation without subject-specific schema forks.

### Scope

- Shared canonical collections and strict schemas.
- Generic state-write plans for PERSON, ORGANIZATION, and PROJECT reference subjects.
- Exact plan hashing, subject/context binding, known-reference integrity, approval consumption, transaction journaling, immutable receipts, and retry recovery.
- Repository census, canonical validation, generated-view registration, and forensic integrity checks.

### Exit criteria

- One human and at least two nonhuman subject classes use identical core contracts and collections.
- State creation is approval-bound, journaled, receipted, recoverable, and auditable.
- Unknown references, subject leakage, context mismatch, duplicate writes, tampering, and cross-transaction replay fail closed.
- No human-specific protection is weakened by generic storage.

### Review gate

Confirm that genericity is proven through reuse rather than achieved by discarding enforceable semantics.

---

## Sprint 8 — Human-State Compatibility, Authority, and Governed Migration

- ID: `NKS-SPR-008`
- Primary capability: strict human overlay on generic Enki core

### Objective

Project the temporal human-state reference implementation into the generic substrate while preserving human agency, historical meaning, privacy, and explicit expression origin.

### Scope

- Compatibility adapter outside Enki core.
- Explicit distinction among subject declaration, quoted expression, governed inference, and unknown origin.
- Human correction, retraction, consent, privacy, purpose, redaction, expiration, and revocation protections.
- Side-effect-free content-addressed migration plans.
- Approval bound to exact migration plan hash, action, subject, execution context, authority, and transaction.
- Immutable migration receipts and interruption recovery.

### Exit criteria

- Historical human records are projected without rewriting canonical history.
- Legacy Boolean model-feedback fields do not become generic authority.
- Every migrated human observation has an explicit expression-origin decision.
- Partial migration recovers through the same transaction without duplicates.
- Human privacy and authority remain stricter than generic subject rules.

### Review gate

Confirm semantic parity and human-agency preservation before generic reconciliation is treated as authoritative for human subjects.

---

## Sprint 9 — Governed Reconciliation and Disclosure Separation

- ID: `NKS-SPR-009`
- Primary capability: reconcile internally; disclose separately

### Objective

Make reconciliation and disclosure distinct governed operations while preserving uncertainty, competing interpretations, audience boundaries, and user ownership of response.

### Scope

- Reconcile-and-record workflow.
- Conservative relationship strategy using recorded relationships only.
- Audience-aware disclose-and-record workflow for subject, internal, external-model, and public audiences.
- Attribution, confidence, context, temporal applicability, sensitivity, purpose, subject request, and authority evaluation.
- Immutable findings and disclosure receipts containing surfaced, deferred, and withheld sets.

### Exit criteria

- Reconciliation can occur without implying disclosure.
- Unknown confidence is deferred rather than erased or upgraded.
- Subject-facing disclosure requires subject request.
- External disclosure requires exact audience, subject, hash, context, transaction, and reserved authority.
- Findings remain attributable, contextual, reconstructable, and nonprescriptive.

### Review gate

Confirm that Enki identifies correspondence, divergence, uncertainty, and change without prescribing compulsory correction or silently widening disclosure.

---

## Sprint 10 — Governed Transition and Conflict Engine

- ID: `NKS-SPR-010`
- Primary capability: controlled change across knowledge states

### Objective

Implement the transactional transition engine for correction, refinement, supersession, retraction, context shift, confidence change, branching, merging, splitting, reversal, restriction, expansion, and deprecation.

### Scope

- Exact before-and-after state hashes.
- Subject, context, evidence, provenance, authority, execution context, interpretation version, transaction, and receipt binding.
- Conflict, contradiction, overlap, branch, merge, and competing-authority semantics.
- Recovery and deterministic forensic reconstruction.
- Human-state regression through the generic engine.

### Exit criteria

- Invalid, cyclic, contradictory, stale, context-mismatched, or unauthorized transitions fail closed.
- TEST transitions cannot mutate PRODUCTION state.
- Branch, merge, overlap, and authority conflicts are reconstructable.
- Interrupted transitions converge to one commit or one documented rollback.
- Human-specific controls remain intact through the generic engine.

### Review gate

Confirm that transition semantics preserve history and uncertainty rather than manufacturing a falsely singular truth.

---

## Sprint 11 — Governed Interpretation and Capability-Isolated Model Use

- ID: `NKS-SPR-011`
- Primary capability: controlled downstream model influence

### Objective

Separate interpretation resolution, package construction, purpose and privacy policy, approval, persistence, receipt creation, and dispatch into independently testable governed steps.

### Scope

- Deterministic authority-aware interpretation resolution.
- Typed model-use directives with explicit transition inclusion.
- Purpose limitation, audience scope, redaction, sensitivity, validity, expiration, and revocation.
- Canonical package hashing and immutable governed model-use receipts.
- TEST dispatcher technically incapable of transport, credentials, endpoints, callbacks, or adapter injection.
- PRODUCTION dispatcher requiring explicit production transport and PRODUCTION receipt.
- Provider effects and failures journaled.

### Exit criteria

- Retracted, expired, superseded, disputed, inapplicable, or unauthorized state cannot control downstream behavior.
- TEST package generation and recovery complete without external dispatch.
- Package tampering is rejected before transport invocation.
- PRODUCTION dispatch requires recognized authority, exact hashes, purpose, privacy filtering, and explicit transport.
- Prediction remains downstream and cannot mutate canonical knowledge state.

### Review gate

Confirm that downstream model influence is narrower than internal knowledge and that transport capability cannot be smuggled into TEST execution.

---

## Sprint 12 — Forensic Reconstruction, Portability, and Governed Work Completion

- ID: `NKS-SPR-012`
- Primary capability: reconstructable operations and evidence-bearing completion

### Objective

Prove that governed operations, approval consumption, migrations, state writes, disclosures, transitions, and model use can be reconstructed, moved, recovered, and completed without authority escalation or unsupported status claims.

### Scope

- Transaction reconstruction for all governed operation families.
- COMPLETE, INCOMPLETE, repairable, rollback, and CONFLICT classifications.
- Import, export, migration, replay, rollback, clean-room recovery, and disaster recovery.
- Approval-context preservation and TEST-to-PRODUCTION escalation prevention.
- Filesystem and GitHub adapter parity for supported operations.
- Governed work-control amendment transaction that binds sprint/work-item status changes to exact evidence.

### Exit criteria

- Every governed mutation and approval consumption is reconstructable from immutable evidence.
- Corrupt, stale, unsupported, cross-context, or privilege-escalating recovery fails closed.
- Clean-room recovery reproduces authoritative state and receipts.
- Adapter behavior is equivalent for the supported contract surface or differences are explicitly recorded.
- No sprint or work item can become complete without qualifying implementation evidence.

### Review gate

Confirm that the system can explain not only current state, but exactly how authority and evidence produced it.

---

## Sprint 13 — Integrated TEST Proof, Release Candidate, and External-Validation Handoff

- ID: `NKS-SPR-013`
- Primary capability: internally complete, reviewable release candidate

### Objective

Run repeated end-to-end TEST loops across subject classes, prove interruption recovery and authority isolation, package a versioned release candidate, and hand a production-ready execution package to the independently governed Sprint 3 external-validation lane.

### Scope

- At least two complete adaptive TEST loops across different subject classes.
- Generic state creation, reconciliation, disclosure decision, transition, interpretation, model-use package, receipt, and reconstruction.
- Chaos and interruption drills.
- Security and authority regression suite.
- Versioned release candidate, threat model, runbooks, rollback path, release notes, limitations, and explicit internal release decision.
- Production-readiness package identifying the exact approvals, transport, account configuration, content, visuals, receipts, and external actions still owned by Sprint 3.

### Exit criteria

- Two complete TEST loops pass without production effects or authority leakage.
- All journals and receipts reconstruct deterministically.
- Chaos drills recover without duplicate effects, partial authority, unexplained state, or context escalation.
- A versioned internal release candidate and rollback path exist.
- Known limitations and external dependencies are explicit.
- The Sprint 3 handoff package is complete, but Sprint 13 does not falsely claim public publication or REAL feedback.

### Review gate

Approve or reject the internal release candidate separately from production publication approval.

---

# Evidence Assessment Against Current Implementation

The open Enki core refactor contains substantial candidate evidence for Sprints 5–9, Sprint 11, and parts of Sprint 12. That implementation must be mapped to the revised sprint records rather than treated as one indivisible completion claim.

Initial assessment:

| Revised sprint | Candidate evidence state | Principal review question |
|---|---|---|
| Sprint 5 | substantial | Does approval and transaction behavior cover every claimed operation and fail-closed path? |
| Sprint 6 | substantial | Is the bounded cognitive-core contract constitutionally correct and dependency-clean? |
| Sprint 7 | substantial | Do generic state writes prove reuse without schema forks and with full integrity? |
| Sprint 8 | substantial | Does migration preserve human meaning, authority, and expression origin? |
| Sprint 9 | substantial | Are reconciliation and disclosure genuinely separate and audience-governed? |
| Sprint 10 | missing or incomplete | Is the full governed transition/conflict engine implemented and evidenced? |
| Sprint 11 | substantial but review required | Are privacy, purpose, dispatch isolation, recovery, and revocation complete? |
| Sprint 12 | partial | Are all operation families reconstructable, are adapters portable, and does governed work completion exist? |
| Sprint 13 | not yet evidenced | Have integrated loops, chaos proof, release artifacts, and the Sprint 3 handoff been executed? |

“Substantial” does not mean complete. Each sprint receives its own evidence review and completion transaction.

# Same-Day Execution Policy

The date target changes sequencing and batch size, not truth standards.

For each revised sprint:

1. isolate the exact implementation and tests that satisfy its scope;
2. identify gaps without reopening already proven work;
3. close the smallest remaining gap;
4. run the required validation;
5. attach immutable evidence;
6. execute the governed completion amendment;
7. continue immediately to the next sprint unless a genuine human or external-effect gate is reached.

A failed review narrows the remaining work. It does not collapse the entire roadmap into a blocker.

# Canonical Promotion Plan

After this proposal is reviewed and accepted:

1. preserve Sprints 1, 2, and 4 unchanged;
2. amend Sprint 3 to declare its parallel external-validation dependency model;
3. revise `NKS-SPR-005` through `NKS-SPR-011` to the accepted modular scopes;
4. create `NKS-SPR-012` and `NKS-SPR-013`;
5. revise or create corresponding backlog items;
6. regenerate canonical roadmap and backlog projections;
7. regenerate the repository audit;
8. run work-control, state-authority, canonicalization-security, coverage, CI, and publication-asset checks;
9. preserve this proposal as the historical rationale for the canonical revision.
