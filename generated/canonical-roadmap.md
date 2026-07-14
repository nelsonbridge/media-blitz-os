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
- Status: `superseded`
- Objective: Complete Publication 000001 through human approval, publication, receipts, and real feedback.
- Work items: BL-003
- Evidence records: 1

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

## Sprint 5 — Context-Bound Approval and Transaction Foundation

- ID: `NKS-SPR-005`
- Status: `complete`
- Objective: Establish one fail-closed approval lifecycle and reusable transaction foundation for canonical mutation, migration, reconciliation, disclosure, model use, transition, feedback, and work control.
- Work items: BL-005
- Evidence records: 3

Exit criteria:

- TEST authority cannot satisfy a PRODUCTION gate or produce a production effect
- Interrupted operations converge to one committed transaction, one recovered exact retry, or one documented rollback
- Approval reservation and consumption are durable, reconstructable, and exact-retry safe
- Ambiguous, stale, revoked, expired, mismatched, competing, or cross-context authority fails closed
- Every declared authority, interruption, retry, rollback, recovery, replay, tamper, and escalation path has automated coverage
- Immutable journals and terminal receipts bind the exact plan, transaction, approval, context, and output

## Sprint 6 — Enki Cognitive-Core Boundary and Generic Contracts

- ID: `NKS-SPR-006`
- Status: `complete`
- Objective: Formalize Enki as a product-neutral cognitive and reconciliation core with explicit constitutional boundaries, stable ports, fail-closed contract versioning, and uncertainty-preserving confidence rules.
- Work items: BL-006
- Evidence records: 4

Exit criteria:

- Core imports no product package and requires no complete Person, Organization, maturity, clinical, or publication ontology
- Core cannot silently substitute human objectives, priorities, choices, values, accountability, or outcomes
- Raw evidence and observations remain preservable for later reinterpretation
- Subject, evidence, observation, relationship, temporal, confidence, finding, disclosure, request, result, and receipt contracts are product-neutral
- Exact, backward, explicitly forward, unsupported, and ambiguous contract-version paths are automated and fail closed where required
- UNKNOWN confidence is deferred and unsupported confidence claims are rejected

## Sprint 7 — Generic Observation, Relationship, and State-Write Substrate

- ID: `NKS-SPR-007`
- Status: `complete`
- Objective: Implement one append-only, schema-governed substrate for observations, relationship assertions, and approval-bound generic state creation without subject-specific schema forks.
- Work items: BL-007
- Evidence records: 3

Exit criteria:

- PERSON, ORGANIZATION, and PROJECT use identical Enki observation, relationship, plan, journal, and receipt contracts
- State-write plans bind exact payload hash, subject, domain, context, known references, authority, and transaction
- Unknown references, subject leakage, domain mismatch, duplicate conflicts, tampering, and cross-plan replay fail closed
- Partial writes recover through the same consumed transaction without duplicate or rewritten state
- TEST state writes cannot reach production effects
- Machine-readable state-write paths have automated coverage and immutable evidence

## Sprint 8 — Human-State Compatibility, Authority, and Governed Migration

- ID: `NKS-SPR-008`
- Status: `complete`
- Objective: Project the temporal human-state reference implementation into the generic Enki substrate while preserving human agency, historical meaning, privacy, consent, purpose limitation, explicit expression origin, and recoverable migration authority.
- Work items: BL-008
- Evidence records: 4

Exit criteria:

- Historical human records are projected without rewriting canonical history or changing their original meaning
- Every migrated observation has an explicit expression-origin decision and attributable source lineage
- Consent, purpose, privacy, correction, retraction, expiration, revocation, and redaction protections fail closed
- Legacy Boolean model-feedback fields never become generic Enki authority
- Migration plans bind exact content hash, subject, policy, purpose, execution context, approval, and transaction
- Partial migration recovers by exact retry without duplicate observations, relationships, or weakened human protections

## Sprint 9 — Governed Reconciliation and Disclosure Separation

- ID: `NKS-SPR-009`
- Status: `complete`
- Objective: Make reconciliation and disclosure distinct governed operations while preserving temporal and contextual applicability, uncertainty, competing interpretations, privacy, consent, purpose limitation, audience boundaries, and user ownership of response.
- Work items: BL-009
- Evidence records: 4

Exit criteria:

- Deterministic eligibility classifies applicable, future, expired, retracted, superseded, historical, disputed, context-mismatched, and endpoint-ineligible state
- Reconciliation records findings without implying or widening disclosure
- Findings preserve observation, relationship, evidence, context, confidence, objective, priority, and interpretation lineage
- Subject disclosure requires subject request and every disclosure requires separately evaluated exact authority
- Purpose, audience, consent, sensitivity, privacy, redaction, expiration, and revocation rules fail closed and record surfaced, deferred, and withheld sets
- Finding and disclosure persistence recover by exact retry without duplicate effects, context escalation, or lost receipts

## Sprint 10 — Governed Transition and Conflict Engine

- ID: `NKS-SPR-010`
- Status: `complete`
- Objective: Implement the transactional engine for correction, refinement, supersession, retraction, reversal, context shift, confidence change, branching, merging, splitting, restriction, expansion, and deprecation while preserving history, uncertainty, authority, and deterministic recovery.
- Work items: BL-010
- Evidence records: 5

Exit criteria:

- Every supported transition binds exact before-and-after state hashes, subject, context, evidence, provenance, interpretation version, authority, execution context, transaction, and receipt
- Correction, refinement, supersession, retraction, reversal, expansion, restriction, confidence change, merge, split, and deprecation paths are explicit and versioned
- Invalid, cyclic, contradictory, stale, context-mismatched, or unauthorized transitions fail closed
- Branch, merge, overlap, contradiction, and competing-authority states remain reconstructable without manufacturing one falsely singular truth
- Interrupted transitions converge to one committed transition, one recovered exact retry, or one documented rollback
- Human-state regression tests pass through the generic engine without weakening human privacy, consent, correction, retraction, or authority controls

## Sprint 11 — Governed Interpretation and Capability-Isolated Model Use

- ID: `NKS-SPR-011`
- Status: `complete`
- Objective: Separate interpretation resolution, package construction, purpose and privacy policy, approval, persistence, receipt creation, revocation, and dispatch into independently testable governed steps while keeping prediction downstream and noncanonical.
- Work items: BL-011
- Evidence records: 5

Exit criteria:

- Interpretation resolution is deterministic across subject, domain, context, temporal applicability, transition state, authority, confidence, restrictions, and purpose
- Typed model-use directives are attributable, purpose-bound, versioned, and explicit about included transitions
- Retracted, expired, superseded, disputed, context-inapplicable, private, redacted, revoked, or unauthorized state cannot control downstream behavior
- TEST package generation, persistence, dispatch rehearsal, rollback, recovery, and receipts complete without transport capability or external effects
- PRODUCTION dispatch requires exact package and context hashes, recognized authority, privacy filtering, explicit transport, and production receipts
- Prediction, recommendation, and model output remain downstream and cannot mutate canonical Enki knowledge without a separately governed operation

## Sprint 12 — Forensic Reconstruction, Portability, and Governed Work Completion

- ID: `NKS-SPR-012`
- Status: `complete`
- Objective: Prove that every governed Enki operation, authority consumption, migration, state write, reconciliation, disclosure, transition, model use, feedback action, promotion, and work-control amendment can be reconstructed, moved, recovered, and completed without authority escalation or unsupported status claims.
- Work items: BL-012
- Evidence records: 5

Exit criteria:

- Every governed operation reconstructs to COMPLETE, INCOMPLETE, REPAIRABLE, ROLLED_BACK, or CONFLICT from immutable evidence
- Import, export, migration, replay, rollback, clean-room recovery, and disaster recovery preserve authority, execution context, hashes, lineage, validity, consumption, and receipts
- Corrupt, stale, unsupported, cross-context, or privilege-escalating recovery fails closed
- Filesystem and GitHub adapters exhibit equivalent behavior for their declared shared contract surface, with unsupported differences recorded and denied
- Governed work-control amendments bind sprint and work-item status changes to exact qualifying evidence and remain reconstructable
- No sprint or work item can become complete without qualifying implementation, path-coverage, validation, and authority evidence

## Sprint 13 — Integrated Internal TEST Proof and Enki Release Candidate

- ID: `NKS-SPR-013`
- Status: `planned`
- Objective: Execute repeated end-to-end internal TEST loops across Enki capabilities and downstream-consumer scenarios, including the complete publication-shaped proof of concept through no-effect adapters, then produce a versioned, reconstructable, rollback-capable Enki release candidate for an explicit release decision.
- Work items: BL-013
- Evidence records: 0

Exit criteria:

- At least two complete adaptive TEST loops pass across different subject classes, including the mandatory publication-shaped POC lane and at least one nonpublication lane
- The publication POC exercises exact content, visuals, configuration, identity, byline, brand, channel, review, TEST approval, package construction, no-effect distribution, TEST receipts, simulated observation, feedback, calibration, rollback, recovery, tamper, replay, and deterministic reconstruction
- SYNTHETIC/TEST, REPLAY/TEST, and controlled REAL/TEST feedback remain distinguishable, attributable, deduplicated, routed, dispositioned, auditable, replayable, and incapable of satisfying production gates
- Every declared success, denial, invalid-input, stale-input, duplicate, conflict, interruption, retry, rollback, recovery, replay, tamper, zero-response, and privilege-escalation path has automated coverage
- Chaos drills recover without duplicate effects, partial authority, unexplained state, audience widening, context escalation, or production effects
- A hash-bound calibration report, threat model, runbooks, limitations, rollback package, release notes, exact evidence manifests, and versioned Enki release candidate exist for an explicit human release decision

Total sprints: 13
