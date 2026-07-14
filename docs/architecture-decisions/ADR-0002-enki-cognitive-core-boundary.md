# ADR-0002: Enki Cognitive Core, Reconciliation Boundary, and Product Separation

> **Authority class: Class 3 — proposed architecture decision.**
> This document does not establish canonical implementation state. Canonical work records and generated projections remain authoritative.

- Status: Proposed
- Date: 2026-07-13
- Governing scope: Enki core, temporal human-state reference implementation, Governed Adaptive Knowledge generalization, and consuming product projections

## Context

The current repository contains a temporal human-state reference implementation that intentionally precedes a platform-neutral Governed Adaptive Knowledge substrate. During architecture review, several concepts from adjacent products were allowed to cross bounded contexts during emergent design:

- a Person Object;
- individual psychological or social-development models;
- the Erikson-derived organizational maturity model used by EOA/V8;
- executive profile management;
- broader organizational diagnostic and balanced-scorecard capabilities.

Those concepts were not invented by the implementation review. They are legitimate platform and product concepts, but they do not all belong to Enki core.

At the same time, Enki is not merely a service consumed by a Person Object. Enki is the cognitive and reconciliation core through which a Person Object—and potentially other governed entities—can examine the relationships among voluntarily entrusted observations, objectives, priorities, decisions, behavior, evidence, and outcomes.

The repository therefore needs an explicit boundary before the human-state reference implementation is generalized.

## Decision

Enki core will be treated as a governed cognitive kernel whose primary discipline is reconciliation.

Enki core:

1. ingests voluntarily entrusted observations and records;
2. examines their provenance, context, temporal applicability, and relationships;
3. reconciles claims, evidence, objectives, priorities, decisions, behavior, and outcomes;
4. records findings and historical revisions without erasing prior state;
5. shares relevant, sufficiently supported findings through a separately governed disclosure boundary; and
6. informs users without assuming ownership of their objectives, priorities, choices, values, or outcomes.

Enki core does **not**:

- prescribe what a user ought to value;
- provide formulas for personal success or ethical development;
- define a mandatory path toward coherence;
- make the user’s choices;
- assume ownership of a person’s development or becoming;
- convert observed inconsistency into a moral judgment;
- require the user to resolve a surfaced divergence;
- silently substitute a system objective for a user objective.

A user may retain, revise, reorder, or reject objectives and priorities. A user may knowingly remain inconsistent with a stated identity or objective. Enki’s obligation is accurate examination and representation, not compliance.

## Core Constitutional Boundary

The following candidate invariants govern the proposed refactor:

1. **User-owned objectives.** Users define what they are attempting to achieve. Enki evaluates correspondence with reality; it does not supply the objective.
2. **User-owned accountability.** Enki does not absorb responsibility for choices or outcomes by prescribing values or decisions.
3. **Attributable history.** Claims, decisions, changes, and model-use effects remain historically attributable through provenance and lineage.
4. **No hidden objective substitution.** Enki must not quietly optimize for a different goal than the one the user supplied.
5. **Continuous internal reconciliation.** Enki may reconcile all information voluntarily entrusted to the applicable context.
6. **Governed external disclosure.** Internal reconciliation does not require every inference to be surfaced. Disclosure is separately governed by relevance, confidence, user intent, potential value, applicable authority, and the user’s demonstrated developmental trajectory.
7. **No compulsory correction.** A surfaced divergence remains information. The user owns whether and how to respond.
8. **Context preservation.** Observations and findings remain bounded by domain, time, provenance, purpose, and applicable execution context.
9. **Relationship integrity.** The system preserves the relationships among evidence, claims, objectives, priorities, decisions, behavior, and outcomes without converting correlation into certainty.
10. **Core restraint.** Product-specific psychology, profile scoring, organizational maturity, and domain advice do not enter Enki core merely because multiple products may use them.

## Working Architectural Hypothesis

Relationships and correspondence are the strongest current abstraction for Enki’s reasoning substrate, but they remain a working hypothesis rather than an irreversible ontology.

The implementation must avoid building into a corner by:

- defining core contracts through ports and protocols rather than inheritance-heavy domain hierarchies;
- keeping subject and product identity outside the reconciliation kernel;
- allowing new relationship and evidence types without schema forks;
- preserving raw observations and provenance so future interpretations can be recomputed;
- versioning interpretation logic independently from stored evidence;
- avoiding a single scalar coherence, maturity, or calibration score.

## Bounded Contexts

### Enki Core

Candidate core concepts:

- Observation
- Subject reference
- Context
- Relationship or correspondence assertion
- Evidence reference
- Provenance
- Confidence assertion
- Temporal applicability
- Reconciliation finding
- Interpretation lineage
- Disclosure decision
- Approval applicability
- Receipt

### Platform Objects

Platform objects may include:

- Person
- Organization
- Project
- Artifact
- Conversation
- Objective
- Decision
- Outcome

Enki may operate across references to these objects without owning their complete domain models.

### Product Projections

Product-specific concepts remain outside Enki core, including:

- EOA/V8 organizational maturity diagnostics;
- Erikson-derived organizational maturity models;
- automated balanced-scorecard organizational review and planning;
- executive profile management;
- social-profile management and analysis;
- individual psychological maturity assessment;
- product-specific recommendations and pathways.

A Person Object may use Enki as its cognitive core while adding identity, relationships, credentials, roles, preferences, and other product-governed data.

## Privacy Boundary

The current product direction should remain on the non-clinical side of health-data regulation wherever practical.

The core may consider voluntarily supplied behavioral and social information, including user-authorized social-profile data, but it should not require clinical diagnosis or an individual psychological maturity classification.

Any product that crosses into health, clinical, or similarly sensitive inference must establish a separate bounded context, authority model, retention policy, disclosure policy, and legal review. Such a product must not silently expand Enki core’s data authority.

## Development

Development is not a maturity rank assigned by Enki. It is a longitudinal reconciliation question:

- How closely do current claims, decisions, and behavior align compared with prior periods?
- Is the user’s mental model more or less aligned with observable reality?
- Are decisions accelerating or impeding progress toward stated objectives?
- Do decisions reflect stated priorities?
- What changed, how did it change, and what evidence supports that conclusion?

Enki records the trajectory and basis of those observations. It does not declare a universal destination.

## Consequences

### Positive

- The temporal human-state implementation can remain a valid reference implementation without becoming the permanent generic ontology.
- The Person Object can retain Enki as its cognitive core without forcing person-specific concepts into the kernel.
- EOA/V8 and executive products can evolve independently without contaminating core contracts.
- Provenance, accountability, and historical reconstruction remain enforceable.
- The system can reconcile broad user context while applying restraint at disclosure time.

### Cost

- Existing human-specific classes require compatibility adapters before platform-neutral contracts replace them.
- Selection, reconciliation, approval, disclosure, packaging, and persistence responsibilities must be separated.
- Product teams must explicitly classify new concepts rather than allowing cross-product usefulness to imply core ownership.
- Existing Boolean approval and behavioral-directive fields require migration into governed contracts.

## Rejected Alternatives

### Make the Person Object the Enki core domain model

Rejected because it would bind the kernel to one subject class and encourage psychological, identity, and product concerns to enter core reasoning contracts.

### Remove the Person Object from the architecture

Rejected because the Person Object is a legitimate platform and product construct and may use Enki as its cognitive core.

### Treat all cross-product concepts as core abstractions

Rejected because emergent design leakage is evidence for review, not automatic admission into the kernel.

### Define a universal coherence or maturity score

Rejected because a scalar score would encourage score optimization, conceal context, and convert an examination tool into a normative ranking system.

### Reconcile only information from the current interaction

Rejected because Enki’s value depends on longitudinal context. Reconciliation may use all voluntarily entrusted, context-applicable information; disclosure remains separately governed.

## Required Follow-Up

1. Map the current repository to Enki core, platform, product, and infrastructure bounded contexts.
2. Introduce platform-neutral reconciliation contracts behind compatibility adapters.
3. Remove naked Boolean authority from the generic path in favor of Sprint 5 `ApprovalGrant` evaluation.
4. Split current feedback publication into interpretation resolution, stewardship/disclosure, packaging, and persistence services.
5. Define constitutional traceability from invariant to contract, service, test, and receipt.
6. Update canonical Sprint 5–9 records only through the governed work-control process after this proposal is accepted.
