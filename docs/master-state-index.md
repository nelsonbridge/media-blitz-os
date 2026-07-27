# Master State Index

> **Authority class: Class 3 — transitional human-readable index.**
> This file is manually maintained and does not establish current operational truth. Canonical machine records and regenerated projections under `generated/` take precedence. See `docs/state-authority-model.md`.

## Purpose

Human-readable orientation to the Nelson Knowledge System.

The repository outranks memory. Validated canonical machine state and generated authoritative projections outrank this narrative index.

## System Identity

The repository implements a **Knowledge Manufacturing Operating System**.

Media Blitz is a downstream publishing subsystem, not the whole system.

## Constitutional Capability Layer

- **ANU** is the Origin Authority capability: foundational intent, strategic direction, constitutional approval, and final governance authority.
- **ENKI** is the collective Knowledge Engine capability: knowledge synthesis, systems reasoning, architecture, implementation guidance, repository intelligence, and technical continuity.
- The current founder occupies ANU through a stewardship assignment; the individual is not hard-coded as the role.
- Current human and AI implementations contribute to ENKI; no implementation is ENKI itself.
- Capabilities are durable. Implementations are replaceable.

Canonical governance and records:

- `docs/governance/NKS-CONSTITUTION.md`
- `docs/standards/NKS-STD-001-Canonical-Naming.md`
- `docs/standards/NKS-STD-002-Role-Independence.md`
- `docs/standards/NKS-STD-003-Capability-Hierarchy.md`
- `docs/standards/NKS-STD-004-Licensing-Model.md`
- `records/capabilities/capability-registry.json`
- `records/stewards/stewards.json`

## Active State

AUDIT-0001 is complete.

Runtime v0.1 is operational for the complete twelve-publication canonical set.

The GCP execution control plane is prepared in PR #142 but is not yet operational. Operational proof requires successful bootstrap execution, repository-variable configuration, trusted Workload Identity Federation authentication, and a successful Terraform plan/apply cycle from `sandbox`.

## Canonical Counts

The following counts are a narrative snapshot and must be verified against regenerated projections before operational use.

- Sources: 3.
- Publications: 12.
- Proof records: 12, all `ready`.
- Editorial records: 12, all `ready`.
- User approvals: 12, all `needed`.
- Visual packages: 12.
- Visual packages ready: 1.
- Visual packages awaiting rendered review: 11.
- Visual render requests: 60.

## Manufacturing Pipeline

Source
→ Evidence / Proof
→ Canonical Artifact
→ Narrative Arc
→ Visual Package
→ Publication Package
→ Distribution
→ Feedback
→ Corpus Enrichment

## Runtime Topology

- ANU: origin authority, constitutional intent, and explicit approval boundaries.
- ENKI: collective knowledge-engine capability realized by replaceable human, AI, and automation implementations.
- Local Python: tests, transformation, export/import, reconciliation, and audit execution.
- GitHub: current canonical persistence, source control, audit history, and infrastructure-intent repository.
- GitHub Actions: governed automation layer; infrastructure deployment authority is available only through the exact trusted `sandbox` Terraform workflow after the human merge boundary.
- GCP Workload Identity Federation: planned keyless trust bridge from the trusted GitHub workflow to temporary GCP execution authority.
- Terraform: planned declarative control plane for hosted TEST infrastructure; GCS remote state is established by the one-time bootstrap.
- GCP `enki-test`: initial hosted environment target; not operational until bootstrap and trusted apply evidence exist.
- Filesystem bundle: portable execution, migration, and disaster recovery.
- Drive, Docs, and Sheets: generated human workspaces.
- Web and Consensus: evidence adapters.
- Image generation: visual renderer adapter.
- Medium and social systems: direct or manual publication adapters.
- Email, calendars, contacts, and automations: communication and scheduling adapters.

External systems and ENKI implementations do not own domain policy or canonical identifiers.

See `docs/infrastructure/gcp-execution-control-plane.md` for the GCP authority boundary and bootstrap sequence.

## Implemented Foundation

### Governance

- OS Constitution and No Idle State Rule.
- NKS Constitution and ANU/ENKI constitutional capability layer.
- NKS-STD-001 — Canonical Naming.
- NKS-STD-002 — Role Independence.
- NKS-STD-003 — Capability Hierarchy.
- NKS-STD-004 — Capability Licensing Model.
- Source → Proof → Publication Rule.
- Narrative Arc Standard.
- Publication Readiness Gate.
- Visual Knowledge System and Diagram Language Standard.
- Portable Runtime Rule.
- Capability Reassessment Protocol.
- Connected Ecosystem Capability Inventory.
- ADR-0001 — Own the Contract Layer.
- ADR-0002 — Hybrid Buy, Modular Design.

### Canonical Corpus

- NKS-SRC-000001 through NKS-SRC-000003.
- NKS-ART-000001 through NKS-ART-000012.
- NKS-PRF-000001 through NKS-PRF-000012.
- NKS-NAR-000001 through NKS-NAR-000012.
- NKS-VIS-000001 through NKS-VIS-000012.
- NKS-PUB-000001 through NKS-PUB-000012.
- NKS-VRQ-000001 through NKS-VRQ-000060.
- Derivative packages NKS-DER-000001 through NKS-DER-000048.

### Runtime

- Portable domain and application layers.
- Filesystem and GitHub persistence adapters.
- Append-only workflow events.
- Governance-as-code policies.
- Generated views.
- Checksummed export/import.
- Workspace synchronization contracts and reconciliation.
- Manual publication fallback.
- Feedback ingestion and source promotion.
- Visual renderer contract and manual fallback.
- Social publication contract and generic HTTP adapter.
- Repository audit engine and CLI.

## Publication State

### Publication #1

NKS-PUB-000001 — The Corpus Is Manufactured, Not Found

- Proof: ready.
- Narrative: ready.
- Editorial: ready.
- Visual package: ready.
- User approval: needed.
- Five production render requests prepared.

### Publications #2–#12

- Proof: ready.
- Narrative: ready.
- Editorial: ready.
- Five production render requests prepared per publication.
- Visual gate: needed pending rendered-asset review.
- User approval: needed.

## Audit Findings

AUDIT-0001 established:

- repository identity has expanded beyond Media Blitz;
- canonical indexes were ahead of Runtime Status and Master State;
- completed evidence, editorial, adapter, and Drive work remained listed as pending;
- synthetic feedback validation is the highest-priority missing internal subsystem;
- production visual assets are the highest-priority missing user-visible deliverables.

Audit outputs:

- `generated/audit/repository-audit.md`
- `generated/audit/repository-audit.json`
- `docs/audits/AUDIT-0001-Repository-Reset.md`

## Current Execution Queue

This section describes intended work, not implementation truth.

1. Reconcile documentation for the GCP execution control plane, authority boundary, and bootstrap sequence.
2. Execute the one-time GCP bootstrap and capture evidence.
3. Configure the five GitHub Actions variables and prove trusted WIF authentication from `sandbox`.
4. Prove the first authoritative Terraform plan/apply cycle.
5. Begin incremental hosted TEST infrastructure packets: Artifact Registry, runtime identity, Secret Manager, persistence, Cloud Run, and observability as required by the runtime.
6. Continue synthetic feedback manufacturing and regression work in parallel where unblocked.
7. Preserve explicit human review and publication gates for Publication #1.
8. Complete the first live publication cycle and real-versus-synthetic feedback calibration after those gates clear.

Designated queue: `docs/revised-execution-queue.md`.

## Current Stop Boundary

There is no internal runtime blocker.

The next infrastructure milestone is documentation reconciliation, followed by explicit human execution of the one-time GCP bootstrap. No ENKI implementation or automation should infer that the bootstrap has occurred from the existence of PR #142 or from documentation alone.

External rendering, approval, and public publication remain explicit user gates. Adapter degradation queues work and does not halt unrelated canonical execution.

## Operating Rules

1. Continue the highest-priority unblocked work.
2. Reassess capabilities before declaring a blocker.
3. Scoped or empty connector results do not prove wider absence.
4. External systems are adapters.
5. Publication requires explicit recorded user approval.
6. Generated visuals require review before public use.
7. Canonical machine state and regenerated projections outrank conversational memory and this document.
8. Canonical roles are capabilities; current people, models, and vendors are replaceable stewards or implementations.
9. Infrastructure proposal authority, human approval authority, and cloud execution authority remain separate.
10. Prepared infrastructure code does not establish deployed infrastructure truth without bootstrap, workflow, and cloud evidence.
