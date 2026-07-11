# Runtime v0.1 Status

## Current State

Runtime v0.1 is operational on the `sandbox` branch for the full twelve-publication canonical set.

The portable core, filesystem execution, GitHub persistence, workspace synchronization contracts, generated views, export/import, manual delivery fallback, feedback ingestion, visual-render request pipeline, and quantitative branch-coverage instrumentation are implemented.

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
- Canonical source records NKS-SRC-000001 through NKS-SRC-000003.
- Canonical artifact, proof, narrative, visual-package, and publication records for NKS-PUB-000001 through NKS-PUB-000012.
- `pytest-cov` instrumentation with branch coverage.
- Terminal missing-line output plus `coverage.json` and `coverage.xml` reports.
- Initial whole-runtime coverage floor of 70%.
- Coverage configuration regression test.
- Portable GitHub Actions coverage workflow using the same `pytest` command as local execution.

## Architectural Boundaries

- Domain and application modules import no GitHub, Google, publication-platform, image-generation, or network clients.
- External systems remain adapters.
- GitHub is current persistence, not runtime identity.
- Workspace edits do not overwrite canonical state without reconciliation.
- External feedback is not proof unless separately evaluated.
- Publication preparation requires explicit recorded user approval.
- Generated visual assets require review before approval or public use.
- Coverage is reproducible locally; GitHub Actions is a secondary verification surface.

## Canonical Publication Gate State

### NKS-PUB-000001

- Source: ready.
- Proof: ready.
- Narrative: ready.
- Visual package: ready.
- Editorial: ready.
- User approval: needed.

Prepared render requests:

- NKS-VRQ-000001 → NKS-DGM-000001 signature diagram.
- NKS-VRQ-000002 → NKS-HRO-000001 hero image.
- NKS-VRQ-000003 → NKS-CAR-000001 carousel.
- NKS-VRQ-000004 → NKS-QTC-000001 quote card.
- NKS-VRQ-000005 → NKS-PIN-000001 Pinterest pin.

### NKS-PUB-000002 through NKS-PUB-000004

- Proof: ready.
- Narrative: ready.
- Visual package: needed.
- Editorial: needed.
- User approval: needed.

### NKS-PUB-000005

- Proof: partial pending quantitative verification.
- Narrative: ready.
- Visual package: needed.
- Editorial: needed.
- User approval: needed.

### NKS-PUB-000006 through NKS-PUB-000008

- Proof: ready.
- Narrative: ready.
- Visual package: needed.
- Editorial: needed.
- User approval: needed.

### NKS-PUB-000009 through NKS-PUB-000012

- Proof: partial pending current primary-source verification.
- Narrative: ready.
- Visual package: needed.
- Editorial: needed.
- User approval: needed.

## Verified Local Functional Results

- Runtime core: 6 passed in 0.14s.
- Generated views: 1 passed in 0.13s.
- GitHub event repository: 2 passed in 0.08s.
- GitHub contents client: 1 passed in 0.12s.
- Dependency extraction: 3 passed in 0.10s.
- Workspace contracts: 3 passed in 0.12s.
- Workspace adapters and reconciliation: 4 passed in 0.09s.
- Manual delivery and feedback workflows: 3 passed in 0.15s.
- Manual visual renderer: 1 passed in 0.12s.
- Publication #2 readiness state: 1 passed in 0.09s.
- Twelve-publication reference and gate verification: 3 assertions passed.
- Twelve-publication generated-index coverage: 1 check passed.

No hosted GitHub Actions result is claimed.

## Quantitative Coverage State

Configured:

- statement and branch coverage;
- terminal missing-line report;
- `coverage.json`;
- `coverage.xml`;
- whole-package failure threshold: 70%;
- target thresholds: domain/policies 90%+, application services 85%+, portable adapters 80%+.

The exact repository-wide percentage must be taken from a complete coverage execution of the committed test suite. Configuration is now enforced by `tests/test_coverage_configuration.py`; no percentage is fabricated before that report exists.

## Generated Views

- `generated/publication-index.md` — 12 publications.
- `generated/proof-index.md` — 12 proof records.
- `generated/visual-package-index.md` — 12 visual packages.
- `generated/visual-request-index.md`.
- `generated/event-index.md`.
- `generated/feedback-index.md`.
- `generated/ecosystem-capabilities.md`.

## Remaining Work

### Executable internally

- Execute the complete committed suite with quantitative coverage and commit the baseline report.
- Raise package-specific thresholds after reviewing uncovered critical paths.
- Create visual briefs and render requests for NKS-PUB-000002 through NKS-PUB-000012.
- Perform primary-source verification for NKS-PUB-000005 and NKS-PUB-000009 through NKS-PUB-000012.
- Run editorial reviews for NKS-PUB-000002 through NKS-PUB-000012.
- Evaluate direct publication adapters against the existing contract.
- Sync generated human views to Drive when connector execution is selected.

### External or user-gated for Publication #1

- Render the five visual assets.
- Review and approve or reject each asset.
- Record explicit user publication approval.
- Publish through a direct or manual adapter.
- Record public URLs and receipts.
- Ingest resulting feedback and metrics.

## Current Stop Boundary

There is no internal runtime blocker. The non-stop rule continues through quantitative coverage execution, visual-package preparation, evidence verification, and editorial review.

Public release remains gated by visual review and explicit user approval.
