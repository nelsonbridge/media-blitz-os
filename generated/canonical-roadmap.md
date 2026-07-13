# Canonical Sprint Roadmap

> Generated from canonical work-control records. Do not edit manually.

## Sprint 1 — Canonical identity and repository truth

- ID: `NKS-SPR-001`
- Status: `complete`
- Objective: Establish schema-aware canonical identity and reconcile stale branches.
- Work items: BL-001
- Evidence records: 1

Exit criteria:

- Identity registry covers canonical collections
- Hosted validation passes

## Sprint 2 — Canonical backlog and roadmap control plane

- ID: `NKS-SPR-002`
- Status: `complete`
- Objective: Make work status evidence-bearing, machine-readable, and deterministically projected.
- Work items: BL-002
- Evidence records: 2

Exit criteria:

- Canonical work records exist
- Generated backlog and roadmap are deterministic
- Authority drift is detectable

## Sprint 3 — First live publication cycle

- ID: `NKS-SPR-003`
- Status: `blocked`
- Objective: Complete Publication 000001 through human approval, publication, receipts, and real feedback.
- Work items: BL-003
- Evidence records: 0

Exit criteria:

- Human decisions are recorded
- Publication and social receipts exist
- Real feedback is ingested

## Sprint 4 — Restricted canonical writer

- ID: `NKS-SPR-004`
- Status: `complete`
- Objective: Enforce one canonical source mutation boundary.
- Work items: BL-004
- Evidence records: 5

Exit criteria:

- Direct writes are prohibited
- Authorization is hash-bound
- Idempotency is enforced

## Sprint 5 — Journaled promotion and approval isolation

- ID: `NKS-SPR-005`
- Status: `planned`
- Objective: Make canonical promotion recoverable, journaled, idempotent, and receipted while establishing context-bound TEST and PRODUCTION approval lanes with policy and adapter-level side-effect isolation.
- Work items: BL-005
- Evidence records: 0

Exit criteria:

- Interrupted promotion converges to one committed transaction or one documented rollback
- Partial authority cannot persist and immutable receipts bind exact inputs, outputs, and execution context
- Approval grants are evaluated against context, action, subject, content, authority, validity, and consumption state
- TEST approvals cannot satisfy PRODUCTION gates or produce production side effects, receipts, REAL feedback, or production model ingestion
- TEST adapters are incapable of external side effects
- Import, replay, migration, rollback, and recovery preserve approval context and reject escalation

## Sprint 6 — Temporal human-state testable reference implementation

- ID: `NKS-SPR-006`
- Status: `planned`
- Objective: Productionize temporal human state on the Sprint 5 journal, receipt, recovery, audit, and approval-context foundation, proving a complete automated TEST lane before generalizing into Governed Adaptive Knowledge.
- Work items: BL-006
- Evidence records: 0

Exit criteria:

- Human-state creation, transition, policy, revocation, and model-feedback operations are journaled and receipted
- TEST-scoped approvals exercise the complete human-state loop without external effects or production authority
- PRODUCTION actions require recognized human authority and reject TEST approval consumption
- Privacy classification, consent, purpose scope, redaction, expiration, and revocation fail closed
- CLI commands, canonical collections, generated views, authority manifest, and forensic audit preserve execution context
- Behavior evaluation fixtures prove that current, contextual, uncertain, disputed, retracted, superseded, and context-inapplicable states are handled correctly

## Sprint 7 — Governed Adaptive Knowledge state and approval substrate

- ID: `NKS-SPR-007`
- Status: `planned`
- Objective: Generalize the proven human-state reference implementation into platform-neutral Subject, Domain, KnowledgeState, and approval-applicability contracts while preserving stricter human-agency protections.
- Work items: BL-007
- Evidence records: 0

Exit criteria:

- Generic state and approval-applicability contracts work without subject-specific schema forks
- Every state creation is journaled, receipted, recoverable, auditable, and bound to execution context
- TEST approvals exercise one human and at least two nonhuman subject classes without production effects
- Human consent, privacy, self-declaration, correction, and production-authority protections remain stricter and regression-tested
- Views, authority registration, migration mappings, and audits preserve approval context
- The substrate is ready for context-bound transactional transitions in Sprint 8

## Sprint 8 — Governed transition, conflict, and approval engine

- ID: `NKS-SPR-008`
- Status: `planned`
- Objective: Implement the transactional state-change engine for Governed Adaptive Knowledge with exact state hashes, context-bound approvals, conflict semantics, recovery, and receipts.
- Work items: BL-008
- Evidence records: 0

Exit criteria:

- All supported transition types bind exact before-and-after state hashes, execution context, approval identity, and receipt
- TEST transition approvals cannot mutate PRODUCTION state or satisfy production transition gates
- Invalid, cyclic, contradictory, context-mismatched, or unauthorized transitions fail closed
- Transition lineage, branch and merge state, overlaps, and authority conflicts are reconstructable
- Recovery after interruption produces one committed transition or one documented rollback
- Human-state regression tests pass through the generic engine without weakening human-specific controls

## Sprint 9 — Interpretation resolution and context-bound model-use boundary

- ID: `NKS-SPR-009`
- Status: `planned`
- Objective: Implement deterministic interpretation resolution and purpose-limited model-use publication with context-bound approvals, non-side-effecting TEST adapters, and separately authorized PRODUCTION dispatch.
- Work items: BL-009
- Evidence records: 0

Exit criteria:

- Interpretation resolution is deterministic and authority-aware across context, validity, confidence, restrictions, and behavioral authority
- Retracted, expired, superseded, disputed, context-inapplicable, or unauthorized state cannot control behavior
- TEST approvals exercise interpretation and model-package generation, redaction, expiration, revocation, recovery, and receipts without production dispatch
- TEST adapters cannot publish externally and TEST evidence cannot satisfy production gates
- PRODUCTION model-use packages require recognized authority, exact hashes, purpose limitation, privacy filtering, journaling, revocation, and immutable receipts
- Prediction remains downstream and cannot mutate canonical knowledge state

## Sprint 10 — Forensic reconstruction, migration, and approval-context portability

- ID: `NKS-SPR-010`
- Status: `planned`
- Objective: Prove system-wide reconstruction, authorized migration, clean-room recovery, and adapter parity while preserving execution context and preventing TEST-to-PRODUCTION privilege escalation.
- Work items: BL-010
- Evidence records: 0

Exit criteria:

- Every governed mutation and approval consumption is forensically reconstructable
- Import and migration preserve execution context, approval scope, authority, hashes, validity, consumption, and receipt lineage
- TEST approvals, receipts, provenance, and adapter capabilities cannot become PRODUCTION through import, migration, replay, rollback, or recovery
- Privilege-escalation, corrupt-input, stale-input, unsupported-migration, and cross-context replay tests fail closed
- Clean-room offline and disaster-recovery exercises pass
- Filesystem and GitHub adapters exhibit equivalent transaction, approval, recovery, receipt, and audit behavior

## Sprint 11 — Two-lane operational proof, hardening, and release candidate

- ID: `NKS-SPR-011`
- Status: `planned`
- Objective: Prove repeated governed adaptive operation through a fully automated TEST lane and a separately authorized PRODUCTION lane, then harden and version the release candidate without treating test approval as real-world authority.
- Work items: BL-011
- Evidence records: 0

Exit criteria:

- At least two complete TEST adaptive loops run across different subject classes using TEST-scoped approvals and non-side-effecting adapters
- TEST journals and receipts are reconstructable but cannot satisfy production publication, REAL-feedback, model-ingestion, release-evidence, or release-authorization gates
- Publication 000001 or an equivalent external cycle uses explicit PRODUCTION approval, external publication, REAL feedback, governed transition, interpretation, and production model-use receipts
- Chaos and interruption drills recover without duplicates, unexplained state, context escalation, or partial authority
- All release gates pass or have explicit governing-authority acceptance with recorded limitations
- A versioned release candidate, rollback path, threat model, runbooks, release notes, and explicit production release decision exist

Total sprints: 11
