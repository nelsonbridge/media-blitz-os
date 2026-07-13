# Enki Core Repository Assessment and Refactor Requirements

> **Authority class: Class 3 — architecture assessment and refactor proposal.**
> This document does not establish canonical implementation state. Canonical records and generated projections remain authoritative.

- Assessment date: 2026-07-13
- Repository: `nelsonbridge/media-blitz-os`
- Assessed branch baseline: `sandbox`
- Proposed refactor branch: `agent/enki-core-refactor`

## Scope Reviewed

This assessment is grounded in the current repository authority model, generated audit, roadmap records, and the implemented temporal human-state reference path, including:

- `README.md`
- `pyproject.toml`
- `docs/state-authority-model.md`
- `docs/architecture-decisions/ADR-0001-context-bound-approvals.md`
- `generated/state-authority-manifest.json`
- `generated/audit/repository-audit.json`
- `records/sprints/NKS-SPR-007.json`
- `records/work-items/BL-007.json`
- `src/nks/domain/human_state.py`
- `src/nks/application/human_state.py`
- `src/nks/adapters/human_state.py`

The repository audit reports 571 files, 152 canonical records, 86 Python files, 33 tests, and 9 schemas. The human-observation, human-transition, model-ingestion-policy, and model-feedback-receipt collections currently contain no canonical records. That makes this the appropriate point to refactor contracts before operational data creates migration pressure.

## Overall Assessment

The repository is not architecturally broken. Its present shape reflects a deliberate sequence:

1. establish provenance and canonicalization controls;
2. establish restricted canonical writing;
3. establish journaled and context-bound authority;
4. prove temporal human state as a reference implementation;
5. generalize the proven mechanism into Governed Adaptive Knowledge.

The required change is therefore a **boundary and responsibility refactor**, not a rewrite.

The existing human-state implementation contains useful primitives, but several responsibilities are fused inside a person-specific bounded context. Sprint 7 already intends to generalize them. The new Enki clarification sharpens what must become generic, what must remain human-specific, and what must remain product-specific.

## Principal Findings

### 1. Human-specific names currently carry platform-neutral concepts

`HumanStateObservation`, `HumanStateTransition`, and `JsonHumanStateRepository` combine two concerns:

- generic governed observation and transition mechanics;
- human-specific authority, privacy, and self-declaration rules.

The implementation is valid as a reference path, but direct reuse would make the generic substrate person-centric.

**Requirement:** Extract platform-neutral contracts and preserve the current classes as compatibility projections or human overlays until migration completes.

Candidate generic contracts:

```text
SubjectRef
Observation
ObservationContext
TemporalApplicability
RelationshipAssertion
Transition
EvidenceRef
ProvenanceRef
ConfidenceAssertion
ReconciliationFinding
Interpretation
DisclosureDecision
```

### 2. Boolean authority conflicts with the accepted approval direction

`HumanStateTransition` contains:

```text
approved_for_model_feedback: bool
approved_by: str | None
```

ADR-0001 explicitly rejects naked Boolean approval as sufficient authority. Sprint 5 plans governed `ApprovalGrant` evaluation bound to execution context, action, subject, content hash, authority class, validity, and consumption state.

**Requirement:** Treat the Boolean fields as temporary compatibility inputs only. The generic transition and model-use path must consume governed approval references and evaluation results.

### 3. The application service mixes five distinct operations

`PublishHumanStateFeedback.execute()` currently performs:

1. policy lookup and authorization checks;
2. temporal eligibility filtering;
3. current-state selection;
4. transition filtering;
5. model package construction, receipt creation, and persistence.

This makes future reconciliation and stewardship policy difficult to evolve independently.

**Requirement:** Split the operation into explicit services:

```text
ResolveInterpretation
EvaluateModelUseAuthority
EvaluateDisclosure
BuildModelUsePackage
RecordModelUseReceipt
DispatchModelUsePackage
```

The first four may operate in TEST without external effects. Dispatch must remain adapter-isolated and context-bound.

### 4. Reconciliation is implicit rather than first-class

The current implementation selects eligible observations and approved transitions, but it does not represent the reconciliation result as its own governed artifact.

This prevents the system from distinguishing:

- raw observations;
- asserted relationships;
- competing hypotheses;
- reconciliation findings;
- externally disclosed findings;
- downstream behavioral instructions.

**Requirement:** Add a versioned `ReconciliationFinding` or equivalent contract with explicit inputs, context, interpretation version, evidence, uncertainty, applicability, and lineage. Do not require the final name or structure to be irreversible; design behind ports and versioned schemas.

### 5. Observation status and lineage semantics need clarification

`HumanStateObservation` combines `temporal_status` with `supersedes_observation_id`. The validator requires `supersedes_observation_id` when the observation itself is marked `SUPERSEDED`, which can blur whether the record supersedes another observation or has itself been superseded.

**Requirement:** Move directional change semantics into explicit transition or lineage records. Observation records should state temporal applicability without ambiguously carrying both sides of a relationship.

### 6. Confidence is currently an unstructured string

Both observations and transitions use `confidence: str`. This preserves flexibility but cannot reliably distinguish:

- source confidence;
- system confidence;
- user-declared certainty;
- statistical confidence;
- qualitative uncertainty;
- confidence basis and calibration history.

**Requirement:** Introduce a structured, extensible confidence assertion rather than a universal numeric score. It must preserve basis, source, method, context, and uncertainty without forcing all confidence into one scale.

### 7. Behavioral instructions are opaque and unprovenanced

`ModelFeedbackPackage.behavioral_instructions` is a `dict[str, bool]`. This is convenient for the reference implementation but weak for governance.

**Requirement:** Replace opaque flags in the generic path with typed directives carrying:

- directive type;
- applicable subject and context;
- source finding or policy;
- purpose scope;
- authority reference;
- issued and expiry times;
- revocation state;
- interpretation version.

### 8. Concrete persistence is coupled into application services

Application services depend directly on `JsonHumanStateRepository` rather than a repository protocol or port.

**Requirement:** Define storage and receipt ports in the application boundary. Keep filesystem JSON as one adapter. This is necessary for clean-room, migration, database, and alternate-storage parity planned in later sprints.

### 9. Generated output ownership is ambiguous for model feedback

`JsonHumanStateRepository.save_feedback()` writes packages under `generated/model-feedback/`, while the authority manifest enumerates specific Class 2 projections and does not currently declare that path.

**Requirement:** Decide explicitly whether model-feedback packages are:

- Class 2 deterministic projections;
- operational artifacts with canonical receipts;
- transient dispatch payloads;
- or a separate governed artifact class.

Do not leave them under a directory whose authority convention implies deterministic generated state without manifest ownership and regeneration rules.

### 10. Product leakage must be classified, not erased

The Person Object, executive profile capabilities, EOA/V8 organizational maturity model, and organizational efficiency suite are valid concepts from adjacent product work. They are not mistakes and should not be deleted.

**Requirement:** Classify them into bounded contexts:

- Enki cognitive core;
- platform objects;
- human-specific authority overlay;
- EOA/V8 organizational diagnostics;
- executive/profile products;
- infrastructure.

Cross-product use is evidence for architectural review, not automatic promotion into core.

### 11. Individual psychological maturity is outside current desired scope

The organization-level Erikson-derived maturity model belongs to EOA/V8. An individual social-psychological maturity model could be built, but it would move the product toward clinical or health-adjacent privacy obligations that are not currently desired.

**Requirement:** Keep individual psychological maturity classification out of Enki core and the current Person Object path. Development may be represented as observed longitudinal correspondence, not as a clinical or universal maturity rank.

### 12. Development needs a longitudinal, evidence-backed representation

Development should answer:

- Is the user’s current mental model more or less aligned with observable reality than before?
- Are decisions accelerating or impeding stated objectives?
- Do decisions align with stated priorities?
- What changed, how did it change, and what evidence supports the finding?

**Requirement:** Represent development as a history of attributable findings and changes. Do not collapse it into a scalar maturity or coherence score.

## Proposed Target Boundaries

```text
src/nks/
  core/
    observation/
    relationship/
    reconciliation/
    interpretation/
    provenance/
    confidence/
    approvals/
    stewardship/
    receipts/

  platform/
    subjects/
    objectives/
    decisions/
    outcomes/
    artifacts/

  overlays/
    human/
      observations/
      consent/
      correction/
      privacy/
      model_use/

  products/
    eoa/
    v8/
    executive_profile/
    profile_management/

  adapters/
    filesystem/
    model_dispatch/
    external_publish/
```

This is a directional module map, not a required immediate directory migration. The first refactor should establish contracts and dependency rules before moving files.

## Dependency Rules

1. Core must not import product modules.
2. Core must not require a complete Person or Organization domain model.
3. Human overlays may depend on core contracts and add stricter authority and privacy rules.
4. Products may compose core, platform, and applicable overlays.
5. Product modules must not become alternative owners of reconciliation truth.
6. Adapters implement ports; application logic does not depend on concrete filesystem or external-service implementations.
7. Generated projections remain deterministic and manifest-owned.
8. Every external or behavioral effect remains approval-, purpose-, hash-, and context-bound.

## Refactor Priority

### Critical before generic rollout

- Replace generic Boolean approval with governed approval evaluation.
- Separate interpretation resolution from disclosure and dispatch.
- Clarify model-feedback artifact authority.
- Introduce generic contracts behind compatibility adapters.
- Preserve human-specific privacy and self-declaration as stricter overlays.

### High

- Extract repository and dispatch ports.
- Introduce governed reconciliation findings.
- Move lineage semantics out of ambiguous observation fields.
- Type confidence and behavioral directives.
- Add architecture tests for dependency direction and bounded-context ownership.

### Medium

- Reorganize package layout after contracts stabilize.
- Add product-context registries and explicit extension points.
- Add constitutional traceability metadata to contracts and tests.
- Add migration tooling from human-state records to generic state records.

### Deferred

- Individual psychological maturity modeling.
- Universal coherence or calibration scores.
- Clinical or health-adjacent Person Object expansion.
- Premature commitment to a single relationship ontology.

## Migration Strategy

1. **Characterize current behavior.** Freeze regression fixtures for human-state selection, transitions, policy rejection, and model-feedback receipts.
2. **Add generic contracts beside existing classes.** Do not rename or move the human path first.
3. **Build adapters between human and generic contracts.** Prove semantic parity.
4. **Split application responsibilities.** Route the human reference path through the new ports and services.
5. **Replace compatibility approval fields.** Governed approval evaluation becomes authoritative.
6. **Add nonhuman reference subjects.** Prove the core is not person-specific.
7. **Move package boundaries only after imports are stable.** Structure follows proven dependency direction.
8. **Migrate records through governed operations.** Do not manually rewrite canonical history.

## Validation Requirements

The refactor is complete only when tests prove:

- current human-state behavior is preserved unless explicitly superseded;
- one human and at least two nonhuman subject classes use the same generic contracts;
- human privacy and self-declaration controls remain stricter;
- TEST authority cannot cross into PRODUCTION;
- reconciliation can retain competing interpretations and uncertainty;
- internal reconciliation and external disclosure are separate operations;
- no product module is imported by core;
- no direct external effect occurs without a governed adapter and approval;
- all decisions, findings, disclosures, packages, and effects remain reconstructable from provenance and receipts;
- model-feedback artifacts have an explicit authority classification.

## Recommendation

Proceed with the refactor as an overlay on existing Sprints 5–9 rather than creating a parallel roadmap. Sprint 5 must establish the approval and transaction foundation; Sprint 6 should harden the human reference path behind ports; Sprint 7 should introduce the generic cognitive core; Sprint 8 should implement relationship and transition reconciliation; Sprint 9 should separate interpretation, stewardship, packaging, and model use.
