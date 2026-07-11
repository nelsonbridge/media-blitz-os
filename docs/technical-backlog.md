# Technical Backlog

## Purpose

This backlog governs implementation of the Nelson Knowledge System runtime while preserving architectural runway toward a portable, modular, service-oriented platform.

GitHub is the current runtime host and storage adapter. It is not the permanent domain boundary.

## Architectural Principle

The runtime must be portable by design.

No domain rule, workflow, state transition, identifier, proof gate, narrative gate, visual gate, or publication gate may depend directly on GitHub, Google Drive, Medium, LinkedIn, or any other external platform.

External systems are adapters. The domain core remains independent.

## Definition of Portable

The runtime is considered portable when:

1. Domain logic runs locally without GitHub Actions.
2. Canonical records can be read from and written to a filesystem adapter.
3. GitHub access is isolated behind repository interfaces.
4. Google Drive access is isolated behind repository or synchronization interfaces.
5. Workflow execution can be invoked from CLI, test runner, GitHub Actions, or future API without changing domain logic.
6. All canonical records use open formats such as JSON or YAML.
7. Generated Markdown is a view, not the only source of truth.
8. External integrations may fail without corrupting domain state.
9. The same functional test can run against at least two storage adapters.

## Technical Direction

Initial implementation defaults:

- Python
- Pydantic or JSON Schema
- YAML or JSON canonical records
- pytest
- CLI entry point
- GitHub Actions as current orchestration host
- Adapter-based storage and integration boundaries
- Deterministic, idempotent workflows
- Event records for auditability

## Backlog

### TB-001 — Define Runtime Package Boundaries

Status: Planned

Create a package structure that separates:

- domain models
- application workflows
- policy validators
- repository interfaces
- storage adapters
- external integrations
- CLI
- tests

Acceptance criteria:

- Domain packages import no GitHub or Google libraries.
- Integration packages may depend on domain interfaces, never the reverse.

### TB-002 — Create Machine-Readable Canonical Schemas

Status: Planned

Create JSON Schema or Pydantic models for:

- source records
- corpus artifacts
- proof records
- narrative records
- publication packages
- visual packages
- derivative packages
- workflow events
- synchronization jobs

Acceptance criteria:

- Existing Markdown records can be mapped to schema-compliant records.
- Schema validation runs without network access.

### TB-003 — Implement Repository Interfaces

Status: Planned

Define interfaces such as:

- SourceRepository
- ArtifactRepository
- ProofRepository
- NarrativeRepository
- VisualRepository
- PublicationRepository
- EventRepository
- SyncQueueRepository

Acceptance criteria:

- No workflow accesses GitHub paths directly.
- Workflows depend only on repository interfaces.

### TB-004 — Implement Filesystem Adapter

Status: Planned

Implement the first neutral storage adapter using local files.

Acceptance criteria:

- Full functional test runs without GitHub connectivity.
- Records persist in deterministic paths.
- Re-running the same workflow is idempotent.

### TB-005 — Implement GitHub Adapter

Status: Planned

Implement GitHub as a repository and execution adapter.

Acceptance criteria:

- GitHub-specific code is isolated under integrations/adapters.
- The same domain tests pass with filesystem and GitHub adapters.
- GitHub failures produce retryable synchronization or persistence errors.

### TB-006 — Implement Drive Adapter Contract

Status: Planned

Define Google Drive, Docs, and Sheets interfaces before implementing connector-specific behavior.

Acceptance criteria:

- Drive synchronization can be disabled without changing workflows.
- Connector intermittency queues work rather than stopping domain execution.
- Drive documents are treated as editorial views, not sole canonical state.

### TB-007 — Create Explicit State Machines

Status: Planned

Implement valid state transitions for source, proof, narrative, visual, publication, and synchronization records.

Acceptance criteria:

- Invalid transitions fail with explicit errors.
- State transitions are deterministic and auditable.
- Transition tests cover recovery from partial failure.

### TB-008 — Implement Governance as Code

Status: Planned

Convert written governance into executable validators:

- validate_source_lineage
- validate_proof_posture
- validate_narrative_arc
- validate_visual_package
- validate_editorial_readiness
- validate_publication_readiness

Acceptance criteria:

- Every public-readiness decision is reproducible.
- Validation results identify exact failing gates.

### TB-009 — Create Event and Audit Model

Status: Planned

Emit append-only events such as:

- source.recorded
- artifact.created
- proof.required
- proof.completed
- narrative.review_required
- visual.briefed
- publication.ready
- sync.queued
- sync.completed

Acceptance criteria:

- Events can reconstruct workflow history.
- Events are platform-neutral records.

### TB-010 — Generate Human Views from Canonical Records

Status: Planned

Generate Markdown indexes, ledgers, and summaries from machine-readable records.

Acceptance criteria:

- Publication Index, Proof Ledger, Visual Index, and Master State are generated views.
- Manual edits to generated views are detectable.

### TB-011 — Build Runtime CLI

Status: Planned

Provide commands such as:

- nks ingest
- nks validate
- nks manufacture
- nks reconcile
- nks test
- nks sync

Acceptance criteria:

- CLI runs locally and in GitHub Actions.
- Commands return machine-readable exit status and reports.

### TB-012 — Build Functional Test Harness

Status: Planned

Test one source through:

Source
→ Canonical Artifact
→ Proof
→ Narrative Arc
→ Visual Package
→ Publication Package
→ Generated Indexes
→ Reconciled State

Acceptance criteria:

- Test runs against filesystem adapter first.
- Test runs against GitHub adapter second.
- Outputs are equivalent except for adapter metadata.
- Re-run creates no duplicate IDs or records.

### TB-013 — Add Contract Tests for Integrations

Status: Planned

Create adapter contract tests for GitHub, Drive, image generation, and publication platforms.

Acceptance criteria:

- Each adapter proves the same repository contract.
- Failures are classified as retryable, blocked, or terminal.

### TB-014 — Add Export and Migration Capability

Status: Planned

Create a complete export of canonical records, events, schemas, and binary asset references.

Acceptance criteria:

- System state can be exported without GitHub APIs.
- Export can initialize a fresh filesystem or database adapter.
- No proprietary platform identifier is required as the primary key.

### TB-015 — Database Adapter Runway

Status: Planned

Define mapping from canonical schemas to a future relational or document database.

Acceptance criteria:

- IDs remain stable across migration.
- Repository interfaces require no domain-level changes.
- Migration can occur incrementally.

### TB-016 — Orchestrator Independence

Status: Planned

Ensure workflow orchestration is not defined exclusively in GitHub Actions YAML.

Acceptance criteria:

- GitHub Actions invokes the same application service used by CLI and tests.
- Workflow definitions contain no business rules.
- A future scheduler, API, or worker can invoke the runtime unchanged.

### TB-017 — Dependency Extraction Test

Status: Planned

Prove the runtime can be extracted from GitHub.

Test procedure:

1. Export canonical state.
2. Initialize a clean local filesystem runtime.
3. Run validation and reconciliation without network access.
4. Manufacture a new test artifact.
5. Confirm identical policy behavior.

Acceptance criteria:

- Test passes without GitHub, Drive, or external publication access.
- No core module imports platform-specific code.

### TB-018 — Embed Provenance / Promotion Validation as Implicit Security

Status: Planned

Capture the real/synthetic/replay provenance and source promotion workflow as an architectural security boundary.

Acceptance criteria:

- Feedback provenance is explicit and enforced by the promotion workflow.
- External adapters may provide signals but cannot directly create canonical source records.
- Promoted feedback includes lineage metadata and proof limitations.
- The model preserves `REAL | SYNTHETIC | REPLAY` distinction and prevents silent canonicalization.
- The work is scoped as backlog for later security hardening, not a current blocker.

### TB-019 — Runtime Hardening and Validation Enforcement

Status: Planned

Harden the runtime by enforcing validation and provenance gates in the core application services.

Acceptance criteria:

- Feedback ingestion and promotion paths are enforced by the runtime, not just documented.
- Invalid provenance, missing lineage, or unauthorized canonicalization transitions fail loudly.
- Promotion to source requires explicit provenance, source location, and proof boundary metadata.
- Runtime instrumentation records audit events for feedback ingestion, promotion, and validation failures.
- CLI commands and automated tests cover the hardened execution path.

## Release Guardrail

Runtime v0.1 is not architecturally acceptable unless TB-001 through TB-005, TB-007, TB-008, TB-011, TB-012, and TB-017 are complete.

## Ongoing Rule

Every new integration must include:

1. an interface or contract;
2. an adapter implementation;
3. contract tests;
4. failure classification;
5. export or migration implications;
6. proof that the domain core remains platform-neutral.
