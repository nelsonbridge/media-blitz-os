# Runtime v0.1 Status

## Current State

Runtime v0.1 is operational on the `sandbox` branch for the complete twelve-publication canonical set.

AUDIT-0001 is complete. Canonical JSON and generated indexes are authoritative over earlier stale narrative state.

## Canonical Coverage

- Sources: NKS-SRC-000001 through NKS-SRC-000003.
- Publications: NKS-PUB-000001 through NKS-PUB-000012.
- Proof records: 12, all `ready`.
- Editorial records: 12, all `ready`.
- User approvals: 12, all `needed`.
- Visual packages: 12.
- Visual render requests: NKS-VRQ-000001 through NKS-VRQ-000060.
- Publication #1 visual package: `ready` pending explicit publication approval.
- Publications #2–#12 visual packages: `needed` pending rendered-asset review.

## Implemented Runtime

- Platform-neutral Pydantic domain records.
- Repository, event, workspace, publication, feedback, visual-renderer, and social-publication ports.
- Filesystem and GitHub persistence adapters.
- Concrete GitHub contents client with optimistic concurrency and classified errors.
- Governance-as-code readiness policies.
- Manufacturing application service.
- Deterministic generated views.
- Portable checksummed export/import.
- Drive/Docs/Sheets-neutral workspace contracts and canonical-wins reconciliation.
- Manual publication fallback and explicit approval enforcement.
- Feedback ingestion, persistence, events, and explicit promotion to source records.
- Manual visual renderer fallback and sixty proof-bounded render requests.
- Vendor-neutral social dispatch service and generic JSON/HTTP adapter.
- Repository audit engine, CLI command, regression tests, and GitHub audit workflow.
- Statement and branch coverage configuration with a 70% whole-package floor.

## Verified Results

Previously verified local suites cover:

- runtime manufacturing and idempotency;
- readiness policies;
- GitHub record and event adapters;
- export/import and tamper detection;
- workspace contracts and reconciliation;
- manual delivery and feedback workflows;
- visual renderer contracts;
- twelve-publication reference integrity;
- generated-index coverage;
- complete five-asset visual linkage;
- social dispatch governance;
- generic HTTP adapter behavior.

No hosted GitHub Actions pass is claimed without an observed result.

## Generated Views

- `generated/publication-index.md` — 12 publications.
- `generated/proof-index.md` — 12 proof records, all ready.
- `generated/visual-package-index.md` — 12 visual packages.
- `generated/visual-request-index.md` — 60 requests.
- `generated/event-index.md`.
- `generated/feedback-index.md`.
- `generated/ecosystem-capabilities.md`.
- `generated/audit/repository-audit.md`.
- `generated/audit/repository-audit.json`.

## Current Queue

1. Execute and record the complete quantitative coverage baseline.
2. Build synthetic feedback infrastructure.
3. Build feedback classification, routing, replay, and regression metrics.
4. Render and review Publication #1 assets.
5. Record explicit publication approval.
6. Execute the first publication cycle and record receipts.
7. Compare real feedback against synthetic expectations.

See `docs/revised-execution-queue.md`.

## Stop Boundary

There is no internal runtime blocker.

Public release remains gated by rendered-asset review and explicit user approval. External adapter degradation queues work and does not halt unrelated canonical execution.
