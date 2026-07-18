# Media Blitz OS

Media Blitz OS is the version-controlled architecture repository for the adaptive knowledge, publishing, and career-opportunity system being built around the Nelson body of work.

## Purpose

This repository contains the machine, not merely the media output.

Google Drive remains the working editorial environment. GitHub holds the durable architecture:

- system charter
- execution protocols
- validation rules
- schemas
- templates
- taxonomies
- future automation logic

## Operating Principle

Drive contains the work. GitHub contains the machine that produces, governs, validates, and evolves the work.

## State Authority

Repository files do not all carry equal authority.

1. Validated canonical machine records establish operational truth.
2. Deterministically generated projections under `generated/` provide authoritative human-readable views of that state.
3. Human-authored plans, explanations, status summaries, diagrams, roadmaps, and historical ledgers are non-authoritative unless explicitly generated.

See [`docs/state-authority-model.md`](docs/state-authority-model.md) for precedence, editing rules, and the transitional classification of existing status documents.

## Canonicalization Security

Ingestion may create evidence candidates. Only an explicitly authorized promotion operation may create a canonical source from feedback.

Feedback provenance is mandatory and closed to `REAL`, `SYNTHETIC`, and `REPLAY`. Missing provenance fails closed; replay output is forcibly marked `REPLAY`; synthetic and replay records cannot be promoted as factual sources; and rejected promotion or validation attempts leave append-only workflow events.

See [`docs/canonicalization-security-boundary.md`](docs/canonicalization-security-boundary.md) for the enforced boundary and remaining hardening work.

## Infrastructure Control Plane

GCP is the initial hosted execution substrate. Infrastructure intent is defined in the repository and executed through a narrowly trusted GitHub Actions → Workload Identity Federation → Terraform path.

Pull requests may validate Terraform offline but do not receive the GCP deployer identity. The TEST authority transition occurs only after an authorized merge to `sandbox`, where the exact trusted Terraform workflow may obtain short-lived deployment credentials and perform a serialized plan/apply cycle.

The control plane is currently **prepared but not yet operational**. Operational proof requires successful bootstrap execution, configuration of the required GitHub Actions variables, and a successful trusted WIF-authenticated Terraform run.

See:

- [`docs/infrastructure/gcp-execution-control-plane.md`](docs/infrastructure/gcp-execution-control-plane.md)
- [`docs/architecture/gcp-test-reference-architecture.md`](docs/architecture/gcp-test-reference-architecture.md)
- [`docs/roadmaps/gcp-hosted-platform-roadmap.md`](docs/roadmaps/gcp-hosted-platform-roadmap.md)
- [`infrastructure/bootstrap/README.md`](infrastructure/bootstrap/README.md)

## Documentation Synchronization

Architecture- and roadmap-affecting changes must update the applicable architecture narrative, diagram source, and roadmap in the same change set whenever applicable. Historical alternatives may be retained, but they must not be confused with the selected current path.

See [`docs/governance/architecture-roadmap-synchronization.md`](docs/governance/architecture-roadmap-synchronization.md).

## Current Scope

The initial system supports:

- Medium-first publication strategy
- cross-platform content derivatives
- editorial governance
- evidence and hypothesis tracking
- validation signal architecture
- drift detection
- ancestry mapping
- meta-learning control plane
- career-opportunity alignment

## Budget Constraint

Present operating budget: `$0.00` plus existing tools and free-tier services.

## Initial Status

Repository initialized July 2026 as the external version-controlled foundation for the Media Blitz OS and its broader Adaptive Knowledge Architecture.