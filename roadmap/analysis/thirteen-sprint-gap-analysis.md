# Enki Roadmap Gap Analysis — Internal Validation with Mandatory Publication POC Lane

> **Authority class: Class 3 — implementation assessment.**
> This analysis supersedes prior versions of this file. It incorporates Enki as the deliverable, mandatory internal publication-shaped POC testing, and deferral of only the external production effect. It does not alter canonical status until promoted through governed work control.

- Assessment date: 2026-07-13
- Canonical branch: `sandbox`
- Canonical head: `8f98e92227b1568a812900d5904dc7c3f057ee24`
- Revised-plan branch: `roadmap/refactor-to-thirteen-sprints`
- Implementation branch: `agent/enki-core-refactor`
- Implementation head: `c29c0de4425e82d693e1c635d12a36e7f3b76097`
- Governing decisions:
  - `roadmap/decisions/automated-path-complete-testing-policy.md`
  - `roadmap/decisions/enki-deliverable-and-production-deferral.md`

## Executive correction

Enki is the deliverable. Enki is not a publication engine.

The first-live-publication proof of concept is nevertheless still tested completely before Enki release. It is one required production-shaped downstream-consumer lane within the internal validation model.

The correction is:

```text
DEFER
actual live publication and production audience evidence

RETAIN AND REQUIRE
complete internal publication-shaped execution through no-effect adapters
```

The prior analysis went too far by describing the publication POC as merely historical or optional future work. Its external effect is deferred. Its internal test obligations remain active and mandatory.

## Corrected execution topology

```text
HISTORICAL FOUNDATION
S1 Canonical identity
→ S2 Work-control plane
→ S4 Restricted canonical writer

ENKI CAPABILITY CONSTRUCTION
S5 Approval and transaction foundation
→ S6 Enki core boundary and contracts
→ S7 Governed generic state creation
→ S8 Human compatibility and governed migration
→ S9 Reconciliation and disclosure governance
→ S10 Transition and conflict engine
→ S11 Governed interpretation and model use
→ S12 Reconstruction, portability, and governed completion

INTEGRATED INTERNAL VALIDATION
S13
├─ complete publication-shaped POC lane using no-effect adapters
├─ complete at least one other adaptive lane
├─ execute full path matrix, rollback, recovery, reconstruction, and chaos proof
└─ produce versioned Enki release candidate

RELEASE
explicit Enki release decision

POST-ENKI DOWNSTREAM PRODUCTION
separate Media Blitz production authority and live publication
```

## What the internal publication POC must prove

Before Enki release, the publication lane must exercise:

- exact content body and visual manifest;
- production-shaped configuration, identity, byline, brand, and channel fixtures;
- review and exact-hash TEST approval;
- publication package construction;
- no-effect publication and distribution adapters;
- TEST publication and distribution receipts;
- simulated observation windows;
- `SYNTHETIC/TEST`, `REPLAY/TEST`, and controlled `REAL/TEST` feedback;
- feedback lineage, classification, routing, deduplication, disposition, and calibration;
- invalid input, denied authority, mismatch, expiry, revocation, stale state, duplicate, conflict, interruption, retry, rollback, recovery, tamper, replay, and privilege-escalation paths;
- deterministic reconstruction of the complete lane.

This proves that Enki can safely govern a downstream product workflow. It does not redefine Enki as that downstream product.

## What is actually deferred

The following are not required before Enki release:

- live publishing accounts and production credentials;
- reachable production transports, endpoints, or callbacks;
- actual external publication or distribution;
- real production audience observation;
- `REAL/PRODUCTION` publication feedback or production zero-feedback receipts;
- production post-publication calibration.

These become Media Blitz release requirements after Enki is live.

## Assessment model

Each Enki sprint is evaluated across:

1. **Design** — the capability and boundaries are defined.
2. **Implementation** — executable contracts, services, schemas, adapters, and receipts exist.
3. **Path automation** — every success, failure, interruption, retry, rollback, recovery, replay, tamper, and escalation path is tested.
4. **Evidence** — immutable proof is bound to the exact commit and sprint.
5. **Authority** — architecture, accepted limitations, completion, and release decisions remain explicit.

## Updated status matrix

| Sprint | Capability | Design | Implementation | Path automation | Evidence / authority | Assessment |
|---|---|---|---|---|---|---|
| S1 | Canonical identity and repository truth | resolved | complete | complete | accepted | COMPLETE |
| S2 | Canonical backlog and roadmap control plane | resolved | complete | complete | accepted | COMPLETE |
| S3 | Original publication POC | preserved and decomposed | internal obligations distributed into S5–S13; external effect deferred | mandatory internal lane incomplete | canonical decomposition decision pending | INTERNAL TEST OBLIGATION, NOT PRODUCTION GATE |
| S4 | Restricted canonical writer | resolved | complete | complete for accepted scope | accepted | COMPLETE |
| S5 | Context-bound approval and transaction foundation | resolved | partial | incomplete | unmapped | PARTIAL |
| S6 | Enki cognitive-core boundary and generic contracts | resolved | strong | mostly present | architecture acceptance and evidence mapping pending | READY FOR COMPLETION REVIEW |
| S7 | Governed generic state write | resolved | partial | incomplete | unmapped | PARTIAL |
| S8 | Human compatibility and governed migration | resolved | partial | incomplete | human-policy decisions and evidence mapping pending | PARTIAL |
| S9 | Governed reconciliation and disclosure | resolved | partial | incomplete | per-operation authority and evidence mapping pending | PARTIAL |
| S10 | Governed transition and conflict engine | resolved | missing | absent | absent | IMPLEMENTATION MISSING |
| S11 | Governed interpretation and capability-isolated model use | resolved | strong but incomplete | partial | unmapped | PARTIAL |
| S12 | Reconstruction, portability, and governed completion | resolved | partial | incomplete | unmapped | PARTIAL |
| S13 | Integrated internal TEST proof and Enki release candidate | resolved | missing as integrated subsystem | publication POC and additional lane not yet executed | controlled REAL/TEST evaluation and release decision pending | IMPLEMENTATION MISSING |

## Governance and integration gaps

### G-1 — Corrected roadmap is not canonical

The live canonical roadmap still has eleven sprints and treats the first publication cycle as blocked production work inside the core sequence.

Closure requires:

1. record approval of the corrected roadmap;
2. preserve S1, S2, and S4 unchanged;
3. decompose Sprint 3 without erasing its history;
4. distribute its mandatory internal TEST obligations across S5–S13;
5. transfer only its external production effect to a downstream Media Blitz backlog;
6. create or update canonical S5–S13 and backlog records;
7. incorporate automated path-complete internal TEST criteria;
8. regenerate roadmap, backlog, authority manifest, and repository audit;
9. run all required workflows.

### G-2 — PR #27 must be reconciled with current `sandbox`

PR #27 is 98 commits ahead and 3 commits behind current `sandbox`. The branches must be reconciled without losing Publication 000001 artifacts, because they remain active internal validation fixtures.

### G-3 — Evidence must come from executable records

PR #27 contains strong candidate implementation, but narrative claims must be validated against source files, schemas, tests, journals, receipts, workflow artifacts, and generated audit outputs.

### G-4 — Path catalogs and coverage enforcement are incomplete

Every governed operation and integrated consumer lane requires a machine-readable path manifest containing:

- operation and path identifiers;
- fixture and input hashes;
- authority and context fixtures;
- expected terminal state;
- expected and prohibited records;
- rollback, compensation, discard, or recovery route;
- observed terminal state;
- immutable evidence reference.

Coverage must fail when a declared path is not executable.

## Sprint-specific gaps

### Sprint 5 — Approval and transaction foundation

Present:

- TEST and PRODUCTION contexts;
- exact approval binding;
- reservation, consumption, revocation, release, and exact retry;
- durable compare-and-swap persistence;
- model-use-specific journaling and recovery.

Missing:

- reusable governed-operation transaction state machine;
- shared operation plan and hash contract;
- common journal and receipt model;
- failure injection at every boundary;
- rollback and recovery proof for every state-changing path;
- cross-context replay and privilege-escalation matrix;
- path-coverage enforcement.

Assessment: **PARTIAL**.

### Sprint 6 — Enki core boundary and contracts

Present:

- ADR-0002;
- generic subject, evidence, observation, relationship, temporal, confidence, finding, disclosure, request, and result contracts;
- product-neutral ports;
- objective and priority substitution rejection;
- dependency and constitutional tests.

Remaining:

- human acceptance or revision of ADR-0002;
- explicit schema and contract-version rules;
- forward, backward, unsupported, and ambiguous compatibility tests;
- final confidence-assertion contract decision;
- evidence manifest and governed completion transaction.

Assessment: **READY FOR COMPLETION REVIEW**.

### Sprint 7 — Governed generic state creation

Present:

- shared collections and contracts for PERSON, ORGANIZATION, and PROJECT;
- append-only repository;
- idempotent writes and conflict rejection.

Missing:

- content-addressed state-write plan;
- exact preflight and known-reference validation;
- approval-bound executor;
- multi-record journal and immutable receipt;
- partial-write recovery and reconstruction;
- complete automated subject-class and failure-path matrix.

Assessment: **PARTIAL**.

### Sprint 8 — Human compatibility and governed migration

Present:

- compatibility adapter outside Enki core;
- explicit expression-origin choice;
- legacy Boolean approval excluded from generic authority;
- legacy transition projection.

Missing:

- content-addressed migration plan and executor;
- migration journal and receipt;
- privacy, consent, purpose, redaction, correction, retraction, expiry, and revocation policy layer;
- semantic-parity fixtures;
- complete interruption, rollback, recovery, duplicate, and tamper matrix.

Assessment: **PARTIAL**.

### Sprint 9 — Reconciliation and disclosure governance

Present:

- reconciliation and disclosure separated;
- findings retain lineage;
- unknown confidence deferred;
- subject request and external approval checks;
- disclosure receipts.

Missing:

- deterministic temporal and context eligibility resolver;
- enforceable privacy, consent, purpose, sensitivity, and redaction contracts;
- transactional reconcile-and-record and disclose-and-record workflows;
- approval lifecycle, journals, receipts, rollback, retry, and recovery owned by each operation;
- competing-interpretation and revocation propagation;
- complete automated path graph.

Assessment: **PARTIAL**.

### Sprint 10 — Transition and conflict engine

Missing primary capability:

- generic versioned transition contracts and schemas;
- exact before-and-after hashes;
- correction, refinement, supersession, retraction, reversal, expansion, restriction, confidence change, branch, merge, split, and deprecation;
- conflict, contradiction, overlap, cycle, stale-input, and authority-conflict semantics;
- approval-bound executor;
- journal, receipt, rollback, retry, and reconstruction;
- path-complete automation.

Assessment: **IMPLEMENTATION MISSING**.

### Sprint 11 — Governed interpretation and model use

Present:

- separated interpretation, package construction, policy, authority, receipt, persistence, and dispatch;
- deterministic hashing;
- exact-retry recovery;
- transport-incapable TEST dispatcher;
- production dispatcher requiring explicit transport;
- tamper rejection and provider journaling.

Missing:

- Enki-native generic packages;
- typed, attributable, purpose-bound directives;
- item-level privacy, consent, sensitivity, purpose, and redaction filtering;
- explicit package-context matching;
- governed revocation and downstream-effect receipts;
- Sprint 10 transition integration;
- full automated privacy, failure, rollback, and recovery matrix;
- no-effect publication-package and distribution-path integration.

Assessment: **PARTIAL, STRONG SUBSTRATE**.

### Sprint 12 — Reconstruction, portability, and governed completion

Present:

- model-use journaling and reconstruction;
- durable approval persistence;
- audit and state-authority registration;
- evidence-required COMPLETE status.

Missing:

- common reconstruction interface and terminal-state taxonomy;
- reconstruction across every operation family;
- reconstruction of the full publication-shaped POC lane;
- clean-room and disaster-recovery exercises;
- import and export preserving authority and lineage;
- filesystem and GitHub adapter parity;
- approval-bound reconstructable work-control amendment;
- cross-operation replay, rollback, import, and escalation matrix.

Assessment: **PARTIAL**.

### Sprint 13 — Integrated internal TEST proof and Enki release candidate

Design and test authority are resolved.

Missing:

- complete cross-operation path manifest;
- complete internal publication-shaped POC lane through no-effect adapters;
- at least one additional adaptive lane across a different subject or product context;
- feedback provenance and execution-context contracts;
- feedback schemas, services, receipts, classification, routing, deduplication, disposition, and promotion control;
- synthetic scenario corpus;
- replay harness;
- controlled REAL/TEST human interface;
- simulated observation-window and zero-feedback handling;
- chaos and interruption campaign;
- path-coverage enforcement;
- deterministic reconstruction of both integrated lanes;
- hash-bound internal calibration report;
- versioned Enki release candidate, threat model, runbooks, rollback package, release notes, limitations, and explicit release decision.

No live external publication is required for Sprint 13 completion. Complete internal publication-shaped testing is required.

Assessment: **IMPLEMENTATION MISSING, DESIGN AND TEST AUTHORITY RESOLVED**.

## Consolidated work packages

### Package A — Shared transaction and path engine

Closes central gaps across S5, S7, S8, S9, S10, S12, and S13.

### Package B — Generic transition and conflict engine

Closes S10 and enables final integration in S11–S13.

### Package C — Internal feedback, calibration, and integrated validation subsystem

Closes S13 by executing the publication POC and at least one additional adaptive lane internally.

### Package D — Canonical promotion and branch integration

Makes the corrected roadmap governable and reconciles PR #27 with current `sandbox`.

## Updated critical path

```text
approve and promote corrected Enki roadmap
→ reconcile PR #27 with current sandbox
→ complete shared transaction and path engine
→ finish Sprint 6 review and evidence mapping
→ implement and prove S7 state creation
→ implement and prove S8 human migration
→ implement and prove S9 reconciliation and disclosure
→ implement S10 transition/conflict engine
→ finish S11 privacy-governed model use and no-effect downstream packaging
→ finish S12 reconstruction and governed completion
→ execute S13 publication POC lane + second adaptive lane + full path matrix + REAL/TEST + chaos + calibration
→ explicit Enki release decision
```

## Final finding

The publication proof of concept remains fully tested.

What is removed is only the requirement to perform the real external publication before Enki itself is proven and released. The remaining blockers are bounded and under direct control: governed operations, automated path coverage, rollback and reconstruction proof, integrated consumer-lane execution, evidence binding, and canonical completion.
