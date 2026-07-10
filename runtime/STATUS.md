# Runtime v0.1 Status

## Current State

Runtime v0.1 is operational on the `sandbox` branch for the current canonical publication set.

The portable core, filesystem execution, GitHub persistence, workspace synchronization contracts, generated views, export/import, manual delivery fallback, feedback ingestion, and visual-render request pipeline are implemented.

## Implemented

- Platform-neutral Pydantic domain records.
- Repository, event, workspace, publication, feedback, and visual-renderer ports.
- Filesystem JSON record and event adapters.
- GitHub record and append-only event repositories.
- Concrete GitHub contents client with optimistic concurrency and classified errors.
- Drive/Docs/Sheets-neutral document, table, and sync-queue contracts.
- In-memory workspace adapters and canonical-wins reconciliation behavior.
- Governance-as-code readiness policies.
- Manufacturing application service.
- Manual publication fallback with deterministic payload and checklist packages.
- Explicit publication-approval enforcement.
- Feedback persistence, ingestion events, and explicit promotion to source records.
- Manual visual renderer fallback with deterministic prompt packages.
- Five proof-bounded render requests for NKS-PUB-000001.
- Deterministic generated views for publications, proofs, visual packages, visual requests, workflow events, feedback, and ecosystem capabilities.
- Portable checksummed export/import.
- CLI support for tests, view generation, and state export/import.

## Architectural Boundaries

- Domain and application modules import no GitHub, Google, publication-platform, image-generation, or network clients.
- External systems remain adapters.
- GitHub is current persistence, not runtime identity.
- Workspace edits do not overwrite canonical state without reconciliation.
- External feedback is not proof unless separately evaluated.
- Publication preparation requires explicit recorded user approval.
- Generated visual assets require review before approval or public use.

## Canonical Publication State

NKS-PUB-000001 — The Corpus Is Manufactured, Not Found

Internal gates:

- Source: pass
- Proof: pass
- Narrative arc: pass
- Visual package: pass
- Editorial readiness: pass
- User approval: pending

Prepared visual-render inputs:

- NKS-VRQ-000001 → NKS-DGM-000001 signature diagram
- NKS-VRQ-000002 → NKS-HRO-000001 hero image
- NKS-VRQ-000003 → NKS-CAR-000001 carousel
- NKS-VRQ-000004 → NKS-QTC-000001 quote card
- NKS-VRQ-000005 → NKS-PIN-000001 Pinterest pin

## Verified Local Results

- Runtime core: 6 passed in 0.14s
- Generated views: 1 passed in 0.13s
- GitHub event repository: 2 passed in 0.08s
- GitHub contents client: 1 passed in 0.12s
- Dependency extraction: 3 passed in 0.10s
- Workspace contracts: 3 passed in 0.12s
- Workspace adapters and reconciliation: 4 passed in 0.09s
- Manual delivery and feedback workflows: 3 passed in 0.15s
- Manual visual renderer: 1 passed in 0.12s

No hosted GitHub Actions result is claimed.

## Generated Views

- `generated/publication-index.md`
- `generated/proof-index.md`
- `generated/visual-package-index.md`
- `generated/visual-request-index.md`
- `generated/event-index.md`
- `generated/feedback-index.md`
- `generated/ecosystem-capabilities.md`

## Remaining Work

### Executable internally

- Expand canonical JSON conversion to publications 2–12.
- Retrofit proof and narrative records for publications 2–12.
- Create visual packages and render requests for publications 2–12.
- Sync generated human views to Drive when connector execution is selected.
- Evaluate direct publication adapters against the existing contract.

### External or user-gated for Publication 1

- Render the five visual assets.
- Review and approve or reject each asset.
- Record explicit user publication approval.
- Publish through a direct or manual adapter.
- Record public URLs and receipts.
- Ingest resulting feedback and metrics.

## Current Stop Boundary

The runtime has no internal blocker for continued corpus expansion.

Publication 1 cannot cross into public delivery until visual review and explicit user approval are recorded.