# Enki Core Refactor Plan — Sprints 5–9

> **Authority class: Class 3 — proposed execution plan.**
> This plan does not replace `records/sprints/*.json`, `records/work-items/*.json`, or generated canonical work-control views. Accepted changes must be promoted through the governed work-control process.

## Planning Principle

Do not create a parallel roadmap. Apply the Enki cognitive-core refactor as a controlled workstream across the already planned Sprint 5–9 sequence.

The sequence matters:

1. authority and transaction integrity;
2. human reference-path stabilization;
3. generic cognitive-core extraction;
4. relationship and transition reconciliation;
5. interpretation, stewardship, disclosure, and model-use separation.

No sprint may bypass provenance, governed approval, receipts, recovery, or state-authority controls to accelerate the refactor.

---

# Sprint 5 — Approval, Transaction, and Refactor Safety Foundation

Existing canonical sprint: `NKS-SPR-005`

## Refactor Objective

Establish the authority, transaction, and test-isolation foundation required to refactor human-state behavior without creating unreceipted state changes or allowing compatibility fields to become permanent authority.

## Required Work

### 5.1 Governed approval contract

Implement the accepted ADR-0001 concepts:

- `ExecutionContext`
- `ApprovalGrant`
- action, subject, content-hash, authority-class, validity, and consumption matching
- reservation and idempotent consumption
- context-bound transaction journal and receipts

### 5.2 Compatibility boundary for naked approval fields

Document and enforce that fields such as:

```text
approved_for_model_feedback
approved_by
```

are compatibility inputs only. They may not directly authorize generic state transition, disclosure, dispatch, or external effect.

### 5.3 Application and adapter ports

Introduce protocols for:

- observation repository;
- transition repository;
- approval evaluator;
- journal;
- receipt store;
- package store;
- model dispatch;
- clock and identifier generation where deterministic testing requires them.

Do not move package directories yet. First invert dependencies.

### 5.4 Characterization tests

Freeze current behavior for:

- observation hash validation;
- transition endpoint and temporal validation;
- stale, revoked, expired, denied, and mismatched policy rejection;
- current-state selection;
- transition inclusion;
- payload and receipt creation.

### 5.5 Model-feedback artifact authority decision

Classify `generated/model-feedback/` explicitly as one of:

- manifest-owned Class 2 projection;
- operational artifact with canonical receipt;
- transient dispatch payload;
- new governed artifact class.

Update manifest, storage path, and tests according to the decision.

## Exit Criteria

- No generic or production effect is authorized by a Boolean field.
- Existing human-state behavior is covered by characterization tests.
- Application services depend on ports rather than concrete filesystem adapters.
- TEST approval and adapters cannot produce PRODUCTION effects.
- Model-feedback artifact authority is explicit and verifiable.
- Interrupted operations converge to a committed transaction or documented rollback.

## Primary Risks

- Refactor work begins before approval semantics stabilize.
- Compatibility inputs accidentally remain authoritative.
- Generated-output ownership remains ambiguous.

---

# Sprint 6 — Human Reference Path Behind Stable Boundaries

Existing canonical sprint: `NKS-SPR-006`

## Refactor Objective

Preserve the temporal human-state implementation as the first strict overlay while separating its human-specific protections from the generic mechanics that Enki core will later reuse.

## Required Work

### 6.1 Human overlay contracts

Retain explicit human protections for:

- subject declaration;
- consent;
- correction;
- retraction;
- privacy classification;
- purpose limitation;
- redaction;
- expiration;
- revocation;
- production model-use authority.

### 6.2 Clarify observation and lineage semantics

Remove ambiguity between:

- an observation that supersedes another;
- an observation that has been superseded;
- current temporal applicability;
- relationship lineage.

Move directional change into transition or lineage records where practical.

### 6.3 Structured confidence assertion

Replace unstructured confidence strings in the new path with an extensible contract carrying:

- confidence type;
- asserted value or qualitative level;
- source;
- basis;
- method;
- context;
- applicable time;
- uncertainty notes.

Do not introduce a universal maturity, coherence, or calibration score.

### 6.4 Separate publication responsibilities

Refactor `PublishHumanStateFeedback` into composable services:

- resolve current human interpretation;
- evaluate approval and purpose;
- evaluate disclosure;
- build package;
- record receipt;
- dispatch through context-bound adapter.

### 6.5 Development history as observations

Represent longitudinal development through evidence-backed findings such as:

- change in model-to-reality alignment;
- change in objective progress;
- change in priority-to-decision alignment;
- recurring or resolved divergence;
- changed context or constraints.

Do not assign a universal developmental destination.

## Exit Criteria

- The human path runs entirely through Sprint 5 ports, journals, approvals, and receipts.
- Human authority and privacy remain stricter than future generic subject rules.
- Observation, relationship, and lineage semantics are unambiguous.
- Internal reconciliation and external publication are distinct operations.
- Development is recorded longitudinally without a maturity rank.
- No clinical or HIPAA-adjacent individual maturity classification is required.

## Primary Risks

- Generic extraction weakens human self-declaration or correction rights.
- Product-specific Person Object fields leak into the human overlay.
- Development tracking becomes covert psychological ranking.

---

# Sprint 7 — Enki Cognitive Core and Generic Reconciliation Contracts

Existing canonical sprint: `NKS-SPR-007`

## Refactor Objective

Generalize the proven human reference path into an entity-neutral cognitive kernel without making the Person Object, Organization Object, or any product ontology the core domain model.

## Required Work

### 7.1 Generic contracts

Introduce versioned contracts behind stable interfaces for:

- `SubjectRef`
- `Observation`
- `Context`
- `EvidenceRef`
- `ProvenanceRef`
- `ConfidenceAssertion`
- `TemporalApplicability`
- `RelationshipAssertion`
- `ReconciliationFinding`
- `Interpretation`
- `DisclosureDecision`
- `ApprovalApplicability`
- `ReceiptRef`

Names are provisional until proven by implementation. Compatibility and versioning matter more than vocabulary purity.

### 7.2 Human compatibility adapters

Map current human-state records to generic contracts without rewriting canonical history.

Prove semantic parity for:

- current and historical state;
- conditional and context-specific state;
- disputed, tentative, unresolved, retracted, expired, and superseded state;
- subject declaration versus governed inference;
- model-use approval and revocation.

### 7.3 Nonhuman reference subjects

Exercise the generic contracts with at least two nonhuman subject classes, for example:

- organization;
- project, publication, strategy, or capability.

The purpose is to prove that core contracts do not encode person-specific assumptions.

### 7.4 Bounded-context dependency tests

Add automated architecture tests asserting:

- core imports no product package;
- core does not require a complete Person or Organization object;
- human overlays may depend on core, not vice versa;
- product modules cannot become alternate owners of reconciliation truth;
- adapters implement ports and do not leak into domain contracts.

### 7.5 Ontology escape hatches

Protect the working relationship/correspondence hypothesis by:

- storing raw observations and evidence;
- versioning reconciliation logic;
- permitting new relationship types without schema forks;
- avoiding inheritance-heavy subject hierarchies;
- supporting reinterpretation from preserved source state.

## Exit Criteria

- One human and at least two nonhuman subjects use the same generic core contracts.
- Human overlays preserve stronger authority and privacy protections.
- No product ontology is required by core.
- Reconciliation findings are versioned, attributable, contextual, and reconstructable.
- Core dependency direction is enforced in CI.
- The system can revise its interpretation model without destroying raw evidence or prior findings.

## Primary Risks

- Prematurely freezing “relationship” or “correspondence” as the only possible ontology.
- Over-generalization produces abstractions too weak to enforce real constraints.
- Human semantics are lost during compatibility mapping.

---

# Sprint 8 — Relationship, Transition, and Reconciliation Engine

Existing canonical sprint: `NKS-SPR-008`

## Refactor Objective

Implement governed reconciliation across observations and relationships while preserving competing interpretations, temporal applicability, authority, and user ownership of choices.

## Required Work

### 8.1 Reconciliation pipeline

Implement explicit stages:

```text
Ingest observations
Validate provenance and applicability
Resolve relevant context
Identify relationship assertions
Generate candidate interpretations
Preserve competing hypotheses
Produce reconciliation findings
Evaluate disclosure separately
```

### 8.2 Divergence as relationship state

Represent objective-behavior, belief-evidence, priority-decision, prediction-outcome, and claim-practice divergence as manifestations of the same generic relationship structure.

Do not assume divergence must be reduced. Enki identifies and explains it; the user owns whether to act.

### 8.3 Transition engine

Support governed correction, refinement, expansion, restriction, supersession, reversal, retraction, context shift, confidence change, merge, split, and deprecation.

Every transition must bind:

- exact before and after hashes;
- subject and context;
- evidence and provenance;
- approval and execution context;
- interpretation version;
- transaction and receipt.

### 8.4 Longitudinal development findings

Compare current and prior states to answer:

- How closely do current actions and claims align relative to prior periods?
- Is the model more or less aligned with observable reality?
- Are decisions accelerating or impeding stated objectives?
- Do decisions align with stated priorities?
- Which contextual changes explain the movement?

### 8.5 Contradiction and uncertainty handling

Preserve:

- unresolved contradiction;
- disputed interpretations;
- insufficient evidence;
- context-dependent conclusions;
- changed constraints;
- minority but credible interpretations.

Do not collapse uncertainty merely to produce a single answer.

## Exit Criteria

- Reconciliation is a first-class governed operation, not an incidental filter inside publication.
- Divergence is represented without moral ranking or compulsory correction.
- Competing interpretations and uncertainty remain visible and reconstructable.
- Development findings are evidence-backed and longitudinal.
- Transitions are journaled, approval-bound, recoverable, and receipted.
- Human and nonhuman reference paths use the same engine without weakening human protections.

## Primary Risks

- Reconciliation becomes disguised recommendation or value prescription.
- A single interpretation is chosen prematurely.
- Development metrics become a vanity score.

---

# Sprint 9 — Stewardship, Disclosure, and Context-Bound Model Use

Existing canonical sprint: `NKS-SPR-009`

## Refactor Objective

Separate what Enki internally reconciles from what it surfaces or permits to influence a downstream model.

## Required Work

### 9.1 Continuous internal reconciliation

Allow reconciliation to consider all voluntarily entrusted, context-applicable information, including longitudinal history.

The user controls what is entrusted and may limit or revoke applicable scope.

### 9.2 Disclosure decision contract

Evaluate whether a finding should be surfaced using explicit factors:

- relevance to current objective or request;
- evidentiary confidence;
- user intent;
- potential decision value;
- temporal and contextual applicability;
- sensitivity and purpose limitation;
- applicable authority and consent;
- demonstrated developmental trajectory;
- risk of misrepresenting inference as fact.

The decision and basis must be receipted where consequential.

### 9.3 Typed model-use directives

Replace opaque Boolean behavioral instructions with typed, attributable directives bound to:

- source interpretation or finding;
- purpose and destination scope;
- applicable context;
- authority grant;
- execution context;
- validity and revocation;
- exact package hash.

### 9.4 Objective and accountability preservation

Tests must prove that Enki:

- does not supply user values;
- does not silently substitute objectives;
- distinguishes assessment from recommendation;
- leaves decisions and accountability with the user;
- allows the user to retain known inconsistency;
- does not claim success merely because the user changed behavior.

### 9.5 Product projection boundary

Define how consuming products may use Enki findings:

- Person Object and personal reflection;
- EOA/V8 organizational diagnostics;
- executive profile and social-profile management;
- publishing, career, or strategy products.

Products may add domain recommendations, but those recommendations must remain attributable to the product context rather than being represented as Enki core conclusions.

## Exit Criteria

- Internal reconciliation and external disclosure are separate, testable operations.
- Every consequential model-use package is purpose-, approval-, context-, and hash-bound.
- Typed directives replace opaque generic behavioral flags.
- Users retain objective, priority, choice, and outcome ownership.
- Product recommendations cannot masquerade as core reconciliation findings.
- TEST packages cannot dispatch externally or satisfy PRODUCTION evidence gates.

## Primary Risks

- “Potential value” becomes a pretext for intrusive disclosure.
- Downstream products turn findings into deterministic prescriptions.
- Social-profile use expands beyond the scope knowingly entrusted by the user.

---

# Cross-Sprint Definition of Done

The five-sprint refactor workstream is complete when:

1. Enki core is a governed cognitive and reconciliation kernel, not a Person, Organization, or product ontology.
2. The Person Object may use Enki as its cognitive core without forcing all Person data into core.
3. Observations, evidence, relationships, findings, interpretations, disclosures, and effects remain attributable.
4. User objectives and accountability are never silently transferred to Enki.
5. Human protections remain stricter than generic subject rules.
6. Relationship/correspondence remains replaceable as an implementation hypothesis.
7. Reconciliation uses all voluntarily entrusted, context-applicable information.
8. Disclosure is separately governed and explainable.
9. No universal psychological maturity, coherence, or calibration score is introduced.
10. Canonical state and generated projections continue to follow the repository authority model.

# Canonical Promotion Plan

After review and acceptance:

1. revise `records/sprints/NKS-SPR-005.json` through `NKS-SPR-009.json` using the governed writer;
2. revise `records/work-items/BL-005.json` through `BL-009.json` with the accepted refactor acceptance criteria;
3. regenerate `generated/canonical-roadmap.md` and `generated/canonical-backlog.md`;
4. regenerate the repository audit;
5. run authority verification and the full test suite;
6. preserve this document as the historical Class 3 proposal that informed the canonical changes.
