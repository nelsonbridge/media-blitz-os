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
      ├─ Creates Workload Identity Pool + OIDC provider
      ├─ Creates terraform-deployer service account
      ├─ Binds nelsonbridge/media-blitz-os → service account (WIF)
      └─ Grants Terraform IAM roles

      ▼
GitHub Actions (PR merge)
      │
      ├─ Authenticates via OIDC token → Workload Identity Federation
      ├─ Impersonates terraform-deployer service account (keyless)
      └─ Runs terraform plan / terraform apply
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

# Run bootstrap (takes ~2–3 minutes)
./infrastructure/bootstrap/bootstrap-gcp.sh
```

The script is **idempotent** — re-running it is safe and will skip resources
that already exist.

---

## What the script creates

| Step | Resource | GCP name |
|---|---|---|
| 1 | GCP API enablement | 14 prerequisite APIs |
| 2 | Terraform state bucket | `enki-test-terraform-state` |
| 3 | State bucket versioning | enabled on bucket above |
| 4 | Workload Identity Pool | `github-actions-pool` |
| 5 | OIDC provider | `github-actions-oidc` |
| 6 | Terraform service account | `terraform-deployer@enki-test.iam.gserviceaccount.com` |
| 7 | Repository binding | `attribute.repository == nelsonbridge/media-blitz-os` |
| 8 | IAM roles | see table below |

### Terraform service account IAM roles

| Role | Purpose |
|---|---|
| `roles/editor` | Broad create/update/delete for managed resources |
| `roles/iam.securityAdmin` | Manage IAM policies on individual resources |
| `roles/resourcemanager.projectIamAdmin` | Set project-level IAM bindings |
| `roles/storage.admin` | Manage GCS (state bucket + application buckets) |
| `roles/secretmanager.admin` | Manage Secret Manager secrets |
| `roles/artifactregistry.admin` | Manage Artifact Registry repositories |
| `roles/run.admin` | Manage Cloud Run services |
| `roles/cloudsql.admin` | Manage Cloud SQL instances |

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

- The OIDC provider attribute-condition is set to
  `assertion.repository == 'nelsonbridge/media-blitz-os'`, so only tokens
  issued for this exact repository are accepted.
- The WIF binding uses `principalSet://…/attribute.repository/…` (defence in
  depth: two independent enforcement points).
- The state bucket uses uniform bucket-level access (no ACLs).
- No service-account key is ever generated or stored.

---

## Subsequent infrastructure work

All Cloud Run, Cloud SQL, Artifact Registry, Secret Manager, networking, and
application resources are defined in Terraform under `infrastructure/terraform/`
and applied exclusively through the GitHub Actions workflow in
`.github/workflows/terraform.yml`.
