# Master State Index

## Purpose

Single authoritative index for the Nelson Knowledge System.

The system manufactures governed intellectual property from fragmented source material. Publishing is one downstream output.

## Active Sprint

Sprint 2 — Knowledge Extraction, Runtime Construction, and Corpus Manufacturing

Status: Active.

Publication #1 is internally ready except for generated-asset review and explicit user publication approval. Runtime v0.1 is operational for the current canonical publication set.

## Manufacturing Pipeline

Source
→ Evidence / Proof
→ Canonical Artifact
→ Narrative Arc
→ Visual Knowledge Package
→ Publication Package
→ Distribution
→ Feedback
→ Corpus Enrichment

## Runtime Topology

- ChatGPT: orchestration and application execution.
- Local Python: primary test, transformation, export/import, and reconciliation runtime.
- GitHub: current canonical persistence, source control, and audit surface.
- GitHub Actions: optional secondary CI surface.
- Drive, Docs, and Sheets: generated human workspaces behind portable contracts.
- Email, calendars, contacts, and automations: notification, identity, scheduling, and monitoring adapters.
- Web, Consensus, and uploaded files: evidence adapters.
- Image generation: visual rendering adapter.
- Medium and social platforms: direct or manual publication adapters.

External systems remain adapters. Domain policy and canonical identifiers remain portable.

## Completed Foundation

### Governance and Architecture

- OS Constitution and No Idle State Rule.
- Source → Proof → Publication Rule.
- Narrative Arc Standard.
- Publication Readiness Gate.
- Visual Knowledge System and Diagram Language Standard.
- Portable Runtime Rule.
- Capability Reassessment Protocol.
- Connected Ecosystem Capability Inventory and machine-readable registry.
- Runtime Topology.
- ADR-0001 — Own the Contract Layer.
- ADR-0002 — Hybrid Buy, Modular Design.

### Corpus and Publication

- Source records NKS-SRC-000001 through NKS-SRC-000003.
- Corpus artifacts NKS-ART-000001 through NKS-ART-000012.
- Publication packages and Medium drafts NKS-PUB-000001 through NKS-PUB-000012.
- Review checklists for all twelve publications.
- Derivative packages NKS-DER-000001 through NKS-DER-000048.
- Proof, narrative, relationship-map, roadmap, and retrofit artifacts.

### Publication 1

NKS-PUB-000001 — The Corpus Is Manufactured, Not Found

Complete:

- Article revision.
- Source and proof boundary.
- Narrative arc.
- Canonical source, artifact, proof, narrative, visual, and publication JSON records.
- Publication Contract payload.
- Readiness checklist.
- Visual package NKS-VIS-000001.
- Briefs for signature diagram, hero image, carousel, quote card, and Pinterest pin.
- Proof-bounded render requests NKS-VRQ-000001 through NKS-VRQ-000005.
- Manufacturing event.
- Generated publication, proof, visual-package, visual-request, event, feedback, and capability views.

Current gate result:

- Source: pass
- Proof: pass
- Narrative arc: pass
- Visual package: pass
- Editorial readiness: pass
- User approval: pending

### Runtime v0.1

Implemented:

- Platform-neutral domain models.
- Repository and event ports.
- Filesystem record and event adapters.
- GitHub record and append-only event adapters.
- Concrete GitHub contents client with optimistic concurrency and classified errors.
- Governance-as-code validators.
- Manufacturing application service.
- Deterministic generated views.
- Portable checksummed export/import.
- Runtime CLI.
- Drive/Docs/Sheets-neutral workspace contracts.
- In-memory workspace adapters and canonical-wins reconciliation.
- Manual publication fallback and explicit approval enforcement.
- Feedback ingestion, persistence, events, and explicit promotion to source records.
- Visual renderer contract and manual render-package fallback.

Verified local results:

- Runtime core: 6 passed in 0.14s
- Generated views: 1 passed in 0.13s
- GitHub event repository: 2 passed in 0.08s
- GitHub contents client: 1 passed in 0.12s
- Dependency extraction: 3 passed in 0.10s
- Workspace contracts: 3 passed in 0.12s
- Workspace adapters and reconciliation: 4 passed in 0.09s
- Delivery and feedback workflows: 3 passed in 0.15s
- Manual visual renderer: 1 passed in 0.12s

No hosted GitHub Actions result is claimed.

## Current Critical Path

1. Canonical state is read from GitHub or imported from a portable bundle.
2. Local runtime executes policies, tests, transformations, generated views, and reconciliation.
3. GitHub persists records, events, views, and audit state.
4. Image generation renders NKS-VRQ-000001 through NKS-VRQ-000005.
5. User reviews generated assets.
6. Explicit user approval releases NKS-PUB-000001.
7. Direct or manual publication adapter distributes it.
8. Public URLs and receipts are recorded.
9. Feedback and metrics become classified feedback records and optional new source records.

GitHub Actions and Drive are not on the critical path.

## Remaining Work

### Internally executable

- Expand canonical JSON conversion to publications 2–12.
- Execute proof and narrative retrofit for publications 2–12.
- Create visual packages and render requests for publications 2–12.
- Evaluate direct publication adapters against the existing contracts.
- Sync generated views to Drive when that adapter is selected for execution.

### External or user-gated for Publication 1

- Generate five visual assets.
- Review and approve or reject each asset.
- Record explicit publication approval.
- Publish through a direct or manual adapter.
- Record public URLs and receipts.
- Ingest feedback and metrics.

## Canonical Stores

- GitHub: current canonical persistence, governance, state, schemas, contracts, records, code, tests, generated views, and audit history.
- Filesystem bundle: portable execution, verification, migration, and disaster recovery.
- Drive: generated editorial workspace and human-facing views.

## Operating Rules

1. Continue the highest-priority unblocked work.
2. Reassess capabilities before declaring a blocker.
3. Scoped or empty connector results do not prove wider absence.
4. External systems are adapters.
5. Publication requires explicit recorded user approval.
6. Generated visuals require review before public use.

## Rule

Update this document at the start and end of every execution session. If state conflicts, this document is authoritative until reconciled.