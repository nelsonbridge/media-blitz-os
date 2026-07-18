# GCP Execution Control Plane

> **Authority class: Class 3 — architecture and operating-model documentation.**
> This document describes intended infrastructure control boundaries and execution flow. It does not establish implementation truth. Merged code, GCP resources, workflow results, and deployment receipts provide operational evidence.

## Purpose

Establish Google Cloud Platform as the initial hosted execution substrate while preserving explicit human authority, keyless automation, repository-defined infrastructure, and separation between implementation agents and deployment authority.

The design goal is not to give AI systems standing cloud credentials. The design goal is to make the repository the governed source of infrastructure intent and GitHub Actions the narrowly trusted execution bridge into GCP.

## Current Status

As of 2026-07-17:

- PR #142 contains the bootstrap script and Terraform GitHub Actions workflow.
- The bootstrap design has passed structural review of its authority boundary.
- The GCP execution bridge is **prepared but not yet operational**.
- No documentation statement should be interpreted as proof that GCP resources have been provisioned.

The bridge becomes operational only after all of the following are evidenced:

1. The `enki-test` GCP project exists with billing attached.
2. `infrastructure/bootstrap/bootstrap-gcp.sh` completes successfully.
3. The five required GitHub Actions variables are configured.
4. PR #142 is merged into `sandbox` through the authorized human merge path.
5. The trusted Terraform workflow successfully authenticates through Workload Identity Federation and completes an authoritative plan/apply cycle.

## Authority Model

The infrastructure path separates proposal, approval, and execution.

```text
Copilot / implementation agent
        |
        v
Pull request
        |
        +--> offline Terraform validation only
        |    no GCP deployer identity
        |
        v
Human-authorized merge -> sandbox
        |
        v
Exact trusted Terraform workflow
        |
        v
GitHub OIDC token
        |
        v
GCP Workload Identity Federation
        |
        v
terraform-deployer
        |
        v
authoritative terraform plan
        |
        v
serialized terraform apply
        |
        v
GCP TEST environment
```

### Human authority

The repository owner retains consequential infrastructure authority. A Copilot-authored change, ChatGPT recommendation, passing test, or successful PR validation does not itself authorize a GCP mutation.

The authority transition for TEST occurs when an authorized human merges an accepted infrastructure change into `sandbox`.

### ENKI contribution

ENKI implementations may contribute architecture, specifications, acceptance contracts, review, implementation, tests, and pull requests. No ENKI implementation owns the cloud account or receives permanent GCP credentials by virtue of being an implementation agent.

### Execution authority

GitHub Actions receives short-lived execution authority only through Workload Identity Federation. No permanent GCP service-account key is stored in GitHub.

## Workload Identity Trust Boundary

The deployer identity accepts only OIDC assertions satisfying all four required claims:

| Claim | Required value |
|---|---|
| `assertion.repository` | `nelsonbridge/media-blitz-os` |
| `assertion.event_name` | `push` |
| `assertion.ref` | `refs/heads/sandbox` |
| `assertion.workflow_ref` | `nelsonbridge/media-blitz-os/.github/workflows/terraform.yml@refs/heads/sandbox` |

A repository-scoped `principalSet` binding provides an additional enforcement point.

Consequences:

- Pull request workflows cannot impersonate `terraform-deployer`.
- Other branches cannot impersonate `terraform-deployer`.
- Other workflow files cannot impersonate `terraform-deployer`.
- Copilot PR execution is structurally separated from deployment authority.

## Bootstrap Boundary

`infrastructure/bootstrap/bootstrap-gcp.sh` is the one-time root-of-trust bootstrap.

It is responsible for:

1. Enabling prerequisite GCP APIs.
2. Creating the Terraform state bucket.
3. Enforcing uniform bucket-level access.
4. Enforcing public access prevention.
5. Enabling state versioning.
6. Creating the Workload Identity Pool.
7. Creating and convergently configuring the GitHub OIDC provider.
8. Creating the `terraform-deployer` service account.
9. Binding the exact repository identity to that service account.
10. Granting temporary bootstrap Terraform permissions.

The bootstrap is intentionally narrow. Application infrastructure belongs in Terraform, not in repeated manual console operations.

## GitHub Actions Variables

The bootstrap prints the values for these repository variables:

- `GCP_PROJECT`
- `GCP_REGION`
- `GCP_WIF_PROVIDER`
- `GCP_SERVICE_ACCOUNT`
- `TF_STATE_BUCKET`

These values are identifiers and configuration, not long-lived authentication secrets.

## Terraform Execution Model

### Pull requests

Infrastructure pull requests run only offline validation:

```text
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

They receive no GCP credentials.

### Sandbox merge

A push to `sandbox` through the trusted workflow performs:

```text
OIDC authentication
-> Terraform init with GCS backend
-> Terraform validate
-> authoritative Terraform plan
-> Terraform apply
```

Sandbox applies are serialized. A later push queues rather than canceling an infrastructure mutation already in progress.

## State Management

Terraform remote state is stored in a dedicated GCS bucket with:

- uniform bucket-level access;
- public access prevention enforced;
- object versioning enabled.

The bootstrap re-applies these controls on every run so repeated execution converges on the expected security posture.

## Environment Sequence

The initial target is TEST only.

```text
GCP
└── enki-test
```

The intended future topology is:

```text
GCP
├── enki-test
├── enki-stage
└── enki-prod
```

STAGE and PROD must not inherit TEST's temporary bootstrap permissions without an explicit least-privilege hardening decision.

## IAM Hardening Obligation

`terraform-deployer` temporarily receives broad bootstrap permissions sufficient to construct the initial resource set.

Before STAGE or PROD is established, those grants must be replaced with resource-specific least-privilege roles based on the Terraform resources actually managed.

Broad bootstrap IAM is therefore an accepted TEST-only transitional condition, not the target production security posture.

## Planned Hosted TEST Stack

After the execution bridge is proven, Terraform may provision the TEST platform incrementally, including:

- Artifact Registry;
- Secret Manager resources and bindings;
- Cloud SQL PostgreSQL, if the runtime persistence model confirms PostgreSQL;
- Cloud Run runtime services;
- runtime service identities;
- Cloud Storage where durable object storage is required;
- logging, monitoring, and alerting;
- DNS and ingress only after the runtime is proven.

The infrastructure should be introduced in governed packets rather than as one monolithic apply.

## Application vs Infrastructure Deployment

Two authority paths remain distinct.

### Infrastructure pipeline

Terraform governs the platform on which ENKI runs.

### Application release pipeline

A separate release path governs which validated application artifact is deployed to that platform.

Production promotion should move an already validated immutable artifact forward rather than rebuild source separately per environment.

## Next Milestone

The next milestone after this documentation reconciliation is **bootstrap execution and evidence capture**, not immediate manual construction of Cloud Run or Cloud SQL.

The expected sequence is:

```text
Documentation reconciled
-> create/confirm enki-test project
-> attach billing
-> run bootstrap script
-> configure five GitHub Actions variables
-> merge trusted bridge
-> prove WIF authentication
-> prove authoritative Terraform apply
-> begin incremental TEST infrastructure packets
```

Until the bootstrap and trusted workflow succeed, the GCP control plane remains documented intent rather than operational infrastructure.
