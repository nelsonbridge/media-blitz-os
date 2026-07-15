# Sprint 24 — Hosted Deployment Options and Split-Cloud Architecture Exploration

## Purpose

Evaluate hosted deployment patterns for Enki after completion of the Enki 1.0-rc1 readiness package, with particular attention to split-cloud architectures and the unresolved physical production controls recorded in Sprint 23.

This sprint is architecture exploration and decision support. It does not provision production infrastructure and does not confer production approval.

## Architecture patterns to evaluate

1. Single-cloud managed deployment.
2. Provider-split cloud, where major service domains are intentionally placed with different cloud providers.
3. Control-plane/data-plane split, where orchestration and consumer-facing runtime are separated from canonical data custody and persistence.
4. Portability-preserving hybrid patterns where they materially reduce lock-in, improve sovereignty, or isolate risk without creating disproportionate operational burden.

## Required analysis dimensions

- compute and runtime placement;
- canonical data placement and replication;
- managed database isolation and row-level controls;
- identity federation and workload identity;
- key custody and per-tenant key management;
- secrets management;
- network segmentation and private connectivity;
- observability and privacy-safe telemetry;
- backup, archive, recovery, and disaster recovery;
- failure domains and blast radius;
- latency and cross-cloud egress;
- availability and consistency tradeoffs;
- operational ownership and support boundaries;
- cost ranges and major cost drivers;
- vendor lock-in and exit cost;
- portability and migration complexity;
- privacy, residency, compliance, and audit implications.

## Split-cloud questions

The sprint must distinguish at least two materially different split-cloud approaches:

- **Provider split:** selected runtime, data, security, or recovery capabilities are distributed across independent cloud providers.
- **Control/data split:** the Enki control plane and consumer/API runtime are hosted separately from canonical data, keys, and persistence, whether or not the separation crosses providers.

The analysis must test whether the additional isolation and resilience benefits justify increased latency, egress, distributed failure modes, IAM complexity, operational burden, and recovery complexity. Split cloud is a candidate architecture, not a presumed target state.

## Sprint 23 prerequisite mapping

Every shortlisted option must explicitly map how it would address, defer, or leave unresolved:

- cloud IAM;
- production identity federation;
- managed database row-level isolation;
- network segmentation;
- per-tenant production key management;
- production secrets management;
- independent penetration testing.

No architecture diagram or provider capability statement counts as validation of these controls.

## Deliverables

- hosting options decision matrix;
- single-cloud reference architecture;
- split-cloud reference architecture;
- threat and trust-boundary analysis;
- failure-domain and data-flow analysis;
- cost model and cost-driver summary;
- migration and rollback considerations;
- shortlist with explicit selection and disqualification criteria;
- human hosting-direction decision request.

## Decision boundary

Sprint 24 completion means the hosting alternatives and their tradeoffs are sufficiently explicit for an informed human decision. It does not mean a provider has been selected, infrastructure has been purchased, production controls have been validated, or Enki has been approved for production hosting.
