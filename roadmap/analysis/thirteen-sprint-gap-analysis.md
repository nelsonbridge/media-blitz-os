# Thirteen-Sprint Gap Analysis — Rerun

> **Authority class: Class 3 — implementation assessment.**
> This rerun supersedes the earlier analysis in this file. It separates design gaps, implementation gaps, evidence gaps, and irreducible authority or external-effect boundaries. It does not change canonical sprint status or authorize production.

- Assessment date: 2026-07-13
- Canonical branch: `sandbox`
- Canonical branch head: `8f98e92227b1568a812900d5904dc7c3f057ee24`
- Revised-plan branch: `roadmap/refactor-to-thirteen-sprints`
- Revised-plan head: `77d79f2b54b7d6cc9cd7141ea9ae97283bc84eb6`
- Implementation branch: `agent/enki-core-refactor`
- Implementation head: `c29c0de4425e82d693e1c635d12a36e7f3b76097`
- Implementation PR: `#27`
- Roadmap PR: `#28`

## Executive conclusion

The prior gap analysis conflated two different conditions in Sprint 3:

1. whether review, configuration, approval, publication, observation, feedback, and calibration mechanisms can be tested before production; and
2. whether the final human authority, external effect, and production evidence have occurred.

That conflation is corrected.

The architecture for pre-production testing is already resolved in the revised roadmap. Sprint 13 owns complete TEST proof using `SYNTHETIC/TEST`, `REPLAY/TEST`, and controlled `REAL/TEST`. Sprint 3 owns only the irreducible production transaction: final human authority, external publication, the real observation window, and production evidence.

The current repository therefore has **no unresolved conceptual paradox around pre-production testing**. It has a finite implementation backlog.

Current state:

- Sprints 1, 2, and 4 are canonically complete.
- The revised thirteen-sprint roadmap is not yet canonical.
- Sprint 3 pre-production mechanics are designed but not yet implemented end to end; that implementation belongs primarily to Sprint 13.
- Sprint 3 production authority and external effects are intentionally pending and are not implementation defects.
- PR #27 contains a strong Enki-core substrate and passes all six required workflows.
- PR #27 is 98 commits ahead of and 3 commits behind current `sandbox`; branch integration must be reconciled before promotion or merge.
- Sprint 6 is functionally ready for completion review after roadmap promotion and branch reconciliation.
- Sprints 5, 7, 8, 9, 11, and 12 have material partial implementation.
- Sprint 10's generic transition/conflict engine is not implemented.
- Sprint 13's feedback-validation, integrated-loop, chaos, calibration, and release-candidate execution is not implemented, although its design is resolved.

Passing CI establishes regression health. It does not by itself establish revised sprint completion.

## Assessment dimensions

This rerun uses four independent dimensions:

- **Design** — whether the capability and boundaries are sufficiently specified to build.
- **Implementation** — whether executable code, schemas, adapters, and tests exist.
- **Evidence** — whether exact implementation evidence is mapped to the revised sprint and accepted through governed work control.
- **Authority / effect** — whether an irreducible human decision or external production event is still required.

Status terms:

- `COMPLETE` — already canonical and evidence-bearing.
- `READY FOR COMPLETION REVIEW` — implementation appears sufficient; evidence mapping and governing review remain.
- `PARTIAL` — useful implementation exists, but material exit criteria remain unimplemented.
- `IMPLEMENTATION MISSING` — design exists, but the primary executable capability does not.
- `PRODUCTION BOUNDARY PENDING` — no implementation defect; final authority or external evidence has not yet occurred.

## Rerun matrix

| Sprint | Capability | Design | Implementation | Evidence | Authority / effect | Rerun assessment |
|---|---|---|---|---|---|---|
| 1 | Canonical identity and repository truth | resolved | complete | accepted | none | COMPLETE |
| 2 | Canonical backlog and roadmap control plane | resolved | complete | accepted | none | COMPLETE |
| 3 | Controlled production publication and post-release calibration | resolved | pre-production mechanics assigned to Sprint 13 | production evidence not yet possible | final human authority and external effect pending | PRODUCTION BOUNDARY PENDING |
| 4 | Restricted canonical writer | resolved | complete | accepted | none | COMPLETE |
| 5 | Context-bound approval and transaction foundation | resolved | partial | unmapped | none | PARTIAL |
| 6 | Enki cognitive-core boundary and generic contracts | resolved | strong | mappable but unaccepted | architecture decision pending | READY FOR COMPLETION REVIEW |
| 7 | Generic observation, relationship, and governed state write | resolved | partial | unmapped | none | PARTIAL |
| 8 | Human-state compatibility, authority, and governed migration | resolved | partial | unmapped | human-policy decisions may be needed | PARTIAL |
| 9 | Governed reconciliation and disclosure separation | resolved | partial | unmapped | disclosure authority applies per operation | PARTIAL |
| 10 | Governed transition and conflict engine | resolved | missing | absent | none | IMPLEMENTATION MISSING |
| 11 | Governed interpretation and capability-isolated model use | resolved | strong but incomplete | unmapped | production transport remains separate | PARTIAL |
| 12 | Forensic reconstruction, portability, and governed work completion | resolved | partial | unmapped | none | PARTIAL |
| 13 | Integrated TEST proof, pre-production feedback validation, and release candidate | resolved | missing as an integrated subsystem | absent | controlled human TEST evaluator required | IMPLEMENTATION MISSING |

---

# Governance and integration gaps

## G-1 — Revised roadmap is not canonical

The live generated roadmap still contains eleven sprints. It still describes Sprint 3 as requiring real feedback as a mandatory occurrence, retains the prior scopes for Sprints 5–11, and has no Sprint 12 or Sprint 13 records.

### Closure required

1. Record the human roadmap decision on PR #28.
2. Promote the accepted Sprint 3 and Sprint 5–13 definitions through governed work control.
3. Create canonical sprint and backlog records for Sprints 12 and 13.
4. Regenerate roadmap, backlog, authority manifests, and repository audit.
5. Run all authority, security, CI, coverage, and publication checks.

No revised sprint should be marked complete against a roadmap that has not yet been canonically adopted.

## G-2 — PR #27 is behind current `sandbox`

The implementation branch is 98 commits ahead of but 3 commits behind `sandbox`. The missing base commits contain the Sprint 3 dependency decomposition, article draft, and publication configuration worksheet.

### Closure required

- Bring `agent/enki-core-refactor` forward to current `sandbox`, or merge it through a path that explicitly preserves the three newer base commits.
- Re-run the full workflow set against the reconciled branch.
- Verify generated audit and authority manifests after integration.

The branch is currently reported mergeable, but mergeability is not evidence that the later base-state changes have been semantically reconciled.

## G-3 — PR narrative exceeds executable evidence

PR #27 describes generic state-write plans, governed migration transactions, migration receipts, and broad forensic reconstruction. The actual changed-file set contains generic repositories, compatibility projection, model-use journaling, and model-use reconstruction, but not dedicated generic state-write executors, migration executors, migration receipt schemas, a generic transition engine, or governed work-control amendment execution.

### Governing rule

Use source files, schemas, tests, immutable receipts, workflow runs, and generated reports as evidence. Treat PR descriptions as claims requiring verification.

## G-4 — Evidence is not mapped to revised sprint boundaries

PR #27 spans several revised sprints. Completion must be assessed capability by capability.

Each sprint requires an evidence manifest binding:

- exact commit;
- relevant source files and schemas;
- tests and expected failure paths;
- workflow run identifiers and artifacts;
- generated audit state;
- known limitations;
- governing review decision.

---

# Sprint-by-sprint rerun

## Sprint 3 — Controlled Production Publication and Post-Release Calibration

### Design status

**Resolved.** The complete mechanism is tested before production in Sprint 13.

Pre-production validation includes:

- review workflow and exact-hash binding;
- production-shaped configuration rehearsal;
- TEST approval lifecycle and rejection paths;
- no-effect publication dry run or governed manual rehearsal;
- TEST receipt construction;
- observation-window and zero-feedback handling;
- feedback lineage, classification, routing, deduplication, disposition, audit, and replay;
- synthetic, replay, and controlled real-human TEST feedback;
- pre-production calibration.

### What actually remains in Sprint 3

- final human decisions on exact production content, visuals, identity, channels, and limitations;
- final PRODUCTION approval;
- actual external publication and distribution;
- passage of the real observation window;
- `REAL/PRODUCTION` feedback or a production zero-feedback receipt;
- post-release calibration.

### Rerun assessment

**PRODUCTION BOUNDARY PENDING.** Sprint 3 is not a technical blocker. Its testable mechanics are a Sprint 13 implementation obligation. Its remaining native work is intentionally irreducible production authority and evidence.

### Current cleanup gaps

- Issue #14 still contains stale language saying the article body is missing.
- Issue #14 still requires real feedback as though audience response were controllable.
- Visual, article, configuration, and final production decisions remain unrecorded.

These documentation and decision gaps do not change the pre-production testing architecture.

---

## Sprint 5 — Context-Bound Approval and Transaction Foundation

### Present implementation

- TEST and PRODUCTION execution contexts.
- Approval bound to action, subject, content hash, authority class, validity, revocation, and transaction.
- AVAILABLE → RESERVED → CONSUMED lifecycle with exact retry.
- Compare-and-swap approval persistence with local locking and atomic replacement.
- Reservation release after pre-consumption failure.
- Model-use-specific journal, persistence recovery, provider failure, and retry behavior.

### Remaining implementation gaps

1. One reusable governed-operation transaction contract across promotion, state write, migration, disclosure, transition, feedback, and work control.
2. Canonical promotion integrated into that transaction boundary.
3. Common journal-stage model and final transaction receipt.
4. Cross-operation recovery taxonomy and reconstruction.
5. Full cross-context import, replay, rollback, migration, and recovery escalation tests.

### Rerun assessment

**PARTIAL.** Approval authority is strong. The shared transaction kernel is not complete.

---

## Sprint 6 — Enki Cognitive-Core Boundary and Generic Contracts

### Present implementation

- ADR-0002 defines the Enki boundary and product separation.
- Generic subject, evidence, observation, relationship, temporal, confidence, finding, disclosure, request, and result contracts.
- Product-neutral ports.
- Reconciliation scope, traceability, and objective/priority ownership checks.
- Unknown relationships preserve uncertainty.
- Hidden objective or priority substitution fails closed.
- Dependency tests keep human-state, Person Object, EOA/V8, and maturity concepts outside core.
- Constitutional traceability tests exist.

### Remaining closure work

1. Human acceptance or revision of ADR-0002.
2. Explicit schema and contract versioning policy.
3. Decision on whether the current confidence structure is sufficient or requires richer assertion metadata.
4. Evidence manifest mapped to revised Sprint 6.
5. Governed completion amendment after roadmap promotion and branch reconciliation.

### Rerun assessment

**READY FOR COMPLETION REVIEW.** This remains the closest revised sprint to legitimate completion.

---

## Sprint 7 — Generic Observation, Relationship, and Governed State Write

### Present implementation

- Shared contracts and collections for PERSON, ORGANIZATION, and PROJECT.
- One append-only filesystem repository.
- Idempotent identical writes and conflict rejection.
- Generic reconciliation across subject classes without schema forks.

### Remaining implementation gaps

1. Content-addressed generic state-write plan.
2. Exact known-reference, subject, domain, and context preflight.
3. Approval-bound state-write executor.
4. Multi-record journal, immutable receipt, and exact retry.
5. Recovery from partial observation, relationship, and receipt writes.
6. Forensic reconstruction and tamper tests.
7. TEST approval proof across one human and two nonhuman subjects.

### Rerun assessment

**PARTIAL.** Generic storage is implemented. Governed state creation is not.

---

## Sprint 8 — Human-State Compatibility, Authority, and Governed Migration

### Present implementation

- Compatibility adapter outside Enki core.
- Explicit expression-origin choice.
- Legacy Boolean model-feedback approval excluded from generic authority.
- Legacy transitions project to generic relationship assertions.

### Remaining implementation gaps

1. Side-effect-free content-addressed migration plan.
2. Exact migration plan hash and approval binding.
3. Governed migration executor using Sprint 5 transaction semantics.
4. Migration events, receipts, recovery, and duplicate prevention.
5. Unified human privacy, consent, purpose, redaction, correction, retraction, expiry, and revocation layer.
6. Full semantic-parity fixture set across temporal and disputed states.

### Rerun assessment

**PARTIAL.** Compatibility design is proven; governed migration execution is absent.

---

## Sprint 9 — Governed Reconciliation and Disclosure Separation

### Present implementation

- Separate reconcile-and-record and disclose-and-record workflows.
- Findings preserve observation, relationship, evidence, objective, priority, and interpretation references.
- Unknown confidence is deferred.
- Subject disclosure requires a subject request.
- External disclosure checks audience, subject, content hash, transaction, and reserved approval ownership.
- Receipts distinguish surfaced, deferred, and withheld findings.

### Remaining implementation gaps

1. Deterministic temporal and context applicability resolver before reconciliation.
2. Enforceable sensitivity, privacy, consent, purpose, and redaction contracts.
3. Approval reserve, consume, recover, and receipt lifecycle owned by disclosure execution.
4. Journaled finding persistence and reconciliation receipt.
5. Competing-interpretation and authority-conflict fixtures.
6. Revocation and withdrawal propagation.

### Rerun assessment

**PARTIAL.** The conceptual separation is implemented; production-grade governance is incomplete.

---

## Sprint 10 — Governed Transition and Conflict Engine

### Design status

**Resolved.** Required contracts and behavior are specified in the revised roadmap.

### Missing implementation

No generic transactional transition engine currently provides:

- exact before-and-after hashes;
- correction, refinement, supersession, retraction, reversal, expansion, restriction, confidence change, merge, split, and deprecation;
- branch, merge, overlap, contradiction, and competing-authority semantics;
- cycle and stale-input detection;
- approval consumption;
- transaction journal and transition receipt;
- interruption recovery and exact retry;
- deterministic reconstruction;
- human-overlay regression through the generic engine.

A legacy transition record or a relationship projection records a relationship. It does not govern the state mutation.

### Rerun assessment

**IMPLEMENTATION MISSING.** This remains the largest single technical gap.

---

## Sprint 11 — Governed Interpretation and Capability-Isolated Model Use

### Present implementation

- Interpretation, package construction, policy evaluation, authority, receipt, persistence, and dispatch are separated.
- Deterministic canonical package hashing.
- Approval reserve and consumption before persistence.
- Exact-retry recovery after authority consumption.
- TEST dispatcher has no transport, credential, endpoint, callback, or adapter surface.
- PRODUCTION dispatcher requires explicit transport and PRODUCTION receipt.
- Package tampering is rejected before dispatch.
- Provider effects and failures are journaled.

### Remaining implementation gaps

1. Enki-native generic model-use contracts rather than human-state compatibility contracts.
2. Typed, attributable, purpose-bound directives replacing Boolean behavioral flags.
3. Item-level privacy, consent, sensitivity, purpose, and redaction filtering.
4. Explicit package/context matching.
5. Governed revocation and downstream-effect receipts.
6. Integration with Sprint 10 transition outputs.

An actual production transport remains a Sprint 3 execution dependency, not a Sprint 11 TEST completion requirement.

### Rerun assessment

**PARTIAL, WITH STRONG SUBSTRATE.** Dispatch isolation and recovery are good; generic governance and privacy remain.

---

## Sprint 12 — Forensic Reconstruction, Portability, and Governed Work Completion

### Present implementation

- Model-use journal and forensic reconstruction.
- Approval persistence and exact-retry evidence.
- Repository audit and state-authority registration for new Enki record families.
- Evidence-required COMPLETE status in work-control schemas.

### Remaining implementation gaps

1. Common reconstruction interface and result taxonomy across all operation families.
2. Reconstruction for generic state write, migration, reconciliation, disclosure, transition, feedback, canonical promotion, and work-control amendment.
3. Clean-room and disaster-recovery exercises.
4. Import/export package preserving authority, context, hashes, consumption, and receipt lineage.
5. GitHub adapter parity for the declared shared contract surface.
6. Journaled, approval-bound, reconstructable work-control amendment transaction.
7. Cross-operation TEST-to-PRODUCTION escalation suite.

### Rerun assessment

**PARTIAL.** Model-use forensics exist; system-wide reconstruction and governed work completion do not.

---

## Sprint 13 — Integrated TEST Proof, Pre-Production Feedback Validation, and Release Candidate

### Design status

**Resolved.** The testing approach has already been established.

Required evidence modes:

- `SYNTHETIC/TEST` for scenario and adversarial coverage;
- `REPLAY/TEST` for regression where immutable cases exist;
- controlled `REAL/TEST` from an identified human evaluator;
- strict rejection of all TEST evidence by production gates.

### Missing implementation

1. Feedback provenance and execution-context contracts.
2. Feedback schemas, repositories, receipts, and services.
3. Publication-lineage validation.
4. Classification, routing, deduplication, disposition, and promotion-control pipeline.
5. Synthetic scenario corpus and expected outcomes.
6. Replay harness preserving original provenance without creating new feedback.
7. Controlled human TEST interface.
8. Observation-window and zero-feedback TEST proof.
9. Two complete adaptive loops across different subject classes.
10. End-to-end chaos and interruption campaign.
11. Hash-bound pre-production calibration report.
12. Versioned release candidate, threat model, runbooks, rollback path, release notes, limitations, internal release decision, and Sprint 3 handoff.

### Rerun assessment

**IMPLEMENTATION MISSING, DESIGN RESOLVED.** The problem is execution of the agreed test architecture, not discovery of how to test before production.

---

# Consolidated gap structure

Most remaining work is not thirteen unrelated feature sets. It concentrates in four shared mechanisms.

## Mechanism A — Shared governed transaction kernel

Closes major gaps in Sprints 5, 7, 8, 9, 10, 12, and 13:

- exact plans and hashes;
- authority reservation and consumption;
- journals and receipts;
- idempotency and exact retry;
- rollback and interruption recovery;
- common reconstruction.

## Mechanism B — Generic transition and conflict engine

Closes Sprint 10 and enables final integration for Sprints 11–13:

- governed changes;
- branch and merge lineage;
- conflict and authority semantics;
- transition receipts and reconstruction.

## Mechanism C — Governed feedback and calibration subsystem

Closes Sprint 13 and provides the tested production handoff to Sprint 3:

- provenance/context matrix;
- synthetic, replay, and controlled human TEST paths;
- feedback processing and disposition;
- observation windows and zero-feedback receipts;
- calibration reports.

## Mechanism D — Canonical promotion and branch integration

Makes the revised plan governable:

- approve PR #28;
- promote revised sprint and backlog records;
- reconcile PR #27 with current `sandbox`;
- map evidence to revised sprint boundaries;
- execute governed completion amendments.

---

# Corrected critical path

```text
Approve PR #28
→ canonically promote revised roadmap
→ reconcile PR #27 with current sandbox
→ review and integrate Enki core substrate
→ implement shared transaction kernel
→ complete Sprint 6 evidence review
→ execute Sprint 7 governed state writes
→ execute Sprint 8 governed migration
→ harden Sprint 9 temporal/privacy disclosure
→ implement Sprint 10 transition/conflict engine
→ complete Sprint 11 generic privacy-governed model use
→ complete Sprint 12 reconstruction and work-control amendment
→ execute Sprint 13 integrated TEST, feedback validation, chaos, calibration, and release proof
→ hand exact release candidate to Sprint 3
→ obtain final production authority and cause the external effect
```

## Parallelizable now

- Sprint 6 ADR and evidence review.
- Sprint 13 feedback contracts and synthetic scenario corpus design.
- Sprint 3 article, visual, identity, channel, and configuration review.
- Publication dry-run specification and observation-window contract.
- Threat model, runbook, rollback, and release-document skeletons.

## Cannot be honestly claimed early

- Sprint 10 completion before governed state-write and migration semantics stabilize.
- Sprint 11 final integration before Sprint 10 transition outputs exist.
- Sprint 12 cross-operation reconstruction before the operation families exist.
- Sprint 13 integrated proof before Sprints 7–12 are operational.
- Sprint 3 production calibration before Sprint 13 has proven the mechanism in TEST.

# Same-day completion finding

The repository does not currently contain enough implementation evidence to mark completion through Sprint 13 today without manufacturing unsupported status.

That does not indicate an architectural paradox. It indicates three substantial missing executable systems plus governance integration:

1. the shared transaction kernel;
2. the generic transition/conflict engine;
3. the governed feedback/calibration subsystem;
4. canonical roadmap promotion and branch reconciliation.

The fastest legitimate route is to build those shared mechanisms and reuse them across sprint boundaries rather than implementing each sprint as isolated work.

# Final rerun finding

The corrected gap is narrower and clearer than the first analysis suggested:

- **Sprint 3 is not waiting for us to invent pre-production testing.** That design is solved.
- **Sprint 13 must implement and execute the solved pre-production test architecture.**
- **Sprint 3 then performs only the final human-authorized production transaction and records real production evidence.**
- **Sprint 10 remains the largest missing domain capability.**
- **The shared transaction kernel is the highest-leverage foundational build.**

The system is not blocked by perception or paradox. It is blocked by a bounded set of executable mechanisms and their evidence-bearing promotion.
