# GCP Bootstrap

Establishes the one-time root of trust that makes GitHub Actions the execution
bridge into GCP. After this runs once, all infrastructure provisioning flows
through Terraform + GitHub Actions with no stored service-account keys.

---

## Architecture

```
You (one-time)
      │
      ▼
bootstrap-gcp.sh
      │
      ├─ Enables GCP APIs
      ├─ Creates Terraform state bucket (GCS)
      ├─ Creates Workload Identity Pool + OIDC provider (deployer)
      ├─ Creates terraform-deployer service account
      ├─ Binds sandbox push events → deployer account (WIF, narrowed)
      └─ Grants Terraform IAM roles

      ▼
Pull Request (Copilot / any branch)
      │
      ├─ pr-validate job: fmt, init -backend=false, validate
      ├─ No GCP credentials provided
      └─ Cannot obtain terraform-deployer identity
             (WIF condition enforces event_name == push)

      ▼
You merge → sandbox
      │
      ▼
deploy job (sandbox push)
      │
      ├─ Authenticates via OIDC → WIF → terraform-deployer (keyless)
      ├─ terraform init / validate / plan
      └─ terraform apply
             │
             ▼
            GCP
```

No permanent GCP service-account key is ever stored in GitHub. Google
explicitly recommends Workload Identity Federation for CI/CD systems running
outside Google Cloud.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| GCP project `enki-test` exists | You create this manually |
| Billing attached to project | Required for most APIs |
| `gcloud` CLI installed | `brew install google-cloud-sdk` or equivalent |
| Authenticated as project owner | `gcloud auth login` |

---

## Running the script

```bash
# Authenticate with your GCP admin account
gcloud auth login

# Set the target project
export GCP_PROJECT=enki-test

# Optional overrides (defaults shown)
export GCP_REGION=us-central1
export GITHUB_REPO=nelsonbridge/media-blitz-os

# Run bootstrap (takes ~2-3 minutes)
./infrastructure/bootstrap/bootstrap-gcp.sh
```

The script is **convergent** — re-running it is safe. Resources are created if
absent and security controls (uniform access, public-access-prevention,
versioning, WIF provider configuration) are enforced on every run.

---

## What the script creates

| Step | Resource | GCP name |
|---|---|---|
| 1 | GCP API enablement | 14 prerequisite APIs |
| 2 | Terraform state bucket | `enki-test-terraform-state` |
| 3 | State bucket versioning | enabled (always enforced) |
| 4 | Workload Identity Pool | `github-actions-pool` |
| 5 | OIDC provider (deployer) | `github-actions-oidc` |
| 6 | Terraform service account | `terraform-deployer@enki-test.iam.gserviceaccount.com` |
| 7 | Repository/branch binding | see WIF condition below |
| 8 | IAM roles | see table below |

### Terraform service account IAM roles

| Role | Purpose |
|---|---|
| `roles/editor` | Bootstrap broad grant — create/update/delete for all managed resources (Cloud Run, Cloud SQL, Artifact Registry, Secret Manager, networking, GCS). Replace with resource-specific roles once the Terraform resource set is stable. |
| `roles/iam.securityAdmin` | Write IAM policies on individual resources (not covered by `roles/editor`) |
| `roles/resourcemanager.projectIamAdmin` | Write project-level IAM bindings (not covered by `roles/editor`) |

---

## After bootstrap — configure GitHub Actions Variables

The script prints the exact values to add. Navigate to:

> **Repository → Settings → Secrets and variables → Actions → Variables**

| Variable | Example value |
|---|---|
| `GCP_PROJECT` | `enki-test` |
| `GCP_REGION` | `us-central1` |
| `GCP_WIF_PROVIDER` | `projects/…/locations/global/workloadIdentityPools/github-actions-pool/providers/github-actions-oidc` |
| `GCP_SERVICE_ACCOUNT` | `terraform-deployer@enki-test.iam.gserviceaccount.com` |
| `TF_STATE_BUCKET` | `enki-test-terraform-state` |

No secrets are required — authentication is fully keyless.

---

## Security constraints

### Deployer WIF trust boundary

The OIDC provider attribute-condition enforces **four independent claims**
before granting the deployer identity:

| Claim | Required value |
|---|---|
| `assertion.repository` | `nelsonbridge/media-blitz-os` |
| `assertion.event_name` | `push` |
| `assertion.ref` | `refs/heads/sandbox` |
| `assertion.workflow_ref` | `nelsonbridge/media-blitz-os/.github/workflows/terraform.yml@refs/heads/sandbox` |

This means:

- **Pull request workflows** cannot obtain the deployer identity
  (`event_name == pull_request`, not `push`).
- **Other branches** cannot obtain the deployer identity
  (`ref` is not `refs/heads/sandbox`).
- **Other workflow files** cannot obtain the deployer identity
  (`workflow_ref` must be exactly `terraform.yml` on `sandbox`).
- **Copilot PRs** are therefore structurally excluded — only the repo owner's
  merge into sandbox triggers the authority transition.

The WIF binding uses `principalSet://…/attribute.repository/…` as a second,
independent enforcement point (defence in depth).

### State bucket

- Uniform bucket-level access enforced (no per-object ACLs).
- Public access prevention set to `enforced`.
- Versioning enabled.
- All three controls are re-applied on every bootstrap run (convergent).

### No stored keys

No service-account key is ever generated or stored. Authentication is entirely
through short-lived OIDC tokens exchanged via Workload Identity Federation.

---

## Subsequent infrastructure work

All Cloud Run, Cloud SQL, Artifact Registry, Secret Manager, networking, and
application resources are defined in Terraform under `infrastructure/terraform/`
and applied exclusively through the `deploy` job in
`.github/workflows/terraform.yml`, which requires a merge to `sandbox` by the
repo owner.
