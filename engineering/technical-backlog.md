# Technical Backlog

## Purpose

Tracks engineering work required to turn the Nelson Knowledge System from a governed knowledge platform into an increasingly automated operating platform.

## Priority Scale

- P0: Required for Publication Milestone 1.
- P1: Required for repeatable production.
- P2: Required for scale.
- P3: Optional improvement.

## Backlog

| Priority | Item | Description | Dependency | Acceptance Criteria |
|---|---|---|---|---|
| P0 | Publication #1 final review | Complete editorial, proof, arc, visual package, and approval gates. | Current publication package | User can approve or request edits. |
| P0 | Generate NKS-DGM-000001 | Produce Signature Diagram image from brief. | Image generation available | Diagram generated and reviewed. |
| P0 | Generate NKS-HRO-000001 | Produce hero image from brief. | Image generation available | Hero generated and reviewed. |
| P0 | Distribution path selection | Choose manual publishing, adapter, or tool-assisted publication for first release. | Integration evaluation | First platform route selected. |
| P0 | Publication Contract validation checklist | Validate NKS-PUB-000001 against Publication Contract v1. | Contract v1 | Contract payload passes manual validation. |
| P1 | Integration Evaluation Matrix | Score free/open-source publishing solutions against NKS adapter criteria. | Web research | Ranked recommendation. |
| P1 | Adapter prototype | Create first adapter skeleton for selected distribution path. | Vendor selection | Dry-run payload mapping works. |
| P1 | Visual Contract v1 | Define visual-generation payload independent of image vendor. | Visual schema | Contract committed. |
| P1 | Execution Orchestrator design | Define how GitHub Actions or local runner executes NKS loops. | Contract layer | Orchestrator ADR and workflow design committed. |
| P1 | Source Intake Pipeline | Define repeatable source discovery/classification/extraction workflow. | Corpus workflow | Intake queue and templates exist. |
| P1 | Knowledge Roadmap | Define what capability areas the engine matures next. | Current corpus | Roadmap committed and used for prioritization. |
| P1 | Internal Coherence Engine | Score artifacts against mission, pillar, proof, relationships, and publication milestone. | Knowledge Roadmap | Coherence scorecard committed. |
| P2 | Analytics feedback contract | Define how public engagement returns to corpus enrichment. | Publication pipeline | Analytics Contract v1 committed. |
| P2 | Drive sync automation | Convert queued GitHub artifacts to Drive when connector is available. | Drive reliability | Sync run verified. |
| P2 | GitHub Actions validation | Validate contract payloads on commit. | Contract schemas | CI check passes/fails contract payloads. |
| P3 | Multi-vendor adapter support | Add second distribution adapter after first is stable. | Adapter prototype | Same NKS package routes to two adapters. |

## Current Engineering Focus

Complete Publication Milestone 1 before expanding automation depth.

## Publication Milestone 1 Definition

NKS-PUB-000001 is complete when:

1. Article is ready for user approval.
2. Proof boundary is recorded.
3. Narrative arc is complete.
4. Visual package is complete.
5. Signature Diagram is generated and reviewed.
6. Hero Image is generated and reviewed.
7. Publication Contract is validated.
8. Distribution path is selected.
9. User approval is recorded.
10. First publication is released or explicitly queued for manual release.