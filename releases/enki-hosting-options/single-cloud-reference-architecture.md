# Single-Cloud Reference Architecture

## Decision Status

Initial hosted TEST selection: **GCP-NATIVE**.

The earlier evaluation identified `CF-NATIVE` as a finalist and retained `GCP-NATIVE` as the container-native alternative. The implementation decision has since moved the initial hosted TEST path to GCP so that the existing Python runtime can be containerized with minimal adaptation and the infrastructure control plane can be governed through GitHub Actions, Workload Identity Federation, and Terraform.

`CF-NATIVE` remains a retained reference alternative. This document preserves both architectures for decision lineage; it no longer implies that Cloudflare is the selected initial TEST target.

Current selected-path documentation:

- `docs/architecture/gcp-test-reference-architecture.md`
- `docs/infrastructure/gcp-execution-control-plane.md`
- `docs/roadmaps/gcp-hosted-platform-roadmap.md`

## GCP-NATIVE — Selected Initial TEST Path

```text
Consumer suites
    |
    v
Cloud Run (Python ENKI runtime)
    |
    +--> governed ENKI consumer boundary
    |      - approval and policy enforcement
    |      - no direct repository shortcut
    |
    +--> Cloud SQL PostgreSQL candidate
    |      - only if runtime persistence confirmation preserves relational semantics
    |
    +--> Cloud Storage evidence / export plane
    |      - only where durable object storage is required
    |
    +--> Artifact Registry
    |      - immutable container artifacts
    |
    +--> Secret Manager / IAM / Workload Identity
    |      - short-lived deployment authority
    |      - runtime least-privilege identities
    |
    +--> Cloud Logging / Monitoring
           - operational health and failure evidence
```

### Trust boundaries

1. Human-authorized merge to `sandbox` is the TEST infrastructure authority transition.
2. Pull-request workflows receive no GCP deployer identity.
3. GitHub OIDC assertions must satisfy the exact repository, `push` event, `refs/heads/sandbox`, and exact Terraform workflow reference before WIF grants deployer impersonation.
4. Terraform governs the platform; the application release pipeline governs which validated immutable ENKI artifact runs there.
5. Runtime persistence remains a governed implementation decision. Cloud SQL PostgreSQL is the current relational candidate, not an assumption that deployment evidence already exists.

### Failure domains

The initial GCP TEST project intentionally accepts a single-provider failure domain to reduce early operational complexity. Provider-exit portability remains a governing requirement through export/import, checksummed recovery artifacts, infrastructure as code, and application-level provider-neutral contracts.

### Data flow

Canonical writes remain governed through ENKI application services. Persistence stores only authorized canonical effects. Evidence and export artifacts remain logically separate from canonical mutation authority. Downstream products consume through stable ENKI consumer contracts and do not write predictions or recommendations directly into canonical state.

### Production prerequisites

TEST bootstrap permissions are transitional and must not be copied into STAGE or PROD. Production readiness requires least-privilege IAM, validated secrets lifecycle, persistence isolation, backup/restore proof, observability, release provenance, rollback, and explicit production authority gates.

## CF-NATIVE — Retained Reference Alternative

```text
Consumer suites
    |
    v
Cloudflare edge / Workers
    |-- governed ENKI consumer boundary
    |-- approval and policy enforcement
    |-- no direct repository shortcut
    |
    +--> D1 candidate canonical operational store
    |      - namespace / tenant / subject / domain / audience boundaries
    |      - logical isolation contract
    |
    +--> R2 evidence / export / portability plane
           - immutable evidence packages
           - recovery exports
           - provider-exit artifacts
```

### Retained rationale

The Cloudflare-native option remains relevant where edge execution, operational consolidation, and low-cost integrated object storage outweigh the runtime-adaptation and persistence-model differences. Re-selection would require a new governed architecture decision and corresponding updates to diagrams and roadmaps.

## Single-cloud selection criteria

Prefer a single-cloud design when reduced operational complexity, one incident owner, and low cross-provider latency are more valuable than provider-failure isolation. Reject it when independent data custody, stronger provider-exit posture, or independent evidence-plane survivability is a governing requirement.

## Documentation Synchronization

Any future provider-selection change must update the selected-path architecture diagrams and hosted-platform roadmap in the same change set. See `docs/governance/architecture-roadmap-synchronization.md`.