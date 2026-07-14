# Thirteen-Sprint Gap Analysis — Path-Complete Testing Update

> **Authority class: Class 3 — implementation assessment.**
> This analysis supersedes prior versions of this file. It incorporates the approved automated TEST policy and separates design, implementation, automated path coverage, evidence, and irreducible production authority. It does not change canonical sprint status or authorize production.

- Assessment date: 2026-07-13
- Canonical branch: `sandbox`
- Canonical head: `8f98e92227b1568a812900d5904dc7c3f057ee24`
- Revised-plan branch: `roadmap/refactor-to-thirteen-sprints`
- Revised-plan head assessed: `f01e024f6173a7446a71dcc40f519a42881b769d`
- Implementation branch: `agent/enki-core-refactor`
- Implementation head: `c29c0de4425e82d693e1c635d12a36e7f3b76097`
- Implementation PR: `#27`
- Roadmap PR: `#28`
- Governing test policy: `roadmap/decisions/automated-path-complete-testing-policy.md`

## Executive conclusion

The remaining gaps are no longer framed as permission to test.

Automated TEST execution is approved when a path is:

- TEST-scoped;
- technically incapable of reaching an unapproved production effect;
- machine-declared with an expected outcome;
- automated and auditable;
- idempotent; and
- protected by rollback, compensation, isolated discard, or exact recovery.

A separate human approval is not required for each automated TEST case. Human authority remains required for constitutional architecture decisions, accepted limitations, evidence-bearing canonical completion, and actual production effects.

The revised gap is therefore:

```text
implement the governed operation
→ declare every path
→ automate every path
→ prove rollback or exact recovery
→ bind immutable evidence to the exact commit
→ execute governed completion
```

The repository contains a substantial Enki-core substrate, but it does not yet contain enough implementation and path-complete evidence to mark Sprints 5–13 complete.

Current condition:

- Sprints 1, 2, and 4 are canonically complete.
- Sprint 3 is a production boundary, not a testing blocker.
- Sprint 5 has strong approval primitives but lacks the reusable path-complete transaction kernel.
- Sprint 6 is ready for completion review.
- Sprints 7–9 have valid component foundations but lack complete governed operations and automated path graphs.
- Sprint 10's transition/conflict engine is not implemented.
- Sprint 11 has a strong model-use and dispatch substrate but remains human-state-specific and incomplete in privacy, typed directives, revocation, and transition integration.
- Sprint 12 lacks system-wide reconstruction, adapter parity, and governed work completion.
- Sprint 13's testing design and authority are resolved, but its integrated feedback, chaos, calibration, and release execution is not implemented.
- PR #27 passes the six required workflows, but is 98 commits ahead of and 3 commits behind current `sandbox`; integration remains a distinct gap.

## Assessment model

Each sprint is evaluated independently across five dimensions:

1. **Design** — the operation and boundaries are sufficiently specified.
2. **Implementation** — executable contracts, services, schemas, adapters, and receipts exist.
3. **Path automation** — every success, denial, failure, interruption, retry, rollback, recovery, replay, and escalation path is executable and tested.
4. **Evidence** — immutable proof is mapped to the exact sprint and commit.
5. **Authority / effect** — any irreducible architecture decision, accepted limitation, canonical completion decision, or production effect remains explicit.

Status vocabulary:

- `COMPLETE` — canonical and evidence-bearing.
- `READY FOR COMPLETION REVIEW` — implementation is materially sufficient; final path coverage, evidence mapping, or governing review remains.
- `PARTIAL` — useful implementation exists, but one or more primary operation or path-complete requirements remain.
- `IMPLEMENTATION MISSING` — design and test authority exist, but the primary executable capability does not.
- `PRODUCTION BOUNDARY PENDING` — TEST proof is owned elsewhere; only final authority, external effect, or production evidence remains.

## Updated matrix

| Sprint | Capability | Design | Implementation | Path automation | Evidence / authority | Assessment |
|---|---|---|---|---|---|---|
| 1 | Canonical identity and repository truth | resolved | complete | complete | accepted | COMPLETE |
| 2 | Canonical backlog and roadmap control plane | resolved | complete | complete | accepted | COMPLETE |
| 3 | Controlled production publication and post-release calibration | resolved | TEST mechanics assigned to Sprint 13 | production-shaped paths must be proven in Sprint 13 | final human authority and external evidence pending | PRODUCTION BOUNDARY PENDING |
| 4 | Restricted canonical writer | resolved | complete | complete for accepted scope | accepted | COMPLETE |
| 5 | Context-bound approval and transaction foundation | resolved | partial | incomplete | unmapped | PARTIAL |
| 6 | Enki cognitive-core boundary and generic contracts | resolved | strong | mostly present; versioning paths remain | architecture acceptance and evidence mapping pending | READY FOR COMPLETION REVIEW |
| 7 | Generic observation, relationship, and governed state write | resolved | partial | incomplete | unmapped | PARTIAL |
| 8 | Human-state compatibility, authority, and governed migration | resolved | partial | incomplete | human-policy decisions and evidence mapping pending | PARTIAL |
| 9 | Governed reconciliation and disclosure separation | resolved | partial | incomplete | per-operation disclosure authority and evidence mapping pending | PARTIAL |
| 10 | Governed transition and conflict engine | resolved | missing | absent | absent | IMPLEMENTATION MISSING |
| 11 | Governed interpretation and capability-isolated model use | resolved | strong but incomplete | partial | unmapped | PARTIAL |
| 12 | Forensic reconstruction, portability, and governed work completion | resolved | partial | incomplete | unmapped | PARTIAL |
| 13 | Integrated TEST proof, feedback validation, and release candidate | resolved | missing as an integrated subsystem | absent as one complete matrix | controlled human TEST evidence and release decision pending | IMPLEMENTATION MISSING |

---

# Governance and integration gaps

## G-1 — Revised roadmap is not canonical

The live generated roadmap still contains eleven sprints, retains obsolete Sprint 3 wording, and does not contain canonical Sprint 12 or Sprint 13 records.

### Closure

1. Record the roadmap decision on PR #28.
2. Promote revised Sprint 3 and Sprint 5–13 definitions through governed work control.
3. Create canonical sprint and backlog records for Sprints 12 and 13.
4. Incorporate the automated path-complete testing policy into sprint exit criteria.
5. Regenerate roadmap, backlog, authority manifests, and audit.
6. Run the full validation suite.

## G-2 — PR #27 must be reconciled with current `sandbox`

PR #27 is 98 commits ahead and 3 commits behind `sandbox`. The missing base commits contain Sprint 3 decomposition, the article body, and publication configuration.

### Closure

- bring the implementation branch forward to current `sandbox`, or merge through a path that explicitly preserves the newer base commits;
- rerun all workflows after reconciliation;
- verify generated audit and authority manifests;
- map the reconciled implementation to the revised sprint boundaries.

## G-3 — PR prose is broader than executable evidence

PR #27 describes governed state-write plans, migration transactions and receipts, and broad forensic reconstruction. The live file set demonstrates strong approval, Enki core, generic storage, compatibility projection, reconciliation/disclosure separation, and model-use execution. It does not show the full dedicated state-write executor, governed migration executor, generic transition engine, system-wide work-control amendment, or integrated feedback subsystem required by the revised roadmap.

### Governing rule

Completion evidence comes from executable contracts, schemas, tests, workflow artifacts, receipts, and generated reports. PR narrative is a claim to validate.

## G-4 — Path catalogs and coverage enforcement do not yet exist across operation families

The new policy requires each operation to have a machine-readable path graph and a suite that fails when a declared path lacks coverage.

### Closure

Create a shared path-manifest contract containing:

- operation identifier;
- path identifier;
- preconditions and fixture hashes;
- authority fixture and execution context;
- expected terminal state;
- expected and prohibited records;
- rollback, compensation, discard, or recovery route;
- observed terminal state;
- immutable test evidence reference.

---

# Sprint-by-sprint updated gaps

## Sprint 3 — Controlled Production Publication and Post-Release Calibration

### Design and testing status

Resolved. Sprint 13 must test the complete production-shaped mechanism before production:

- review workflow and exact-hash binding;
- configuration rehearsal;
- TEST approval lifecycle;
- no-effect publication rehearsal;
- receipt creation;
- observation-window and zero-feedback handling;
- feedback ingestion and disposition;
- synthetic, replay, and controlled real-human TEST evidence;
- pre-production calibration.

### What remains native to Sprint 3

- final human decisions on exact content, visuals, identity, channels, and limitations;
- exact PRODUCTION approval;
- actual publication and distribution;
- real observation-window passage;
- `REAL/PRODUCTION` feedback or a production zero-feedback receipt;
- post-release calibration.

### Assessment

**PRODUCTION BOUNDARY PENDING.** No new testing design is needed.

---

## Sprint 5 — Context-Bound Approval and Transaction Foundation

### Present

- TEST and PRODUCTION contexts;
- exact approval binding across action, subject, content hash, authority class, validity, revocation, and transaction;
- AVAILABLE, RESERVED, CONSUMED, and REVOKED states;
- compare-and-swap persistence;
- reservation release;
- exact retry;
- model-use-specific journaling and recovery.

### Missing implementation

- reusable governed-operation transaction state machine;
- shared operation plan and plan-hash contract;
- common journal stages and final transaction receipt;
- integration with canonical promotion and restricted writing;
- common reconstruction result taxonomy.

### Missing automated paths

- every authority mismatch and denial;
- interruption before reservation, after reservation, after consumption, during persistence, and before receipt;
- conflict after preflight;
- duplicate request and competing transaction;
- rollback, compensation, and exact recovery;
- import, replay, rollback, and cross-context escalation attempts;
- coverage enforcement for undeclared or untested terminal paths.

### Why partial

Approval primitives are implemented. The shared automated transaction kernel is not.

---

## Sprint 6 — Enki Cognitive-Core Boundary and Generic Contracts

### Present

- ADR-0002 Enki boundary;
- generic subject, evidence, observation, relationship, temporal, confidence, finding, disclosure, request, and result contracts;
- product-neutral ports;
- scope and traceability validation;
- hidden objective and priority substitution rejection;
- uncertainty preservation;
- dependency and constitutional traceability tests.

### Remaining

- human acceptance or revision of ADR-0002;
- explicit schema and contract-version evolution rules;
- automated forward, backward, unsupported, and ambiguous version paths;
- final confidence-assertion contract decision and resulting tests;
- sprint evidence manifest and governed completion transaction.

### Why ready for review

The primary capability exists. Remaining work is bounded architectural acceptance, compatibility-path coverage, and evidence promotion.

---

## Sprint 7 — Generic Observation, Relationship, and Governed State Write

### Present

- shared contracts and collections for PERSON, ORGANIZATION, and PROJECT;
- append-only generic repository;
- idempotent identical writes and conflicting-write rejection;
- shared reconciliation without subject-specific schema forks.

### Missing implementation

- content-addressed `StateWritePlan`;
- known-reference, subject, domain, and context preflight;
- approval-bound executor;
- multi-record journal and immutable receipt;
- partial-write recovery and reconstruction.

### Missing automated paths

- valid write;
- invalid and stale references;
- duplicate and conflicting writes;
- interruption at every write stage;
- authority consumed before incomplete write;
- receipt loss and receipt conflict;
- tampering;
- rollback or exact recovery;
- cross-transaction replay;
- PERSON, ORGANIZATION, and PROJECT matrix.

### Why partial

Storage behavior is proven. Governed state creation and its full path graph are not.

---

## Sprint 8 — Human-State Compatibility, Authority, and Governed Migration

### Present

- compatibility adapter outside Enki core;
- explicit expression-origin selection;
- exclusion of legacy Boolean model-feedback approval from generic authority;
- legacy transition projection to generic relationships.

### Missing implementation

- content-addressed migration plan;
- approval-bound migration executor;
- migration journal and receipt;
- human protection policy layer for privacy, consent, purpose, redaction, correction, retraction, expiry, and revocation;
- semantic-parity fixtures across all temporal states.

### Missing automated paths

- every expression-origin choice;
- privacy and consent allow and deny states;
- purpose mismatch;
- correction, retraction, expiry, and revocation;
- duplicate migration and semantic mismatch;
- interruption before and after authority consumption and during writes;
- rollback, compensation, and exact recovery;
- migration receipt conflict and tampering.

### Why partial

Projection is implemented. Governed, rollback-capable migration is not.

---

## Sprint 9 — Governed Reconciliation and Disclosure Separation

### Present

- reconciliation and disclosure are separate operations;
- findings retain observation, relationship, evidence, objective, priority, and interpretation lineage;
- unknown confidence is deferred;
- subject disclosure requires subject request;
- external disclosure checks bound approval;
- receipts distinguish surfaced, deferred, and withheld findings.

### Missing implementation

- deterministic temporal and context eligibility resolver;
- sensitivity, privacy, consent, purpose, and redaction contracts;
- transactional reconcile-and-record workflow;
- transactional disclose-and-record workflow with authority reserve, consume, release, retry, and recovery;
- journaled finding persistence and reconciliation receipt;
- competing-interpretation and revocation propagation model.

### Missing automated paths

- applicable, future, expired, retracted, superseded, disputed, and context-inapplicable inputs;
- uncertainty and competing interpretations;
- subject-requested and nonrequested disclosure;
- privacy denial and redaction;
- external approval success, absence, mismatch, expiry, revocation, and competing reservation;
- duplicate disclosure, receipt conflict, interruption, rollback, and recovery.

### Why partial

The conceptual separation exists. The complete governed operation graph and automated proof do not.

---

## Sprint 10 — Governed Transition and Conflict Engine

### Missing primary implementation

- versioned generic transition contracts and schemas;
- exact before-and-after state hashes;
- correction, refinement, supersession, retraction, reversal, expansion, restriction, confidence change, merge, split, and deprecation;
- branch, merge, overlap, contradiction, and authority-conflict semantics;
- cycle and stale-input detection;
- approval-bound executor;
- journal, receipt, rollback, exact retry, and reconstruction;
- human-overlay regression.

### Required path automation

Every transition type, conflict type, cycle, stale input, authority failure, interruption, branch, merge, split, rollback, and retry path.

### Assessment

**IMPLEMENTATION MISSING.** This remains the largest single domain gap.

---

## Sprint 11 — Governed Interpretation and Capability-Isolated Model Use

### Present

- interpretation, package construction, policy evaluation, authority, receipt, persistence, and dispatch separated;
- deterministic package hashing;
- reserve and consume before persistence;
- exact-retry recovery;
- TEST dispatcher without transport capability;
- PRODUCTION dispatcher requiring explicit transport and PRODUCTION receipt;
- package-tamper rejection;
- provider-effect and failure journaling.

### Missing

- Enki-native generic packages;
- typed, attributable, purpose-bound directives;
- item-level privacy, consent, sensitivity, purpose, and redaction filtering;
- explicit package/context matching;
- governed revocation and downstream-effect receipts;
- Sprint 10 transition integration;
- path-complete provider-failure, revocation, privacy, rollback, and recovery matrix.

### Assessment

**PARTIAL, WITH STRONG SUBSTRATE.**

---

## Sprint 12 — Forensic Reconstruction, Portability, and Governed Work Completion

### Present

- model-use journaling and reconstruction;
- durable approval persistence and exact-retry evidence;
- audit and state-authority registration;
- schema rule requiring evidence before COMPLETE status.

### Missing

- common reconstruction interface and COMPLETE, INCOMPLETE, REPAIRABLE, ROLLED_BACK, and CONFLICT taxonomy;
- reconstruction across state write, migration, reconciliation, disclosure, transition, feedback, promotion, and work-control amendment;
- clean-room and disaster-recovery exercises;
- import/export package preserving authority and lineage;
- filesystem and GitHub adapter parity for the declared contract;
- approval-bound, journaled, reconstructable work-control amendment;
- cross-operation path matrix for replay, rollback, import, and privilege escalation.

### Assessment

**PARTIAL.**

---

## Sprint 13 — Integrated TEST Proof, Feedback Validation, and Release Candidate

### Design and test authority

Resolved. The policy authorizes the complete automated TEST matrix, including rollback-capable state changes, synthetic feedback, replay, and controlled real-human TEST evidence.

### Missing implementation

- feedback provenance and execution-context contracts;
- feedback schemas, repositories, receipts, and services;
- publication-lineage validation;
- classification, routing, deduplication, disposition, and promotion control;
- synthetic scenario corpus and expected outcomes;
- replay harness;
- controlled human TEST interface;
- observation-window and zero-feedback TEST proof;
- two complete adaptive loops across different subject classes;
- cross-operation chaos campaign;
- path-coverage enforcement;
- hash-bound pre-production calibration report;
- versioned release candidate, threat model, runbooks, rollback path, release notes, limitations, internal release decision, and Sprint 3 handoff.

### Assessment

**IMPLEMENTATION MISSING, DESIGN AND TEST AUTHORITY RESOLVED.**

---

# Consolidated work packages

## Package A — Shared governed transaction and path engine

Closes the central execution gaps in Sprints 5, 7, 8, 9, 10, 12, and 13:

- plan and hash;
- path manifest;
- authority reservation and consumption;
- journal and receipt;
- failure injection;
- rollback, compensation, discard, and exact recovery;
- reconstruction;
- path-coverage enforcement.

## Package B — Generic transition and conflict engine

Closes Sprint 10 and enables final integration for Sprints 11–13.

## Package C — Governed feedback and calibration subsystem

Closes Sprint 13 and supplies the tested handoff to Sprint 3.

## Package D — Canonical promotion and branch integration

- approve PR #28;
- promote revised roadmap and testing policy;
- reconcile PR #27 with current `sandbox`;
- map evidence to revised sprint boundaries;
- execute governed completion amendments.

# Updated critical path

```text
approve PR #28 and promote the revised roadmap
→ reconcile PR #27 with current sandbox
→ complete shared transaction and path engine
→ finish Sprint 6 review and evidence mapping
→ implement and prove Sprint 7 state writes
→ implement and prove Sprint 8 migration
→ implement and prove Sprint 9 governed reconciliation/disclosure
→ implement Sprint 10 transition/conflict engine
→ finish Sprint 11 generic privacy-governed model use
→ finish Sprint 12 reconstruction and work-control amendment
→ execute Sprint 13 complete automated path matrix, human TEST evaluation, chaos, calibration, and release proof
→ hand the exact release candidate to Sprint 3
→ obtain final PRODUCTION authority and cause the external effect
```

## Parallel work now authorized

- Sprint 5 transaction path catalog and failure-injection harness;
- Sprint 6 architecture review and versioning tests;
- Sprint 7 state-write plan and test matrix;
- Sprint 8 migration plan, human-policy rules, and fixture matrix;
- Sprint 9 temporal/privacy contracts and disclosure path matrix;
- Sprint 13 feedback contracts, scenario corpus, replay design, and release-document skeletons;
- Sprint 3 editorial, visual, identity, channel, configuration, and no-effect publication rehearsal.

# Final updated finding

Testing approval is no longer a gap.

The remaining work is executable and measurable:

1. build each missing governed operation;
2. declare every path;
3. automate every path;
4. prove rollback, compensation, discard, or exact recovery for every state-changing path;
5. prevent every TEST path from reaching production;
6. bind immutable evidence to the exact commit;
7. complete each sprint through governed work control.

Sprint 6 is ready for review. Sprints 5, 7, 8, and 9 remain partial because their complete governed operation graphs and automated rollback-capable path coverage do not yet exist. Sprint 10 and Sprint 13 remain implementation-missing, with their design and TEST authority resolved.