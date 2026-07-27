# Platform Capability Roadmap

## Purpose

Define the capability maturation path for the Nelson Knowledge System as an adaptive knowledge manufacturing platform.

This roadmap measures platform growth, not artifact volume or publication count.

## Core Principle

The platform should know why it is doing something before it knows how to do it.

## Version Model

| Version | Platform State | Primary Question |
|---|---|---|
| V1 | Governed knowledge manufacturing system | Can NKS manufacture proof-bounded reusable knowledge? |
| V2 | Self-assessing knowledge platform | Can NKS evaluate its own health, gaps, and next actions? |
| V3 | Adaptive knowledge platform | Can NKS improve its own manufacturing capability over time? |

## Capability Areas

| Capability | V1 | V2 | V3 |
|---|---|---|---|
| Source Ingestion | Manual / guided | Classified and prioritized | Continuous adaptive ingestion |
| Artifact Manufacturing | Template-driven | Coherence-scored | Self-improving extraction patterns |
| Proof System | Boundary recorded | Confidence scored | Evidence graph and contradiction handling |
| Knowledge Graph | Seeded manually | Coverage measured | Relationship discovery and graph repair |
| Opportunity Engine | Portfolio-based | Value scored across clusters | Adaptive opportunity generation |
| Visual Knowledge | Package-driven | Coverage and reuse measured | Automatic visual recommendations |
| Corpus Health | Implicit | Explicit health metrics | Health-driven execution selection |
| Manufacturing Metrics | Snapshot-based | Measured throughput and reuse | Optimization loops |
| Continuous Validation | Manual review | Automated checklist validation | Integrated quality gates |
| Adaptive Prioritization | Policy-based | Gap-driven scoring | Self-adjusting backlog |
| Hosted Execution & Release | Repository-defined TEST control plane | Multi-environment promotion, observability, and recovery | Self-assessing operational posture with governed optimization |

## Hosted Execution Track

GCP is the selected initial hosted TEST substrate. The infrastructure control plane is repository-defined and uses GitHub Actions, Workload Identity Federation, and Terraform with explicit human authority at merge.

The current hosted-platform sequence is maintained in `docs/roadmaps/gcp-hosted-platform-roadmap.md`, with architecture diagrams in `docs/architecture/gcp-test-reference-architecture.md`.

The hosted execution track progresses through:

1. control-plane preparation;
2. bootstrap and WIF trust proof;
3. minimum ENKI TEST substrate;
4. governed immutable application release;
5. observability and recovery proof;
6. least-privilege IAM hardening and STAGE;
7. governed PROD authority;
8. Project Gilgamesh platform extension.

Hosted-platform roadmap status must not be inferred from architecture documentation alone. Each phase requires the evidence defined by its exit criteria.

## V2 Build Objectives

1. Corpus Health Model.
2. Manufacturing Metrics Framework.
3. Continuous Validation Framework.
4. Adaptive Prioritization Engine.
5. Graph Index and Coverage Measurement.
6. Capability Gap Register.
7. Release Test Harness.
8. Governed hosted execution evidence and operational health measurement.

## V2 Success Criteria

The platform can answer:

1. What is the strongest capability?
2. What is the weakest capability?
3. Where are the largest proof gaps?
4. Which source material has the highest unrealized value?
5. Which artifact creates the greatest downstream leverage?
6. What should be manufactured next, and why?
7. What release can be tested without distorting the trajectory?
8. What exact application artifact is running, where is it running, and what evidence supports its operational state?

## Documentation Synchronization

Architecture- or roadmap-affecting changes must update the relevant diagrams and roadmap artifacts in the same change set. See `docs/governance/architecture-roadmap-synchronization.md`.

## Anti-Regression Rule

If a proposed action increases output volume but does not improve capability, coherence, proof, reuse, learning, operational reliability, or strategic optionality, it is not a V2 priority.

## Status

Implemented as V2 roadmap foundation. Hosted execution track updated for the selected initial GCP TEST path in July 2026.