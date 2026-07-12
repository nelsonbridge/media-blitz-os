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

## Sprint 5 — Journaled promotion transaction

- ID: `NKS-SPR-005`
- Status: `planned`
- Objective: Make canonical promotion recoverable, atomic or journaled, idempotent, and receipted.
- Work items: BL-005
- Evidence records: 0

Exit criteria:

- Interrupted promotion is recoverable
- Partial state cannot persist
- Immutable promotion receipts exist

## Sprint 6 — Temporal human-state reference implementation

- ID: `NKS-SPR-006`
- Status: `planned`
- Objective: Productionize temporal human state on the Sprint 5 journal, receipt, recovery, and audit foundation before generalizing it into Governed Adaptive Knowledge.
- Work items: BL-006
- Evidence records: 0

Exit criteria:

- Human-state creation, transition, policy, revocation, and model-feedback operations are journaled and receipted
- Privacy classification, consent, purpose scope, redaction, expiration, and revocation fail closed
- CLI commands, canonical collections, generated views, authority manifest, and forensic audit are integrated
- Behavior evaluation fixtures prove that current, contextual, uncertain, retracted, and superseded states are handled correctly

## Sprint 7 — Governed Adaptive Knowledge state substrate

- ID: `NKS-SPR-007`
- Status: `planned`
- Objective: Introduce generic subject, domain, and KnowledgeState contracts on the journaled mutation foundation while retaining stricter human-agency policy overlays.
- Work items: BL-007
- Evidence records: 0

Exit criteria:

- Generic Subject, Domain, and KnowledgeState records exist with explicit context, confidence, validity, provenance, authority, sensitivity, and lineage
- The substrate supports humans and at least two nonhuman subject classes without schema forks
- Knowledge-state creation is journaled, receipted, recoverable, audited, and represented in deterministic views
- Human consent, privacy, and self-declaration protections remain stricter than generic entity policies

## Sprint 8 — Governed transition and conflict engine

- ID: `NKS-SPR-008`
- Status: `planned`
- Objective: Apply typed knowledge-state transitions transactionally while preserving history, authority, branch semantics, and conflict visibility.
- Work items: BL-008
- Evidence records: 0

Exit criteria:

- Correction, refinement, expansion, restriction, supersession, reversal, retraction, context shift, confidence change, merge, split, and deprecation rules are enforced
- Transitions are journaled, receipted, idempotent, recoverable, and linked to exact before-and-after state hashes
- Cycle, overlap, branch, merge, and conflicting-authority conditions fail closed or enter explicit review state
- The human-state subsystem uses the generic engine without weakening human-specific authority protections

## Sprint 9 — Interpretation resolution and model-use boundary

- ID: `NKS-SPR-009`
- Status: `planned`
- Objective: Resolve the current governed interpretation for a subject and context, then publish only purpose-limited, redactable, expirable, revocable, receipted model feedback.
- Work items: BL-009
- Evidence records: 0

Exit criteria:

- ResolveInterpretation deterministically returns applicable current state, lineage, confidence, uncertainty, restrictions, and behavioral authority
- Retracted, expired, superseded, context-inapplicable, or unauthorized state cannot control behavior
- Model-feedback packages are purpose-scoped, hash-bound, privacy-filtered, expirable, revocable, and immutably receipted
- Prediction remains a downstream consumer and cannot write probabilistic forecasts into canonical knowledge state

## Sprint 10 — Forensic reconstruction, migration, and adapter parity

- ID: `NKS-SPR-010`
- Status: `planned`
- Objective: Prove that canonical state, transitions, model-use decisions, receipts, and recovery can be reconstructed, migrated, exported, imported, and executed equivalently across supported adapters.
- Work items: BL-010
- Evidence records: 0

Exit criteria:

- Every canonical state creation, transition, revocation, interpretation package, and recovery action is reconstructable from journals and receipts
- Legacy human-state and canonical-source records migrate into current schemas through authorized, receipted transformations
- Clean-room offline export, import, verification, and disaster-recovery exercises pass without network or GitHub dependency
- Filesystem and GitHub adapters satisfy equivalent transaction, idempotency, recovery, and audit contracts
- Schema-version and forward/backward migration fixtures fail closed on unsupported or unauthorized changes

## Sprint 11 — Operational proof, hardening, and release candidate

- ID: `NKS-SPR-011`
- Status: `planned`
- Objective: Demonstrate repeated governed adaptive operation across human and nonhuman subjects, complete an explicitly approved external feedback cycle, exercise recovery under failure, and produce a versioned release candidate.
- Work items: BL-011
- Evidence records: 0

Exit criteria:

- At least two complete adaptive loops run across different subject classes, including one human-state loop and one nonhuman knowledge-state loop
- Publication 000001 or an equivalent explicitly approved external publication cycle produces publication, feedback, transition, and model-use receipts
- Chaos and interruption exercises recover without duplicate, unexplained, or partially authoritative state
- Security, privacy, behavior, portability, migration, and performance regressions pass as a release gate
- Threat model, known limitations, operational runbooks, rollback plan, versioned artifacts, and release decision are recorded

Total sprints: 11
