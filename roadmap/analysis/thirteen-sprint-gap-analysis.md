# Thirteen-Sprint Gap Analysis

> **Authority class: Class 3 — implementation assessment.**
> This analysis compares the revised thirteen-sprint proposal with the live canonical roadmap and the current implementation in PR #27. It does not change sprint status or authorize production.

- Assessment date: 2026-07-13
- Canonical branch assessed: `sandbox`
- Revised-plan branch: `roadmap/refactor-to-thirteen-sprints`
- Implementation branch: `agent/enki-core-refactor`
- Implementation PR: `#27`
- Roadmap PR: `#28`
- PR #27 head assessed: `c29c0de4425e82d693e1c635d12a36e7f3b76097`

## Executive conclusion

The repository contains a substantial Enki-core implementation substrate, but the revised roadmap is not yet canonical and the implementation does not yet support completion through Sprint 13.

The current condition is:

- Sprints 1, 2, and 4 are canonically complete.
- Sprint 3 remains canonically blocked under obsolete exit language.
- Sprints 5–11 remain canonically planned with no completion evidence.
- Sprints 12 and 13 do not yet exist in canonical work control.
- PR #27 provides strong candidate evidence for Sprint 6 and material partial evidence for Sprints 5, 7, 8, 9, 11, and 12.
- Sprint 10 is not implemented as a generic governed transition/conflict engine.
- Sprint 13 pre-production feedback validation and integrated release proof are not implemented.

Passing CI establishes regression health. It does not establish that the revised sprint exit criteria are satisfied.

## Status vocabulary

- **READY FOR COMPLETION REVIEW** — implementation appears to cover the revised scope; remaining work is evidence mapping, review, and governed status amendment.
- **PARTIAL** — useful implementation exists, but one or more material exit criteria lack code or evidence.
- **MISSING** — the primary sprint capability is not implemented.
- **EXTERNAL / HUMAN GATE** — completion depends on explicit human authority or an actual external effect and cannot be manufactured by CI.

## Gap matrix

| Sprint | Revised capability | Current assessment | Principal gap |
|---|---|---|---|
| 1 | Canonical identity and repository truth | COMPLETE | None; preserve historical evidence |
| 2 | Canonical backlog and roadmap control plane | COMPLETE | None; use it to promote the revised plan |
| 3 | Controlled production publication and post-release calibration | EXTERNAL / HUMAN GATE | Roadmap language is stale; approvals, configuration, production execution, observation window, and calibration remain |
| 4 | Restricted canonical writer | COMPLETE | None; extend rather than bypass it |
| 5 | Context-bound approval and transaction foundation | PARTIAL | Approval lifecycle exists; one general journaled transaction/promotion boundary does not |
| 6 | Enki cognitive-core boundary and generic contracts | READY FOR COMPLETION REVIEW | Architecture decision and implementation evidence still require governing acceptance and mapping |
| 7 | Generic observation, relationship, and state-write substrate | PARTIAL | Generic storage exists; governed approval-bound state-write transaction and receipt do not |
| 8 | Human-state compatibility, authority, and governed migration | PARTIAL | Compatibility projection exists; governed migration transaction, consent/privacy enforcement, and migration receipts do not |
| 9 | Governed reconciliation and disclosure separation | PARTIAL | Separation exists; temporal/context applicability, privacy/redaction, journaled authority consumption, and recovery remain incomplete |
| 10 | Governed transition and conflict engine | MISSING | No generic transactional transition engine, conflict semantics, lineage reconstruction, or transition receipts |
| 11 | Governed interpretation and capability-isolated model use | PARTIAL | Strong dispatch boundary exists; typed directives, package-wide privacy filtering, context matching, and revocation remain incomplete |
| 12 | Forensic reconstruction, portability, and governed work completion | PARTIAL | Model-use reconstruction exists; cross-operation reconstruction, clean-room recovery, GitHub adapter parity, and governed work amendment do not |
| 13 | Integrated TEST proof, pre-production feedback validation, and release candidate | MISSING | No feedback harness, controlled human TEST path, integrated loops, chaos proof, calibration report, or release package |

---

# Governance and roadmap gaps

## G-1 — Revised roadmap is not canonical

The live generated roadmap still contains eleven sprints. Sprint 3 still requires real feedback as a mandatory occurrence, Sprints 5–11 retain their prior scopes, and Sprints 12–13 do not exist.

### Closure required

1. Record the human roadmap decision on PR #28.
2. Promote the accepted Sprint 3 and Sprint 5–13 definitions through the governed work-control path.
3. Create canonical sprint and work-item records for Sprints 12 and 13.
4. Regenerate canonical roadmap and backlog projections.
5. Regenerate the repository audit and run all authority checks.

No implementation sprint can be canonically completed against the revised scope until this promotion occurs.

## G-2 — PR #27 narrative exceeds the live file evidence in several areas

The PR description refers to governed generic state-write plans, migration receipts, and broader forensic reconstruction. The live changed-file set does not contain dedicated state-write transaction services, migration transaction services, migration receipt schemas, generic transition services, or a governed work-control amendment mechanism.

### Governing rule

Use executable files, tests, schemas, receipts, and workflow artifacts as evidence. Treat PR prose as a claim to verify, not as completion evidence.

## G-3 — Completion evidence has not been mapped to revised sprint criteria

PR #27 is one implementation substrate spanning multiple revised sprints. It cannot be treated as one indivisible completion event.

### Closure required

For each sprint, produce an evidence manifest binding:

- exact commit;
- relevant source files;
- schemas;
- tests;
- workflow run and artifacts;
- generated audit;
- remaining limitations;
- governing review decision.

---

# Sprint-by-sprint analysis

## Sprint 5 — Context-Bound Approval and Transaction Foundation

### Present evidence

- `ExecutionContext` separates TEST and PRODUCTION.
- `ApprovalGrant` binds action, subject, content hash, authority class, validity, revocation, and consumption state.
- Approval lifecycle supports AVAILABLE, RESERVED, CONSUMED, and REVOKED states.
- Reservation and consumption use compare-and-swap semantics.
- Exact retry by the same transaction is supported.
- A durable filesystem approval repository uses exclusive lock and atomic replacement.
- Model-use execution demonstrates reserve, authorize, consume, persist, journal, release, and retry behavior for one operation family.

### Material gaps

1. **No general transaction coordinator.** Transaction behavior is implemented primarily for human-state model use, not one reusable operation contract covering canonical promotion, state creation, migration, disclosure, transition, feedback, and work control.
2. **Canonical promotion is not journaled through this mechanism.** The current restricted writer remains separate from the new approval lifecycle.
3. **No universal transaction receipt.** Operation-specific events exist, but there is no common immutable transaction receipt binding exact inputs, outputs, authority, context, and final disposition across all operation families.
4. **Recovery taxonomy is incomplete.** COMPLETE, rollback, repairable, and CONFLICT reconstruction is not available across all governed operations.
5. **Cross-path escalation tests are incomplete.** Import, replay, migration, rollback, and recovery have not all been proven incapable of turning TEST authority into PRODUCTION authority.

### Minimum closure package

- General governed-operation transaction contract and state machine.
- Integration with canonical promotion and restricted writer.
- Common journal and final receipt contract.
- Interruption tests before and after authority consumption.
- Cross-context replay and escalation tests.
- Sprint 5 evidence manifest and governed completion amendment.

### Assessment

**PARTIAL.** Approval semantics are strong enough to retain. The remaining gap is generalization into the shared transaction foundation claimed by the sprint.

---

## Sprint 6 — Enki Cognitive-Core Boundary and Generic Contracts

### Present evidence

- ADR-0002 defines Enki as a governed cognitive and reconciliation kernel rather than a Person, Organization, maturity, clinical, or product ontology.
- Generic contracts exist for subject, evidence, confidence, temporal applicability, observation, relationship, finding, disclosure, request, and result.
- Reconciliation validates subject and domain scope, evidence references, and objective/priority ownership.
- Hidden objective and priority substitution fail closed.
- The baseline strategy preserves unknown relationships as uncertainty.
- Architecture tests inspect the Enki package for prohibited bounded-context dependencies.
- Constitutional traceability maps invariants to contract, service, and test references.

### Remaining gaps

1. **ADR status remains proposed.** Governing human acceptance is not yet recorded.
2. **No canonical sprint evidence mapping.** The implementation must be bound to revised Sprint 6 rather than the former Sprint 7-oriented proposal.
3. **Contract versioning policy is implicit.** Interpretation versions exist, but schema and compatibility evolution rules should be explicit before production records accumulate.
4. **Confidence structure is still narrow.** It has level, rationale, and evidence IDs, but not the full asserted value, source, basis, method, context, applicable time, and uncertainty-note structure envisioned by the refactor plan.

### Minimum closure package

- Accept or revise ADR-0002.
- Add explicit contract/schema versioning and compatibility rules.
- Decide whether the present confidence contract satisfies Sprint 6 or requires extension.
- Map tests and files to every Sprint 6 exit criterion.
- Execute the governed Sprint 6 completion amendment.

### Assessment

**READY FOR COMPLETION REVIEW.** This is the strongest revised sprint in the current implementation.

---

## Sprint 7 — Generic Observation, Relationship, and State-Write Substrate

### Present evidence

- Shared observation and relationship contracts work for PERSON, ORGANIZATION, and PROJECT subjects.
- One filesystem repository stores all three subject classes in shared collections.
- Append-only identifiers are idempotent and reject conflicting rewrites.
- Reconciliation operates on the shared contracts without subject-specific schema forks.

### Material gaps

1. **Direct repository writes remain possible.** `append_observations()` and `append_relationships()` accept records directly without approval, execution context, transaction, or receipt.
2. **No generic state-write plan.** Exact plan hashing, known-reference binding, and preflight validation are not represented as a reusable application contract.
3. **No approval consumption for generic writes.** The tests exercise direct persistence rather than TEST-scoped state-write approvals.
4. **No state-write journal or immutable receipt.** Generic records are append-only, but the operation that created them is not independently reconstructable.
5. **No interruption recovery.** There is no demonstrated recovery from observations written without relationships, authority consumed before write, or receipt missing after write.
6. **No canonical record instances.** The repository audit still reports zero operational Enki observations and relationships in the assessed branch state.

### Minimum closure package

- Content-addressed `StateWritePlan` covering observations, relationships, known references, subject, domain, and context.
- Approval-bound `ExecuteStateWrite` workflow.
- Atomic or recoverable multi-record write sequence.
- State-write journal and receipt schema.
- Forensic reconstruction and tamper tests.
- TEST approvals across one human and at least two nonhuman subjects.

### Assessment

**PARTIAL.** Generic contracts and storage are proven; governed state creation is not.

---

## Sprint 8 — Human-State Compatibility, Authority, and Governed Migration

### Present evidence

- The compatibility adapter lives outside Enki core.
- Human observations can be projected into generic observations.
- Expression origin must be supplied explicitly rather than inferred from explicit wording.
- Legacy model-feedback Boolean fields are excluded from generic authority.
- Human transitions can be represented as relationship assertions for compatibility.

### Material gaps

1. **Projection is not migration.** The current adapter transforms in memory; it does not create a side-effect-free migration plan or execute a governed migration transaction.
2. **No migration-plan hash or approval.** There is no exact migration content hash bound to subject, authority, context, and transaction.
3. **No migration receipts or events.** Partial migration and exact retry cannot be forensically reconstructed.
4. **Human protection execution is incomplete.** Consent, privacy classification, purpose scope, redaction, expiration, revocation, subject correction, and retraction are not enforced by a unified human overlay workflow.
5. **Transition projection loses attributable evidence.** Legacy transition confidence is reduced to UNKNOWN because the legacy contract lacks attributable evidence references.
6. **No semantic-parity fixture set.** Current, historical, conditional, disputed, tentative, retracted, expired, superseded, and context-inapplicable states have not all been proven through migration and generic reconciliation.

### Minimum closure package

- Content-addressed migration plan with one explicit origin decision per observation.
- Approval-bound migration executor using Sprint 5 transaction semantics.
- Immutable migration receipt and event schema.
- Interruption recovery and duplicate-prevention tests.
- Human consent/privacy/purpose/correction/revocation policy layer.
- Full semantic-parity fixture suite.

### Assessment

**PARTIAL.** Compatibility semantics are promising; operational governed migration is absent.

---

## Sprint 9 — Governed Reconciliation and Disclosure Separation

### Present evidence

- Reconciliation and disclosure are separate services.
- Reconciliation findings are attributable to observations, relationships, evidence, objectives, priorities, and interpretation version.
- Unknown relationship types remain uncertain.
- Unknown-confidence findings are deferred rather than erased.
- Subject-facing disclosure requires subject request.
- External-model and public disclosure require a reserved or exact-retry approval bound to audience, subject, and content hash.
- Disclosure receipts distinguish surfaced, deferred, and withheld findings.

### Material gaps

1. **Temporal applicability is not resolved by the core engine.** The engine accepts the observations and relationships supplied by the caller but does not itself reject retracted, expired, superseded, future, or context-inapplicable state.
2. **No sensitivity and privacy classification.** Findings and disclosure contexts lack enforceable sensitivity, privacy, consent, and redaction contracts.
3. **Approval is checked but not consumed in the disclosure workflow.** `DiscloseAndRecord` receives an evaluation and writes a receipt, but does not own a reserve/consume/recover transaction.
4. **Finding persistence is not journaled.** Reconciliation may persist findings directly through an optional writer with no execution-context receipt.
5. **No deterministic competing-interpretation model.** The structures allow hypotheses, but the baseline strategy creates one finding per supplied relationship and does not preserve or rank multiple candidate interpretations.
6. **No revocation or withdrawal propagation.** A later authority or privacy revocation does not invalidate or supersede prior disclosure eligibility through a governed transition.

### Minimum closure package

- Deterministic context and temporal state resolver before reconciliation.
- Sensitivity, privacy, consent, purpose, and redaction contracts.
- Transactional reconcile-and-record and disclose-and-record workflows.
- Approval consumption and recovery for external disclosure.
- Competing-interpretation fixtures and receipts.
- Revocation propagation tests.

### Assessment

**PARTIAL.** The conceptual boundary is implemented, but its production governance is incomplete.

---

## Sprint 10 — Governed Transition and Conflict Engine

### Present evidence

- The legacy human-state domain has a `HumanStateTransition` record.
- The compatibility adapter can project a legacy transition as a generic relationship assertion.
- Generic observations carry temporal status.

### Missing primary capability

There is no generic governed transition engine implementing:

- exact before-and-after state hashes;
- correction, refinement, supersession, retraction, reversal, expansion, restriction, confidence change, merge, split, and deprecation;
- branch and merge lineage;
- contradictory or overlapping transitions;
- authority conflicts;
- cycle detection;
- stale-input rejection;
- context-bound approval consumption;
- transaction journal and transition receipt;
- interruption recovery;
- deterministic forensic reconstruction;
- human-state regression through the generic engine.

Mapping a transition to a relationship assertion does not satisfy these requirements because it records that a relationship exists without governing the state mutation it represents.

### Minimum closure package

- Versioned generic transition contracts and schemas.
- Transition preflight planner binding exact source and destination state hashes.
- Conflict and branch/merge model.
- Approval-bound executor with journal, receipt, rollback, and exact retry.
- Reconstruction service and adversarial tests.
- Human overlay regression suite.

### Assessment

**MISSING.** This is the largest implementation gap and the principal technical critical-path item.

---

## Sprint 11 — Governed Interpretation and Capability-Isolated Model Use

### Present evidence

- Human-state interpretation, package construction, policy evaluation, approval, receipt creation, persistence, and dispatch are separated.
- Package hashes use deterministic canonical JSON.
- Model-use execution reserves and consumes exact approval authority before persistence.
- Exact retry can recover after authority consumption.
- TEST dispatch accepts no transport, credentials, endpoint, callback, or generic adapter.
- PRODUCTION dispatch requires an explicitly injected production transport and PRODUCTION receipt.
- Package tampering is rejected before transport invocation.
- Provider failures and effects are journaled.

### Material gaps

1. **Model-use contracts remain human-state specific.** The workflow has not yet been generalized to Enki findings and generic subject contracts.
2. **Behavioral instructions remain opaque Boolean flags.** Typed, attributable, purpose-bound directives are not implemented.
3. **Package-wide privacy filtering is absent.** The package may contain current and historical observations without item-level sensitivity, consent, purpose, or redaction evaluation.
4. **Context matching is incomplete.** `requires_context_match` exists in policy but the authorization path does not enforce an explicit package/context match.
5. **Revocation is declarative rather than operational.** Receipts are marked revocable, but no governed revocation workflow prevents future use or records downstream revocation effects.
6. **No production transport implementation.** The capability boundary exists, but an operational adapter and credentials are intentionally absent.
7. **No generic transition authority.** Model-use can explicitly include legacy transitions, but cannot yet consume output from the missing Sprint 10 engine.

### Minimum closure package

- Enki-native interpretation and model-use package.
- Typed model-use directives.
- Item-level privacy, consent, purpose, sensitivity, and redaction filter.
- Explicit context-match enforcement.
- Governed revocation workflow and receipts.
- Transition-engine integration.
- Production adapter remains a Sprint 3 dependency, not a Sprint 11 TEST completion requirement.

### Assessment

**PARTIAL.** The capability-isolated dispatch and recovery boundary are strong; the data-governance and generic-contract layers are incomplete.

---

## Sprint 12 — Forensic Reconstruction, Portability, and Governed Work Completion

### Present evidence

- Model-use events and receipts can be reconstructed.
- Repository audit and state-authority validation include new Enki record families.
- Approval grants use durable filesystem persistence.
- Some model-use partial-output and exact-retry behavior is tested.
- Existing work-control records require evidence before COMPLETE status.

### Material gaps

1. **Reconstruction is operation-specific.** Generic state write, migration, disclosure, transition, feedback, canonical promotion, and work-control amendments lack equivalent reconstruction.
2. **No clean-room recovery exercise.** There is no demonstrated rebuild from immutable records and receipts into an equivalent authoritative state.
3. **No import/export portability contract.** Context, approval scope, consumption, hashes, and receipt lineage are not proven across migration between repositories.
4. **No GitHub adapter parity.** The assessed implementation is filesystem-oriented; there is no adapter implementing the shared transaction surface through GitHub.
5. **No governed work-control amendment transaction.** Sprint and backlog status changes are schema-validated, but not yet executed through a journaled, approval-bound, reconstructable amendment workflow.
6. **No cross-operation privilege-escalation suite.** TEST artifacts have not been proven unable to become PRODUCTION through every import, replay, rollback, and recovery path.

### Minimum closure package

- Common forensic reconstruction interface and result taxonomy.
- Reconstruction for every operation family.
- Clean-room and disaster-recovery exercises.
- Import/export package preserving authority and lineage.
- GitHub adapter for the declared shared contract surface.
- Governed work-control amendment and reconstruction workflow.
- Cross-context escalation test matrix.

### Assessment

**PARTIAL.** Useful model-use forensics exist, but system-wide portability and work-control governance remain unimplemented.

---

## Sprint 13 — Integrated TEST Proof, Pre-Production Feedback Validation, and Release Candidate

### Present evidence

- Unit and component tests cover many Enki-core and model-use behaviors.
- CI, runtime coverage, state authority, work-control authority, canonicalization security, and publication-asset workflows pass on the PR #27 head.
- TEST model-use dispatch is structurally non-side-effecting.

### Missing primary capability

1. **No feedback provenance contract.** `REAL`, `SYNTHETIC`, and `REPLAY` are not implemented as a governed feedback type independent of execution context.
2. **No feedback pipeline.** There is no ingestion, publication lineage, classification, routing, deduplication, disposition, promotion control, audit, or replay service.
3. **No synthetic scenario corpus.** Supportive, critical, corrective, ambiguous, irrelevant, duplicate, contradictory, adversarial, malformed, mismatched, unauthorized, and zero-response cases are not encoded.
4. **No replay harness.** Historical cases cannot be rerun while preserving original provenance and preventing them from appearing as new feedback.
5. **No controlled human TEST interface.** There is no mechanism for an identified evaluator to produce `REAL/TEST` feedback through a non-side-effecting path.
6. **No integrated adaptive loops.** The system has not executed complete state-write → reconciliation → disclosure → transition → interpretation → model-use → feedback → disposition loops across two subject classes.
7. **No chaos campaign.** Interruption at every authority, persistence, receipt, dispatch, and recovery boundary has not been exercised end to end.
8. **No calibration report.** Expected and observed synthetic, replay, and human results are not compared in a hash-bound artifact.
9. **No release package.** Version, threat model, runbooks, rollback path, release notes, known limitations, and internal release decision do not exist as an integrated candidate.

### Minimum closure package

- Feedback contracts, schemas, repositories, receipts, and execution services.
- Synthetic scenario fixtures and expected outcomes.
- Replay harness.
- Controlled human TEST review surface and authority boundary.
- Two complete integrated loops across different subject classes.
- Chaos and recovery matrix.
- Pre-production calibration report.
- Versioned release candidate, threat model, runbooks, rollback, release notes, and Sprint 3 handoff.

### Assessment

**MISSING.** Existing tests are inputs to Sprint 13, not evidence that Sprint 13 has occurred.

---

# Sprint 3 parallel production lane

## Present evidence

- Publication 000001 canonical record exists.
- Article body now exists at the declared draft path.
- Visual package and manifest exist and automated checks pass.
- A configuration worksheet exists.
- Issue #14 provides a traceable approval workspace.

## Remaining gaps

1. Issue #14 still states that the article body is missing and retains the obsolete mandatory real-feedback exit language.
2. Human visual decision is not recorded.
3. Human article-body decision is not recorded.
4. Channels, account identity, byline, brand treatment, channel copy, selected assets, and publication method remain unresolved.
5. Final production authorization has not been recorded against exact body and manifest hashes.
6. Production publication and distribution receipts do not exist.
7. The observation-window and zero-feedback receipt contracts do not exist.
8. Sprint 13 pre-production feedback validation has not occurred.
9. No post-release calibration report exists.

## Closure sequence

Sprint 3 should remain parallel until Sprint 13 has produced the pre-production calibration report and release handoff. Visual, editorial, and configuration review can proceed before then.

---

# Critical path

The minimum legitimate technical critical path is:

```text
Roadmap approval and canonical promotion
→ Sprint 5 general transaction foundation
→ Sprint 6 completion review
→ Sprint 7 governed state-write transaction
→ Sprint 8 governed human migration
→ Sprint 9 temporal/privacy-governed reconciliation and disclosure
→ Sprint 10 transition/conflict engine
→ Sprint 11 generic privacy-filtered model use and revocation
→ Sprint 12 system-wide reconstruction and governed work completion
→ Sprint 13 feedback validation, integrated loops, chaos proof, and release candidate
```

Sprint 3 editorial, visual, and configuration work can proceed in parallel. Production authorization waits for Sprint 13 or an explicit accepted limitation.

## Parallelizable work

The following can be developed without violating the dependency chain:

- Roadmap promotion records and Sprint 5 transaction work.
- Sprint 6 evidence mapping and ADR review.
- Sprint 13 feedback contracts and synthetic scenario design, provided they depend only on stable core contracts.
- Sprint 3 visual, article, and publication-configuration review.
- Release-document skeletons, threat-model outline, and runbook templates.

The following cannot be honestly completed early:

- Sprint 10 before governed state creation and human migration semantics are stable.
- Sprint 11 final integration before Sprint 10 transition outputs exist.
- Sprint 12 cross-operation reconstruction before all operation families exist.
- Sprint 13 integrated proof before Sprints 7–12 are operational.
- Sprint 3 production calibration before Sprint 13 feedback validation.

# Recommended immediate execution order

1. Approve or revise PR #28.
2. Promote the revised roadmap canonically.
3. Review PR #27 as the shared implementation substrate and merge only after its current claims are reconciled with live files.
4. Close Sprint 5's general transaction gap.
5. Complete Sprint 6 evidence review.
6. Implement Sprint 7 governed state-write workflow.
7. Implement Sprint 8 governed migration workflow.
8. Harden Sprint 9 temporal, privacy, and disclosure transactions.
9. Build Sprint 10 transition/conflict engine.
10. Generalize and privacy-harden Sprint 11 model use.
11. Build Sprint 12 cross-operation reconstruction and governed work amendment.
12. Execute Sprint 13 feedback, integrated, chaos, and release proof.
13. Hand the release candidate to Sprint 3 for separately authorized production validation.

# Final assessment

The architecture is not blocked by a paradox. It is blocked by a finite set of missing operation boundaries.

The greatest leverage comes from implementing three missing shared mechanisms rather than treating every sprint as independent feature work:

1. a reusable approval-bound transaction and receipt engine;
2. a generic transition/conflict engine;
3. a governed feedback and calibration subsystem.

Those three mechanisms close the majority of the remaining gaps across Sprints 5, 7–13 while preserving the modularity established by the revised roadmap.
