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
- Status: `complete`
- Objective: Characterize Enki performance and resource behavior under governed synthetic workloads, publish explicit budgets and limits, and reject unsupported production-scale claims.
- Work items: BL-015
- Evidence records: 5

Exit criteria:

- Repeatable benchmarks cover transactions, state writes, reconciliation, transitions, model use, reconstruction, and export/import
- Latency, throughput, memory, storage growth, and recovery cost are reported by workload size
- Performance budgets and overload behavior are explicit and machine-tested
- Benchmarks preserve TEST isolation and contain no private or production data
- No benchmark result is represented as a production capacity guarantee

## Sprint 16 — Zero-Cost Governed Boundary and Isolation Proof

- ID: `NKS-SPR-016`
- Status: `complete`
- Objective: Prove namespace, tenant, subject, domain, and audience isolation through product-neutral contracts, application enforcement, shared and physically separated local adapters, and exhaustive TEST fixtures without paid infrastructure, production credentials, or external services.
- Work items: BL-016
- Evidence records: 6

Exit criteria:

- Every governed record and operation carries an immutable namespace, tenant, subject, domain, audience, and execution-context boundary
- Authorization is evaluated against the complete boundary and cross-tenant, cross-subject, cross-domain, cross-audience, and TEST-to-PRODUCTION access fails closed
- Shared logical-store and physically separated local adapters exhibit equivalent denial behavior without network access or paid services
- Export, import, migration, replay, rollback, and recovery preserve exact boundaries and reject boundary tampering or escalation
- Errors, audits, receipts, and telemetry reconstruct isolation failures without exposing protected cross-boundary content
- Human consent, privacy, correction, retraction, revocation, and ownership protections remain stricter than generic tenant authorization
- A bounded local-process adversarial test covers forged boundary envelopes, path traversal, delayed or duplicated delivery, and mismatched recovery packages
- The complete Sprint 16 proof uses only repository-local code, Python standard-library capabilities, temporary storage, and existing zero-cost CI
- Cloud IAM, managed database isolation, network segmentation, per-tenant production keys, and external penetration certification remain explicitly unvalidated production prerequisites for Sprint 23

## Sprint 17 — Versioned Policy Lifecycle and Simulation

- ID: `NKS-SPR-017`
- Status: `complete`
- Objective: Govern policy creation, comparison, simulation, approval, activation, rollback, and retirement without rewriting historical decisions or widening authority.
- Work items: BL-017
- Evidence records: 5

Exit criteria:

- Policy bundles are immutable, versioned, attributable, context-bound, and hash-bound
- Policy simulation reports affected operations and decisions without mutating canonical state
- Activation and rollback require exact authority and produce receipts
- Historical decisions retain the policy version under which they were made
- TEST policy outcomes cannot activate or replace PRODUCTION policy

## Sprint 18 — Privacy-Preserving Observability and Operational Metrics

- ID: `NKS-SPR-018`
- Status: `complete`
- Objective: Provide actionable health, metrics, tracing, and diagnostic evidence while preventing canonical content, private human state, secrets, or unauthorized context from leaking through telemetry.
- Work items: BL-018
- Evidence records: 5

Exit criteria:

- Structured operation, transaction, recovery, and adapter telemetry uses stable identifiers and bounded metadata
- Metrics and traces expose no protected content, secrets, or disallowed personal data
- Health, saturation, failure, and recovery indicators support explicit TEST service objectives
- Telemetry loss, duplication, and correlation mismatch are detectable
- Observability cannot mutate canonical state or widen disclosure

## Sprint 19 — Retention, Archival, and Cryptographic Continuity

- ID: `NKS-SPR-019`
- Status: `complete`
- Objective: Govern retention, archival, tombstoning, legal or subject-driven restriction, and hash-algorithm continuity while preserving historical lineage and authority.
- Work items: BL-019
- Evidence records: 5

Exit criteria:

- Retention and archival policies are explicit, versioned, purpose-bound, and authority-bound
- Archival preserves verification, lineage, execution context, and receipt integrity
- Restriction or deletion requests produce governed tombstones or redactions without silently rewriting history
- Hash-algorithm migration preserves old verification and creates new receipted continuity evidence
- Expired, archived, restricted, or revoked records cannot control unauthorized downstream behavior

## Sprint 20 — Concurrency, Contention, and Distributed Recovery

- ID: `NKS-SPR-020`
- Status: `complete`
- Objective: Prove correct behavior under concurrent approvals, competing writes, duplicate delivery, out-of-order evidence, adapter interruption, and partition-shaped failure.
- Work items: BL-020
- Evidence records: 10

Exit criteria:

- Concurrent approval reservation and consumption permit at most one conflicting effect
- Duplicate, delayed, and out-of-order messages remain idempotent or fail closed
- Compare-and-swap contention and adapter interruption produce reconstructable outcomes
- Partition-shaped failures recover without split authority, duplicate effects, or lost receipts
- Filesystem and GitHub adapters satisfy the declared concurrency and recovery contract

## Sprint 21 — Stable Consumer API, CLI, and Compatibility Contract

- ID: `NKS-SPR-021`
- Status: `complete`
- Objective: Expose a stable product-neutral Enki service boundary through versioned APIs and CLI operations without allowing consumers to bypass governance or access repositories directly.
- Work items: BL-021
- Evidence records: 8

Exit criteria:

- Versioned request, response, error, receipt, pagination, and idempotency contracts are explicit
- CLI and API exercise the same application services and authority checks
- Unsupported, ambiguous, or incompatible versions fail closed
- Consumers cannot write canonical records or consume approvals through repository shortcuts
- Generated contract documentation and compatibility fixtures remain deterministic

## Sprint 22 — Downstream Product Boundary Proofs

- ID: `NKS-SPR-022`
- Status: `complete`
- Objective: Demonstrate that Media Blitz, Career Intelligence and Placement, and Personal Cognitive Continuity can consume Enki through scoped no-effect adapters without redefining the core or acquiring unauthorized authority.
- Work items: BL-022
- Evidence records: 5

Exit criteria:

- Each downstream suite uses an explicit consumer contract and no-effect TEST adapter
- Consumer-specific views and packages preserve provenance, context, privacy, and authority
- Products cannot write predictions, recommendations, publication decisions, or inferred preferences directly into canonical Enki state
- Cross-product data leakage, authority reuse, and audience widening fail closed
- At least one end-to-end TEST proof passes for each downstream suite

## Sprint 23 — Production-Readiness Review and Enki 1.0 Decision Package

- ID: `NKS-SPR-023`
- Status: `complete`
- Objective: Consolidate supply-chain, performance, logical-isolation, policy, observability, retention, concurrency, compatibility, consumer-boundary, and unresolved physical-isolation evidence into an independently reviewable Enki 1.0 decision package.
- Work items: BL-023
- Evidence records: 5

Exit criteria:

- All prior sprint evidence is assembled into one exact, versioned readiness manifest
- Adversarial, chaos, recovery, privacy, logical-isolation, compatibility, and supply-chain campaigns pass or have explicit accepted findings
- Known limitations, production prerequisites, operating runbooks, rollback plans, and support boundaries are complete
- Cloud IAM, production identity federation, managed database row-level isolation, network segmentation, per-tenant production key management, production secrets management, and independent penetration testing are explicitly validated or recorded as unresolved prerequisites
- No local TEST proof is represented as production infrastructure certification or multitenancy accreditation
- An independent review checklist records unresolved concerns without self-certification
- An Enki 1.0 candidate and human decision request exist without implying production approval

## Sprint 24 — Hosted Deployment Options and Split-Cloud Architecture Exploration

- ID: `NKS-SPR-024`
- Status: `complete`
- Objective: Produce an independently reviewable hosting-architecture decision package for Enki by evaluating single-cloud, split-cloud, and portability-preserving alternatives against governance, security, resilience, cost, operational, and migration requirements without implying production approval.
- Work items: BL-024
- Evidence records: 5

Exit criteria:

- A hosting options matrix compares single-cloud, provider-split cloud, control-plane/data-plane split, and relevant hybrid or portability-preserving patterns
- At least one single-cloud and one split-cloud reference architecture define compute, canonical data, identity, database isolation, key custody, secrets, network, observability, backup, disaster recovery, and support boundaries
- Threat, trust-boundary, failure-domain, data-flow, latency, egress, cost, operational complexity, lock-in, portability, privacy, compliance, and recovery tradeoffs are explicit for each finalist
- Each option maps its implications for the unresolved Sprint 23 production prerequisites without treating local TEST evidence as production validation
- Migration and rollback paths from the current repository-local TEST architecture are documented
- A cost model identifies expected ranges and major cost drivers without requiring paid deployment
- A recommended shortlist and explicit human hosting-decision criteria exist without default approval
- No production infrastructure is provisioned and Sprint completion does not constitute production hosting approval

## Sprint 25 — Hosted Multi-Finalist Validation Foundation

- ID: `NKS-SPR-025`
- Status: `complete`
- Objective: Convert the Sprint 24 shortlist and explicit human hosting direction into a deterministic, comparable, TEST-only validation program for all three finalists while preserving the zero-cost boundary, unresolved production prerequisites, and fail-closed external capability gates.
- Work items: BL-025
- Evidence records: 5

Exit criteria:

- A human decision records VALIDATE MULTIPLE FINALISTS without selecting or approving a production architecture
- CF-NATIVE, CF-NEON-R2, and GCP-NEON-R2 share one ordered validation phase contract and complete boundary-validation requirements
- The executable validation program is TEST-only and rejects production authority, production data, and production credentials
- All seven Sprint 23 production prerequisites remain explicit and unresolved for every finalist
- Hosted execution readiness requires provider TEST identity, provider TEST credentials, and teardown authority and otherwise fails closed as BLOCKED_EXTERNAL_CAPABILITY
- Automated tests cover the declared success and denial paths and pass in CI and runtime coverage
- No infrastructure is provisioned and no production-hosting approval is implied by Sprint completion

## Sprint 26 — CF-NATIVE Hosted TEST Validation

- ID: `NKS-SPR-026`
- Status: `blocked`
- Objective: Execute the complete governed hosted TEST validation program against the Cloudflare-native finalist and capture independently reviewable evidence without production data, production credentials, or production authority.
- Work items: BL-026
- Evidence records: 0

Exit criteria:

- Cloudflare TEST identity, TEST credentials, and teardown authority are available and scoped to non-production validation
- The CF-NATIVE finalist completes every ordered validation phase from preflight through teardown and reconstruction
- Hosted boundary isolation, transaction recovery, portability, privacy-preserving observability, failure injection, and quota behavior are evidenced
- No TEST approval, credential, or result becomes production authority
- The hosted TEST environment is destroyed and canonical TEST state remains reconstructable
- All evidence is hash-bound, attributable, and comparable to the later finalist validations

## Sprint 27 — CF-NEON-R2 Hosted TEST Validation

- ID: `NKS-SPR-027`
- Status: `planned`
- Objective: Execute the complete governed hosted TEST validation program against the Cloudflare Workers, Neon Postgres, and R2 finalist and measure the operational consequences of the provider split without implying production approval.
- Work items: BL-027
- Evidence records: 0

Exit criteria:

- Cloudflare and Neon TEST capabilities satisfy the same fail-closed preflight contract used for the other finalists
- Every ordered validation phase completes with comparable evidence
- Cross-provider transaction, failure, latency, egress, privacy, recovery, credential-revocation, and teardown behavior is explicit
- No provider failure can create duplicate canonical effects, split authority, or unexplained evidence loss
- The environment is destroyed and the final TEST state is reconstructable from governed exports
- Results remain TEST evidence and cannot satisfy unresolved production-control prerequisites

## Sprint 28 — GCP-NEON-R2 Hosted TEST Validation

- ID: `NKS-SPR-028`
- Status: `planned`
- Objective: Execute the complete governed hosted TEST validation program against the Cloud Run, Neon Postgres, and R2 finalist and measure whether lower runtime adaptation cost justifies the additional three-provider operational and trust complexity.
- Work items: BL-028
- Evidence records: 0

Exit criteria:

- Google Cloud, Neon, and Cloudflare TEST capabilities satisfy the common fail-closed hosted preflight contract
- Every ordered validation phase completes with evidence comparable to the other finalists
- Three-provider identity, secret, latency, egress, quota, failure, observability, recovery, and teardown behavior is explicit
- The current Python service boundary remains governed and consumers cannot bypass Enki application services
- The environment is destroyed and final TEST state reconstructs from governed exports
- Results remain non-production evidence and cannot promote unresolved production controls

## Sprint 29 — Cross-Finalist Comparative Evaluation

- ID: `NKS-SPR-029`
- Status: `planned`
- Objective: Convert the three hosted TEST campaigns into one evidence-bound, independently reviewable comparative evaluation that preserves uncertainty and failed evidence while making architecture tradeoffs explicit for a later human hosting decision.
- Work items: BL-029
- Evidence records: 0

Exit criteria:

- All finalist campaigns are evaluated through one deterministic comparison contract
- Measured TEST evidence, provider documentation, assumptions, and unresolved findings remain distinct
- Security, governance, resilience, performance, cost, egress, portability, complexity, recovery, privacy, and support tradeoffs are explicit
- Incomplete or failed evidence cannot be silently scored as success
- Production prerequisites remain unresolved unless separately validated with production-scope evidence
- The package produces a recommendation, disqualifiers, confidence, limitations, and rollback implications without issuing a hosting decision

## Sprint 30 — Hosting Direction and Production-Control Validation Decision Package

- ID: `NKS-SPR-030`
- Status: `planned`
- Objective: Assemble the complete hosted TEST evidence, comparative findings, unresolved production-control requirements, operational obligations, migration and rollback consequences, and explicit decision options into an independently reviewable package for the next human hosting-direction decision.
- Work items: BL-030
- Evidence records: 0

Exit criteria:

- The decision package binds the exact hosted validation and comparison evidence used
- Recommendation and human approval remain separate and no default selection is inferred
- Every unresolved production prerequisite has explicit evidence status and a sequenced validation path
- Migration, rollback, disaster recovery, support, cost, portability, and failure-domain obligations are explicit
- Decision options include select, defer, request more evidence, and reject
- No production infrastructure or production authority is created without a later explicit human production-hosting decision

## Sprint 31 — Canonical Schema and Temporal Authority Hardening

- ID: `NKS-SPR-031`
- Status: `complete`
- Objective: Align the canonical record model with the corrected nine-layer architecture by making historical truth, current authority, effective time, recorded time, supersession, revocation, consent, policy validity, and migration semantics explicit across governed record families.
- Work items: BL-031
- Evidence records: 5

Exit criteria:

- Canonical record families distinguish historical truth from current authority without rewriting history
- Recorded, effective, superseded, revoked, consumed, and authority-valid temporal states are explicit where applicable
- Approval, consent, policy, transition, reconciliation, disclosure, transaction, retention, conflict, and recovery records share compatible temporal semantics
- Schema evolution and migration preserve exact lineage and deterministic reconstruction
- Invalid temporal overlap, authority ambiguity, and unsupported supersession fail closed
- Automated regression tests prove historical and current-authority views remain distinguishable

## Sprint 32 — Governed Retrieval, Projection, and Model Gateway

- ID: `NKS-SPR-032`
- Status: `complete`
- Objective: Deliver governed knowledge retrieval, temporal projection, semantic access boundaries, and provider-neutral model-use orchestration without allowing projections or model output to become canonical authority.
- Work items: BL-032
- Evidence records: 5

Exit criteria:

- Consumers can query current-authority and historical views through explicit, distinguishable contracts
- Structured and semantic retrieval preserve tenant, subject, domain, audience, privacy, and purpose boundaries
- Projection and interpretation outputs remain noncanonical unless promoted through a separate governed operation
- Model gateway requests are context-bound, provenance-filtered, policy-evaluated, receipted, replayable, and provider-neutral
- Model output cannot mutate canonical Enki state without a separate authorized transaction
- Pagination, error, stale-state, denial, replay, and leakage paths are automated and deterministic

## Sprint 33 — Hosted Downstream Consumer Integration

- ID: `NKS-SPR-033`
- Status: `complete`
- Objective: Integrate Media Blitz, Career Intelligence and Placement, and Personal Cognitive Continuity through stable governed Enki consumer contracts while preserving independent product boundaries and stricter human-state protections.
- Work items: BL-033
- Evidence records: 5

Exit criteria:

- All three product suites consume Enki through versioned consumer boundaries rather than direct canonical persistence
- Media Blitz exercises governed source retrieval, package construction, publication-shaped TEST delivery, feedback, and calibration without direct Enki mutation
- Career Intelligence exercises governed professional-state, evidence, opportunity, and role-fit projections with explicit external-action approval
- Personal Cognitive Continuity exercises history, preferences, decisions, correction, retraction, consent, privacy, and temporal authority with human controls stricter than generic tenant policy
- Cross-product purpose, audience, namespace, subject, and authority leakage fail closed
- All integrations remain TEST-only unless separately authorized for production effects

## Sprint 34 — Multi-Consumer Isolation and Platform Operations

- ID: `NKS-SPR-034`
- Status: `complete`
- Objective: Operate multiple independent Enki consumers concurrently and prove workload isolation, purpose limitation, shared-knowledge boundaries, contention handling, telemetry, incident response, portability, and recovery under coordinated TEST load.
- Work items: BL-034
- Evidence records: 5

Exit criteria:

- Media Blitz, Career Intelligence and Placement, and Personal Cognitive Continuity execute concurrently without cross-product authority or data leakage
- Tenant, namespace, subject, domain, audience, purpose, and execution-context isolation survive concurrent workloads
- Contention, duplicate work, delayed delivery, queue-shaped pressure, retry, rollback, and recovery preserve exact receipts and canonical authority
- Privacy-preserving telemetry identifies workload interference and incident conditions without exposing protected payloads
- One consumer failure cannot widen another consumer's authority or corrupt shared canonical state
- Portability and recovery exercises reconstruct multi-consumer TEST operation deterministically

## Sprint 35 — Selected Hosting Architecture Production-Control Validation Readiness

- ID: `NKS-SPR-035`
- Status: `complete`
- Objective: Prepare the selected hosting direction, or the unresolved shortlist if no selection has been made, for explicit production-control validation by defining exact control tests, evidence requirements, deployment prerequisites, rollback obligations, and stop conditions without manufacturing production evidence.
- Work items: BL-035
- Evidence records: 5

Exit criteria:

- Cloud IAM, production identity federation, managed database isolation, network segmentation, per-tenant key management, secrets management, and independent penetration testing each have explicit validation contracts
- TEST substitutes and production validations remain distinguishable and cannot satisfy each other's gates
- Selected-hosting control mappings identify provider responsibilities, Enki responsibilities, evidence owners, failure criteria, and rollback paths
- Unresolved hosting direction does not block provider-neutral control-contract implementation
- No production deployment is authorized by completion of this sprint
- A later validation run can fail closed on missing production capability rather than reopening architecture design

## Sprint 36 — Enki Hosted Release Candidate and Deployment Decision

- ID: `NKS-SPR-036`
- Status: `complete`
- Objective: Consolidate the hosted validation, canonical architecture, multi-consumer operation, zero-cost envelope, production-control readiness, portability, recovery, limitations, and exact evidence into a final hosted Enki release candidate and explicit human deployment decision package.
- Work items: BL-036
- Evidence records: 5

Exit criteria:

- The release candidate binds exact architecture, implementation, hosted TEST, multi-consumer, recovery, portability, performance, and security evidence
- Software readiness, hosted architecture validation, zero-cost operating envelope, and production deployment readiness are reported as separate conclusions
- Known limitations, unresolved production controls, support boundaries, runbooks, rollback plans, migration paths, and independent-review requirements are explicit
- No unresolved or failed evidence is represented as passing
- The package supports APPROVE, APPROVE WITH CONDITIONS, DEFER, and REJECT dispositions
- Human deployment authority remains required and is not self-issued by automation or model output

## Sprint 37 — Deployment Decision Resolution and Architecture Lock

- ID: `NKS-SPR-037`
- Status: `blocked`
- Objective: Convert an explicit human RC2 deployment disposition into a governed architecture baseline, or preserve the pending decision as a fail-closed blocker without inferring a hosting or production choice.
- Work items: BL-037
- Evidence records: 0

Exit criteria:

- An explicit human RC2 disposition is bound to the exact candidate hash before any architecture lock
- APPROVE, APPROVE WITH CONDITIONS, DEFER, and REJECT produce distinguishable governed outcomes
- No hosting provider or production architecture is inferred from TEST evidence or sprint completion
- Any approved conditions become explicit prerequisites with owners, evidence requirements, and stop conditions
- A defer or reject outcome preserves the validated software baseline and historical decision lineage
- Architecture lock, when authorized, identifies exact provider choices, optional services, responsibility boundaries, and rollback baseline

## Sprint 38 — Infrastructure-as-Code and Reproducible Environment Build

- ID: `NKS-SPR-038`
- Status: `planned`
- Objective: Implement the human-authorized hosted architecture as reproducible TEST infrastructure with deterministic creation, verification, teardown, and clean rebuild while preserving the zero-cost boundary until separately changed.
- Work items: BL-038
- Evidence records: 0

Exit criteria:

- The selected architecture is represented as versioned infrastructure definitions rather than hidden manual configuration
- TEST and later production environments have explicit configuration and authority separation
- Environment creation, verification, teardown, and clean rebuild are automated and deterministic
- Secrets are referenced through governed bindings and never committed to the repository
- Infrastructure drift and undeclared provider services fail closed
- The environment can be destroyed without losing reconstructable governed TEST state

## Sprint 39 — Hosted Identity, Tenancy, and Context Enforcement

- ID: `NKS-SPR-039`
- Status: `planned`
- Objective: Move Enki identity, tenant, subject, domain, audience, purpose, and execution-context boundaries into the authorized hosted runtime and validate least-privilege behavior adversarially.
- Work items: BL-039
- Evidence records: 0

Exit criteria:

- Hosted authentication and identity resolution bind exact Enki boundary context
- Cross-tenant, cross-subject, cross-domain, cross-audience, cross-purpose, and TEST-to-PRODUCTION escalation fail closed
- Scoped credentials, revocation, expiry, rotation, and forged-identity paths are validated
- Human-state controls remain stricter than generic tenant authorization
- Hosted denial evidence is privacy-preserving and reconstructable
- No TEST identity or credential can satisfy a production identity gate

## Sprint 40 — Physical Canonical Persistence and Migration

- ID: `NKS-SPR-040`
- Status: `planned`
- Objective: Implement the definitive hosted mapping for canonical structured state and temporal authority, including schema migration, indexes, transactions, reservations, receipts, conflicts, and reconstruction.
- Work items: BL-040
- Evidence records: 0

Exit criteria:

- The physical schema preserves historical truth, current authority, recorded time, effective time, and authority-valid time
- Canonical writes remain reachable only through governed mutation paths
- Transactions, reservations, receipts, conflicts, and temporal lineage are physically reconstructable
- Schema migration preserves identifiers, hashes, authority, and historical lineage
- Cross-tenant physical isolation matches the selected production-control contract
- Rollback restores the last validated schema and canonical fingerprint

## Sprint 41 — Evidence and Object Plane

- ID: `NKS-SPR-041`
- Status: `planned`
- Objective: Implement the hosted evidence, package, manifest, export, backup, and recovery object plane while preserving cryptographic linkage to structured governed state and provider portability.
- Work items: BL-041
- Evidence records: 0

Exit criteria:

- Evidence objects and canonical structured state remain distinct but hash-linked
- Publication, model-use, audit, export, backup, and recovery packages use deterministic manifests
- Retention, tombstone, archival, and deletion semantics preserve governed history
- Object corruption, missing objects, manifest tampering, and orphan evidence fail closed
- Provider-specific object storage does not become canonical authority
- Portable export and clean-room import reconstruct exact evidence relationships

## Sprint 42 — Hosted Governed Execution Runtime

- ID: `NKS-SPR-042`
- Status: `planned`
- Objective: Deploy and validate the complete Enki governed mutation path in the authorized hosted runtime so no canonical mutation can bypass context, authority, policy, provenance, reservation, journaling, receipts, and recovery.
- Work items: BL-042
- Evidence records: 0

Exit criteria:

- Hosted requests resolve exact context before authority or mutation evaluation
- Every canonical mutation passes authority, policy, provenance, reservation, journal, and receipt controls
- Duplicate, delayed, interrupted, and conflicting operations converge or fail closed
- Hosted retries cannot duplicate canonical effects or consume authority twice
- Failure recovery reconstructs exact state and evidence lineage
- TEST execution remains incapable of production effects unless separately authorized

## Sprint 43 — Hosted Retrieval and Knowledge Access

- ID: `NKS-SPR-043`
- Status: `planned`
- Objective: Operationalize current-authority, historical, contextual, structured, semantic, and projection access against the hosted governed state without leaking authority or converting projections into canonical truth.
- Work items: BL-043
- Evidence records: 0

Exit criteria:

- Hosted consumers can explicitly request current-authority, historical, and as-of views
- Tenant, subject, domain, audience, purpose, privacy, and provenance filters are enforced server-side
- Structured and semantic retrieval remain deterministic within declared contracts
- Projections and interpretations remain noncanonical absent separate governed promotion
- Pagination, stale-state, denial, replay, and leakage paths are validated
- Model access continues through the governed provider-neutral model gateway

## Sprint 44 — Disaster Recovery, Portability, and Provider Exit

- ID: `NKS-SPR-044`
- Status: `complete`
- Objective: Prove that hosted Enki can be backed up, exported, reconstructed, restored, and migrated without permanent dependence on the selected provider combination or loss of authority semantics.
- Work items: BL-044
- Evidence records: 5

Exit criteria:

- Structured state and object evidence have coordinated backup and recovery procedures
- Point-in-time and clean-room reconstruction preserve exact canonical fingerprints and receipts
- Provider outage and provider-exit scenarios have tested recovery paths
- Exports remain open, deterministic, hash-bound, and independently verifiable
- Rollback and migration preserve authority, lineage, policy, consent, and temporal semantics
- Provider loss cannot silently convert projections, caches, or replicas into canonical authority

## Sprint 45 — Production-Control Implementation

- ID: `NKS-SPR-045`
- Status: `planned`
- Objective: Implement and validate the seven Sprint 35 production-control contracts against the human-authorized hosted architecture using qualifying production-scope evidence and independent assessment where required.
- Work items: BL-045
- Evidence records: 0

Exit criteria:

- Cloud IAM is validated with least-privilege and denial evidence
- Production identity federation is validated with forged, expired, revoked, and wrong-audience denial paths
- Managed database row-level isolation and network segmentation are validated in production scope
- Per-tenant production keys and production secrets management are validated for rotation, revocation, and leakage resistance
- Independent penetration testing is performed by an authorized independent assessor
- Every control is classified VALIDATED, PARTIALLY VALIDATED, UNVALIDATED, or EXTERNALLY REQUIRED without self-certification

## Sprint 46 — Operational Observability and Incident Management

- ID: `NKS-SPR-046`
- Status: `complete`
- Objective: Provide production-shaped operational visibility, incident reconstruction, health monitoring, alerting, and privacy-preserving diagnostics without exposing protected knowledge or allowing observability to mutate canonical state.
- Work items: BL-046
- Evidence records: 5

Exit criteria:

- Metrics, traces, structured logs, and health indicators use bounded metadata and stable correlation identifiers
- Protected canonical content, secrets, and disallowed personal data never enter telemetry
- Queue pressure, saturation, latency, failure, retry, recovery, and provider degradation are observable
- Incident records reconstruct exact operation, authority, evidence, and recovery lineage without widening disclosure
- Telemetry loss, duplication, ordering gaps, and correlation mismatch are detectable
- Observability and incident tooling cannot mutate canonical state or authorize recovery effects

## Sprint 47 — Multi-Product Hosted Integration

- ID: `NKS-SPR-047`
- Status: `planned`
- Objective: Run Media Blitz, Career Intelligence and Placement, and Personal Cognitive Continuity concurrently against hosted Enki through stable governed consumer boundaries without cross-product data, purpose, or authority leakage.
- Work items: BL-047
- Evidence records: 0

Exit criteria:

- All three product suites use versioned hosted Enki consumer contracts
- Concurrent hosted workloads preserve tenant, subject, domain, audience, purpose, and product isolation
- Media Blitz publication paths, Career external-action paths, and Personal Cognitive Continuity human controls remain independently governed
- One product failure or overload cannot widen another product authority or corrupt canonical state
- Cross-product observability remains privacy-preserving and attributable
- No downstream product acquires direct canonical persistence or approval-consumption capability

## Sprint 48 — Enki 1.0 Operational Release and Human Launch Decision

- ID: `NKS-SPR-048`
- Status: `planned`
- Objective: Assemble the complete operational evidence package for Enki 1.0, report software, hosted platform, production controls, operations, cost, recovery, portability, and multi-consumer readiness separately, and request an explicit human launch decision.
- Work items: BL-048
- Evidence records: 0

Exit criteria:

- The release package binds exact software, architecture, hosting, security, identity, canonical data, evidence, recovery, portability, multi-consumer, operations, and cost evidence
- Hosted platform readiness and production-control readiness are not inferred from software TEST success
- Known limitations, accepted findings, support obligations, rollback, migration, and independent-review requirements are explicit
- Missing, failed, deferred, or conditional evidence remains distinguishable
- The package supports APPROVE, APPROVE WITH CONDITIONS, DEFER, and REJECT
- Only explicit human launch authority can authorize operational production launch

Total sprints: 48
