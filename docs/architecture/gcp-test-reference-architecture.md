# ENKI GCP TEST Reference Architecture

> **Authority class: Class 3 — architecture documentation.**
> This document records the selected initial hosted TEST topology and authority flow. It does not prove that the depicted GCP resources have been provisioned or validated.

## Status

Selected initial hosted path: **GCP TEST**.

Current state: **prepared in repository, pending bootstrap execution and operational proof**.

The earlier Cloudflare-native and Cloudflare/Neon/R2 architectures remain retained reference alternatives. They are not the selected initial TEST implementation path.

## Control-Plane Architecture

```mermaid
flowchart TB
  subgraph AUTHOR["Authority and Implementation"]
    HUMAN["Human origin authority\nreview + merge decision"]
    ENKI["ENKI implementations\narchitecture + specifications + review"]
    COPILOT["Copilot / implementation agent\nTerraform + workflow changes"]
  end

  subgraph GH["GitHub Control Plane"]
    PR["Pull Request"]
    VALIDATE["Offline Terraform validation\nfmt + init -backend=false + validate"]
    SANDBOX["sandbox branch"]
    WORKFLOW["Exact trusted workflow\n.github/workflows/terraform.yml"]
    OIDC["GitHub OIDC token"]
  end

  subgraph GCPAUTH["GCP Trust Boundary"]
    WIF["Workload Identity Federation\nrepo + push + sandbox + workflow_ref"]
    DEPLOYER["terraform-deployer\nshort-lived impersonation"]
    STATE[("GCS Terraform state\nuniform access + PAP + versioning")]
  end

  subgraph TEST["GCP Project: enki-test"]
    TF["Terraform authoritative plan/apply"]
    AR["Artifact Registry"]
    SM["Secret Manager"]
    RUN["Cloud Run\nENKI runtime"]
    SQL[("Cloud SQL PostgreSQL\nconditional on persistence confirmation")]
    OBJ[("Cloud Storage\nwhen durable object storage is required")]
    OBS["Cloud Logging + Monitoring"]
    IAM["Runtime service identities + IAM"]
  end

  COPILOT --> PR
  ENKI --> PR
  PR --> VALIDATE
  VALIDATE --> HUMAN
  HUMAN -->|authorized merge| SANDBOX
  SANDBOX --> WORKFLOW
  WORKFLOW --> OIDC
  OIDC --> WIF
  WIF --> DEPLOYER
  DEPLOYER --> TF
  TF <--> STATE
  TF --> AR
  TF --> SM
  TF --> RUN
  TF -. if confirmed .-> SQL
  TF -. if required .-> OBJ
  TF --> OBS
  TF --> IAM
```

## Runtime and Release Separation

```mermaid
flowchart LR
  subgraph INFRA["Infrastructure authority path"]
    IPR["Infrastructure PR"] --> IMERGE["Human merge to sandbox"] --> TF["Terraform"] --> PLATFORM["GCP TEST platform"]
  end

  subgraph APP["Application release authority path"]
    SRC["ENKI source"] --> TESTS["Tests + governed validation"] --> BUILD["Build immutable container"] --> REG["Artifact Registry"] --> DIGEST["Image digest"] --> DEPLOY["Deploy validated digest"]
  end

  PLATFORM --> DEPLOY
  DEPLOY --> RUNNING["Running ENKI TEST"]
```

Terraform governs **where ENKI runs**. The application release pipeline governs **which validated ENKI artifact runs there**. These are separate authority paths.

## Initial Resource Sequence

The TEST platform should be introduced incrementally after the control plane is operationally proven:

```mermaid
flowchart LR
  A["Bootstrap trust"] --> B["Prove WIF + Terraform apply"] --> C["Artifact Registry"] --> D["Runtime IAM + Secret Manager"] --> E["Cloud Run"] --> F["Persistence decision"] --> G["Cloud SQL if confirmed"] --> H["Observability"] --> I["Object storage if required"] --> J["DNS / ingress after runtime proof"]
```

## Environment Evolution

```mermaid
flowchart LR
  TEST["enki-test\ninitial governed environment"] --> HARDEN["Least-privilege IAM hardening\nrelease + recovery proof"] --> STAGE["enki-stage\nproduction-equivalent validation"] --> PROD["enki-prod\ngoverned production authority"]
```

TEST bootstrap permissions must not be copied into STAGE or PROD without explicit hardening.

## Trust-Boundary Invariants

1. Pull-request workflows receive no GCP deployer identity.
2. The deployer WIF condition requires the exact repository, `push` event, `refs/heads/sandbox`, and exact Terraform workflow reference.
3. A passing PR check does not authorize infrastructure mutation.
4. Human-authorized merge is the TEST authority transition.
5. GitHub Actions receives short-lived authority only; no permanent service-account key is stored in GitHub.
6. Terraform state is protected by uniform bucket access, public-access prevention, and versioning.
7. Application releases deploy validated immutable artifacts rather than rebuilding independently per environment.

## Related Documentation

- `docs/infrastructure/gcp-execution-control-plane.md`
- `docs/roadmaps/gcp-hosted-platform-roadmap.md`
- `docs/governance/architecture-roadmap-synchronization.md`
- `infrastructure/bootstrap/README.md`

## Evidence Boundary

This reference architecture becomes an operationally proven topology only when bootstrap execution, Workload Identity Federation authentication, Terraform apply, and subsequent resource-deployment evidence exist. Until then, it is the selected and prepared architecture, not a claim of deployed state.