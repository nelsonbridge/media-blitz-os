# Architecture and Roadmap Synchronization Rule

> **Authority class: Class 3 — documentation-governance rule.**
> This rule governs required documentation updates for architecture- and roadmap-affecting changes. Implementation truth remains established by merged code, canonical records, generated authoritative projections, workflow evidence, deployment receipts, and external system state as applicable.

## Purpose

Prevent the repository's explanatory architecture, diagrams, and roadmaps from drifting behind governed implementation decisions.

Architecture and roadmap documentation are part of the change surface. When a change materially alters deployment topology, trust boundaries, authority flow, system boundaries, persistence, integration contracts, environment strategy, or planned capability sequence, the same change set must update the affected documentation artifacts.

## Required Synchronization

A qualifying pull request must update, as applicable:

1. The relevant architecture narrative.
2. The relevant architecture diagram source.
3. The relevant roadmap or capability sequence.
4. Index, README, or cross-reference links needed to make the updated artifacts discoverable.
5. Status language distinguishing documented intent from operationally proven state.

Documentation updates should land in the same pull request as the architecture-affecting change whenever practical. A change must not be described as operational merely because its documentation or infrastructure code has been merged.

## Diagram Rule

Architecture diagrams must be stored as version-controlled documentation source, preferably Mermaid or another text-based reproducible format.

Provider-specific deployment diagrams belong under `docs/architecture/` or the corresponding `docs/infrastructure/` documentation tree. Existing architecture references elsewhere in the repository may be retained for historical comparison, but they must be clearly marked when they are no longer the selected implementation path.

Rendered image exports are optional presentation artifacts. The version-controlled source diagram is the durable documentation artifact.

## Roadmap Rule

Roadmap-affecting changes must update the applicable roadmap in the same change set.

- Hosted platform and infrastructure sequencing belongs under `docs/roadmaps/` and may also be reflected in broader capability roadmaps under `roadmap/`.
- Generated authoritative roadmap files under `generated/` must never be edited manually. Their canonical inputs must be changed instead.
- Historical roadmaps may remain for audit and decision lineage, but current-path documents must identify the selected path and current phase explicitly.

## State and Evidence Rule

Documentation may describe:

- intended architecture;
- selected architecture;
- prepared implementation;
- deployed implementation;
- operationally proven implementation.

These are not interchangeable states.

A diagram showing a planned resource does not prove the resource exists. A roadmap milestone marked prepared does not prove the milestone is complete. Completion claims require the evidence class appropriate to the change.

## Pull Request Check

For any architecture- or roadmap-affecting pull request, reviewers should ask:

1. Did the system topology change?
2. Did an authority or trust boundary change?
3. Did a provider, runtime, persistence, or environment decision change?
4. Did the capability sequence or milestone order change?
5. If yes, are the relevant diagrams and roadmaps updated in this pull request?
6. Are historical alternatives retained or explicitly superseded without being confused for the current selected path?
7. Does the documentation avoid claiming operational completion without evidence?

## Current Application

PR #142 establishes the initial GCP execution control plane for ENKI TEST. Therefore the same change set includes:

- `docs/infrastructure/gcp-execution-control-plane.md`;
- `docs/architecture/gcp-test-reference-architecture.md`;
- `docs/roadmaps/gcp-hosted-platform-roadmap.md`;
- updates to the broader platform capability roadmap and retained hosting-reference documents.

This synchronization pattern is the standing expectation for future architecture and roadmap changes.