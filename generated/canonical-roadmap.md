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
- Status: `complete`
- Objective: Execute repeated end-to-end internal TEST loops across Enki capabilities and downstream-consumer scenarios, including the complete publication-shaped proof of concept through no-effect adapters, then produce a versioned, reconstructable, rollback-capable Enki release candidate for an explicit release decision.
- Work items: BL-013
- Evidence records: 6

Exit criteria:

- At least two complete adaptive TEST loops pass across different subject classes, including the mandatory publication-shaped POC lane and at least one nonpublication lane
- The publication POC exercises exact content, visuals, configuration, identity, byline, brand, channel, review, TEST approval, package construction, no-effect distribution, TEST receipts, simulated observation, feedback, calibration, rollback, recovery, tamper, replay, and deterministic reconstruction
- SYNTHETIC/TEST, REPLAY/TEST, and controlled REAL/TEST feedback remain distinguishable, attributable, deduplicated, routed, dispositioned, auditable, replayable, and incapable of satisfying production gates
- Every declared success, denial, invalid-input, stale-input, duplicate, conflict, interruption, retry, rollback, recovery, replay, tamper, zero-response, and privilege-escalation path has automated coverage
- Chaos drills recover without duplicate effects, partial authority, unexplained state, audience widening, context escalation, or production effects
- A hash-bound calibration report, threat model, runbooks, limitations, rollback package, release notes, exact evidence manifests, and versioned Enki release candidate exist for an explicit human release decision

## Sprint 14 — Reproducible Release and Supply-Chain Integrity

- ID: `NKS-SPR-014`
- Status: `complete`
- Objective: Make every Enki release candidate reproducible from a clean checkout and bind source, dependencies, workflows, artifacts, and attestations without introducing production credentials or self-issued trust.
- Work items: BL-014
- Evidence records: 6

Exit criteria:

- Clean-room build regenerates the exact declared release candidate and artifact hashes
- A machine-readable dependency inventory and SBOM cover runtime, test, workflow, and release tooling
- Source, workflow, dependency, and artifact provenance are bound in reproducible TEST attestations
- Dependency drift, artifact substitution, missing provenance, and secret leakage fail closed
- Release verification remains independent of production credentials and cannot issue a human release decision

## Sprint 15 — Performance, Capacity, and Resource Boundaries

- ID: `NKS-SPR-015`
- Status: `planned`
- Objective: Characterize Enki performance and resource behavior under governed synthetic workloads, publish explicit budgets and limits, and reject unsupported production-scale claims.
- Work items: BL-015
- Evidence records: 0

Exit criteria:

- Repeatable benchmarks cover transactions, state writes, reconciliation, transitions, model use, reconstruction, and export/import
- Latency, throughput, memory, storage growth, and recovery cost are reported by workload size
- Performance budgets and overload behavior are explicit and machine-tested
- Benchmarks preserve TEST isolation and contain no private or production data
- No benchmark result is represented as a production capacity guarantee

## Sprint 16 — Namespace, Tenant, and Subject Isolation

- ID: `NKS-SPR-016`
- Status: `planned`
- Objective: Enforce namespace, tenant, subject, domain, and audience isolation across every governed operation, export, import, recovery, and downstream-consumer boundary.
- Work items: BL-016
- Evidence records: 0

Exit criteria:

- Every governed record and operation carries an explicit namespace or tenant boundary
- Cross-tenant, cross-subject, cross-domain, and unauthorized audience access fails closed
- Export, import, migration, replay, and recovery preserve isolation boundaries
- Human consent, privacy, correction, retraction, and ownership protections remain stricter than generic tenant rules
- Isolation failures are reconstructable without exposing protected content

## Sprint 17 — Versioned Policy Lifecycle and Simulation

- ID: `NKS-SPR-017`
- Status: `planned`
- Objective: Govern policy creation, comparison, simulation, approval, activation, rollback, and retirement without rewriting historical decisions or widening authority.
- Work items: BL-017
- Evidence records: 0

Exit criteria:

- Policy bundles are immutable, versioned, attributable, context-bound, and hash-bound
- Policy simulation reports affected operations and decisions without mutating canonical state
- Activation and rollback require exact authority and produce receipts
- Historical decisions retain the policy version under which they were made
- TEST policy outcomes cannot activate or replace PRODUCTION policy

## Sprint 18 — Privacy-Preserving Observability and Operational Metrics

- ID: `NKS-SPR-018`
- Status: `planned`
- Objective: Provide actionable health, metrics, tracing, and diagnostic evidence while preventing canonical content, private human state, secrets, or unauthorized context from leaking through telemetry.
- Work items: BL-018
- Evidence records: 0

Exit criteria:

- Structured operation, transaction, recovery, and adapter telemetry uses stable identifiers and bounded metadata
- Metrics and traces expose no protected content, secrets, or disallowed personal data
- Health, saturation, failure, and recovery indicators support explicit TEST service objectives
- Telemetry loss, duplication, and correlation mismatch are detectable
- Observability cannot mutate canonical state or widen disclosure

## Sprint 19 — Retention, Archival, and Cryptographic Continuity

- ID: `NKS-SPR-019`
- Status: `planned`
- Objective: Govern retention, archival, tombstoning, legal or subject-driven restriction, and hash-algorithm continuity while preserving historical lineage and authority.
- Work items: BL-019
- Evidence records: 0

Exit criteria:

- Retention and archival policies are explicit, versioned, purpose-bound, and authority-bound
- Archival preserves verification, lineage, execution context, and receipt integrity
- Restriction or deletion requests produce governed tombstones or redactions without silently rewriting history
- Hash-algorithm migration preserves old verification and creates new receipted continuity evidence
- Expired, archived, restricted, or revoked records cannot control unauthorized downstream behavior

## Sprint 20 — Concurrency, Contention, and Distributed Recovery

- ID: `NKS-SPR-020`
- Status: `planned`
- Objective: Prove correct behavior under concurrent approvals, competing writes, duplicate delivery, out-of-order evidence, adapter interruption, and partition-shaped failure.
- Work items: BL-020
- Evidence records: 0

Exit criteria:

- Concurrent approval reservation and consumption permit at most one conflicting effect
- Duplicate, delayed, and out-of-order messages remain idempotent or fail closed
- Compare-and-swap contention and adapter interruption produce reconstructable outcomes
- Partition-shaped failures recover without split authority, duplicate effects, or lost receipts
- Filesystem and GitHub adapters satisfy the declared concurrency and recovery contract

## Sprint 21 — Stable Consumer API, CLI, and Compatibility Contract

- ID: `NKS-SPR-021`
- Status: `planned`
- Objective: Expose a stable product-neutral Enki service boundary through versioned APIs and CLI operations without allowing consumers to bypass governance or access repositories directly.
- Work items: BL-021
- Evidence records: 0

Exit criteria:

- Versioned request, response, error, receipt, pagination, and idempotency contracts are explicit
- CLI and API exercise the same application services and authority checks
- Unsupported, ambiguous, or incompatible versions fail closed
- Consumers cannot write canonical records or consume approvals through repository shortcuts
- Generated contract documentation and compatibility fixtures remain deterministic

## Sprint 22 — Downstream Product Boundary Proofs

- ID: `NKS-SPR-022`
- Status: `planned`
- Objective: Demonstrate that Media Blitz, Career Intelligence and Placement, and Personal Cognitive Continuity can consume Enki through scoped no-effect adapters without redefining the core or acquiring unauthorized authority.
- Work items: BL-022
- Evidence records: 0

Exit criteria:

- Each downstream suite uses an explicit consumer contract and no-effect TEST adapter
- Consumer-specific views and packages preserve provenance, context, privacy, and authority
- Products cannot write predictions, recommendations, publication decisions, or inferred preferences directly into canonical Enki state
- Cross-product data leakage, authority reuse, and audience widening fail closed
- At least one end-to-end TEST proof passes for each downstream suite

## Sprint 23 — Production-Readiness Review and Enki 1.0 Decision Package

- ID: `NKS-SPR-023`
- Status: `planned`
- Objective: Consolidate supply-chain, performance, isolation, policy, observability, retention, concurrency, compatibility, and consumer-boundary evidence into an independently reviewable Enki 1.0 decision package.
- Work items: BL-023
- Evidence records: 0

Exit criteria:

- All prior sprint evidence is assembled into one exact, versioned readiness manifest
- Adversarial, chaos, recovery, privacy, isolation, compatibility, and supply-chain campaigns pass or have explicit accepted findings
- Known limitations, production prerequisites, operating runbooks, rollback plans, and support boundaries are complete
- An independent review checklist records unresolved concerns without self-certification
- An Enki 1.0 candidate and human decision request exist without implying production approval

Total sprints: 23
