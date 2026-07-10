# Connected Ecosystem Execution Backlog

## Purpose

Translates the reassessed connected ecosystem into executable work while preserving the portable-runtime architecture.

This backlog supplements `docs/technical-backlog.md`. It does not replace the platform-neutral runtime backlog.

## Current Operating Topology

- GitHub: canonical persistence and audit surface.
- Local Python: primary runtime verification and transformation surface.
- GitHub Actions: optional secondary CI surface.
- Drive/Docs/Sheets: human workspace and generated views.
- Gmail/Calendar/Automations: communication, approvals, scheduling, and condition watches.
- Web/Consensus/files: evidence acquisition.
- Image generation: visual rendering.
- Publication platforms: distribution adapters or manual fallback targets.

## Work Items

### ECO-001 — Capability Registry as Machine-Readable State

Status: Planned

Create a canonical JSON registry describing each capability, adapter role, reliability posture, permissions, known limitations, and last verification date.

Acceptance criteria:

- Registry uses platform-neutral capability IDs.
- Empty or partial tool results are annotated with scope limitations.
- Human inventory can be generated from the registry.

### ECO-002 — Local Execution Harness

Status: In Progress

Formalize local isolated execution as a supported runtime adapter.

Acceptance criteria:

- Canonical records can be reconstructed or exported locally.
- Complete pytest suite can execute offline.
- Results generate a machine-readable test report.
- Local execution never claims access to unavailable external networks.

### ECO-003 — GitHub Persistence Client

Status: In Progress

Implement a concrete client for the existing GitHub repository adapter protocol.

Acceptance criteria:

- Read, create, update, list, and conflict behavior are explicit.
- Platform SHA/version metadata remains adapter-only.
- Retryable, conflict, permission, and not-found errors are classified.

### ECO-004 — Generated Indexes

Status: Planned

Generate Publication Index, Proof Ledger, Visual Package Index, runtime status summaries, and eventually Master State from canonical JSON.

Acceptance criteria:

- Generated views are deterministic.
- Drift from manual edits is detectable.
- Generation runs locally and can persist through GitHub adapter.

### ECO-005 — GitHub Event Persistence

Status: Planned

Add append-only workflow event persistence through the GitHub adapter.

Acceptance criteria:

- Duplicate event IDs are idempotent.
- Concurrent writes detect conflicts.
- Event export works without GitHub metadata.

### ECO-006 — Drive/Docs/Sheets Adapter Contracts

Status: Planned

Define separate contracts for document rendering, tabular operational views, and synchronization.

Acceptance criteria:

- Drive connector intermittency queues actions.
- Canonical records remain in portable storage.
- Human edits have an explicit reconciliation policy.

### ECO-007 — Notification and Approval Adapter

Status: Planned

Use Gmail or Outlook for notification and approval communication without treating email replies as implicit domain approval.

Acceptance criteria:

- Messages reference stable NKS IDs.
- Approval requires an explicit recorded domain event.
- Notification failure does not change package state.

### ECO-008 — Scheduling and Monitoring Adapter

Status: Planned

Use Calendar and Automations for review windows, connector watches, publication timing, and recurring summaries.

Acceptance criteria:

- Schedules trigger application commands or notifications, not embedded business rules.
- Condition watches do not duplicate domain events.
- Timezone is explicit.

### ECO-009 — Evidence Adapter Contract

Status: Planned

Unify web research, Consensus, uploaded files, and future document sources behind evidence-record inputs.

Acceptance criteria:

- Source quality and retrieval date are recorded.
- Evidence cannot silently change proof status.
- Quotes and citations retain source lineage.

### ECO-010 — Visual Renderer Adapter

Status: Planned

Connect approved visual briefs to image generation and store generated asset metadata.

Acceptance criteria:

- Renderer consumes NKS visual IDs and proof boundaries.
- Generated files preserve parent relationships and prompt/version metadata.
- User review is required before public use.

### ECO-011 — Manual Publication Adapter

Status: Planned

Treat human-performed publication as a valid adapter implementation.

Acceptance criteria:

- System produces complete platform payload and checklist.
- User records or supplies resulting public URL.
- Publication event maps external URL to platform-neutral publication ID.

### ECO-012 — Direct Publication Adapter Evaluation

Status: Planned

Evaluate available publishing services and platform APIs against the existing Publication Contract and Adapter Contract.

Acceptance criteria:

- Cost remains within operating budget.
- Credentials and secrets remain outside canonical records.
- Each adapter has dry-run, validation, failure classification, and manual fallback.

### ECO-013 — Feedback Ingestion

Status: Planned

Capture platform metrics, comments, qualitative responses, and editorial lessons as new source/evidence records.

Acceptance criteria:

- External feedback is not treated as truth without classification.
- Feedback links to the publication and derivative IDs.
- Useful feedback can create new source records and backlog items.

### ECO-014 — Capability Reassessment Automation

Status: Planned

Create a recurring process to reassess installed plugins and critical adapter capabilities.

Acceptance criteria:

- Reassessment records exact tool scope and limitations.
- Changed capabilities create state/backlog updates.
- No automated reassessment changes domain policy without review.

### ECO-015 — Ecosystem Failure Drill

Status: Planned

Test execution under simulated failures:

- GitHub unavailable;
- Drive unavailable;
- local runtime network isolated;
- image generation unavailable;
- publication adapter unavailable.

Acceptance criteria:

- Domain state remains valid.
- Work is queued or diverted to a fallback.
- No single external platform halts unrelated work.

## Immediate Sequence

1. ECO-004 — Generated Indexes.
2. ECO-005 — GitHub Event Persistence.
3. ECO-003 — Concrete GitHub Persistence Client.
4. ECO-010 — Visual Renderer Adapter for NKS-PUB-000001.
5. ECO-011 — Manual Publication Adapter.
6. ECO-006 — Drive/Docs/Sheets contracts.
7. ECO-013 — Feedback Ingestion.

## Completion Condition

The connected ecosystem is operationally mature when every external capability has:

1. a role definition;
2. an interface or contract;
3. at least one implementation or manual fallback;
4. failure classification;
5. test coverage;
6. an export/migration posture;
7. no direct ownership of domain policy or canonical IDs.
