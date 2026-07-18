#!/usr/bin/env bash
# bootstrap-gcp.sh
#
# One-time bootstrap for Enki GCP infrastructure.
#
# Establishes the root of trust that Terraform itself cannot create before it
# has access:
#   1. Enable prerequisite GCP APIs
#   2. Create Terraform state bucket
#   3. Enable state bucket versioning
#   4. Create GitHub Workload Identity Pool
#   5. Create GitHub OIDC provider
#   6. Create Terraform deployment service account
#   7. Bind the exact Enki GitHub repository to that service account
#   8. Grant minimum Terraform permissions to the service account
#
# Prerequisites
#   - gcloud CLI authenticated as a GCP project owner/admin
#   - The GCP project already exists and has billing attached
#
# Usage
#   export GCP_PROJECT=enki-test
#   export GITHUB_REPO=nelsonbridge/media-blitz-os   # owner/repo
#   ./infrastructure/bootstrap/bootstrap-gcp.sh

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration — override via environment variables before running
# ---------------------------------------------------------------------------
GCP_PROJECT="${GCP_PROJECT:-enki-test}"
GCP_REGION="${GCP_REGION:-us-central1}"
GITHUB_REPO="${GITHUB_REPO:-nelsonbridge/media-blitz-os}"

# Derived names — kept consistent so the script is idempotent
STATE_BUCKET="${GCP_PROJECT}-terraform-state"
WIF_POOL_ID="github-actions-pool"
WIF_PROVIDER_ID="github-actions-oidc"
SA_NAME="terraform-deployer"
SA_EMAIL="${SA_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com"

# GitHub OIDC issuer (fixed by GitHub)
GITHUB_OIDC_ISSUER="https://token.actions.githubusercontent.com"

# Deployer WIF trust constraints
# The OIDC provider attribute-condition is intentionally narrow:
#   - only tokens issued for this exact repository
#   - only push events (not PR, schedule, workflow_dispatch, etc.)
#   - only the protected sandbox branch
#   - only the terraform.yml workflow file on that branch
# This ensures that Copilot PRs and other branch workflows cannot obtain the
# deployer identity regardless of what steps they contain.
DEPLOY_BRANCH="refs/heads/sandbox"
DEPLOY_WORKFLOW="${GITHUB_REPO}/.github/workflows/terraform.yml@${DEPLOY_BRANCH}"

DEPLOYER_ATTRIBUTE_MAPPING=(
  "google.subject=assertion.sub"
  "attribute.actor=assertion.actor"
  "attribute.repository=assertion.repository"
  "attribute.repository_owner=assertion.repository_owner"
  "attribute.ref=assertion.ref"
  "attribute.event_name=assertion.event_name"
  "attribute.workflow_ref=assertion.workflow_ref"
)
# Join with commas for the gcloud flag
DEPLOYER_ATTRIBUTE_MAPPING_STR=$(IFS=,; echo "${DEPLOYER_ATTRIBUTE_MAPPING[*]}")

DEPLOYER_CONDITION="assertion.repository == '${GITHUB_REPO}' \
&& assertion.event_name == 'push' \
&& assertion.ref == '${DEPLOY_BRANCH}' \
&& assertion.workflow_ref == '${DEPLOY_WORKFLOW}'"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
log() { echo "[bootstrap] $*"; }

# ---------------------------------------------------------------------------
# 0. Target project
# ---------------------------------------------------------------------------
log "Targeting project: ${GCP_PROJECT}"
gcloud config set project "${GCP_PROJECT}"

# ---------------------------------------------------------------------------
# 1. Enable prerequisite GCP APIs
# ---------------------------------------------------------------------------
log "Step 1 — Enabling prerequisite APIs…"
REQUIRED_APIS=(
  "cloudresourcemanager.googleapis.com"
  "iam.googleapis.com"
  "iamcredentials.googleapis.com"
  "sts.googleapis.com"
  "storage.googleapis.com"
  "serviceusage.googleapis.com"
  "secretmanager.googleapis.com"
  "sqladmin.googleapis.com"
  "run.googleapis.com"
  "artifactregistry.googleapis.com"
  "monitoring.googleapis.com"
  "logging.googleapis.com"
  "compute.googleapis.com"
  "servicenetworking.googleapis.com"
)
gcloud services enable "${REQUIRED_APIS[@]}" --project="${GCP_PROJECT}"
log "APIs enabled."

# ---------------------------------------------------------------------------
# 2. Create Terraform state bucket
# ---------------------------------------------------------------------------
log "Step 2 — Ensuring Terraform state bucket exists: gs://${STATE_BUCKET}"
if ! gsutil ls -b "gs://${STATE_BUCKET}" &>/dev/null; then
  gsutil mb \
    -p "${GCP_PROJECT}" \
    -l "${GCP_REGION}" \
    -b on \
    "gs://${STATE_BUCKET}"
  log "Bucket created."
else
  log "Bucket already exists."
fi

# Always enforce security controls regardless of whether the bucket was just
# created or already existed — this makes reruns convergent, not merely
# non-destructive.
log "  Enforcing uniform bucket-level access…"
gsutil uniformbucketlevelaccess set on "gs://${STATE_BUCKET}"
log "  Enforcing public access prevention…"
gsutil pap set enforced "gs://${STATE_BUCKET}"

# ---------------------------------------------------------------------------
# 3. Enable state bucket versioning
# ---------------------------------------------------------------------------
log "Step 3 — Enabling versioning on gs://${STATE_BUCKET}…"
gsutil versioning set on "gs://${STATE_BUCKET}"
log "Versioning enabled."

# ---------------------------------------------------------------------------
# 4. Create GitHub Workload Identity Pool
# ---------------------------------------------------------------------------
log "Step 4 — Creating Workload Identity Pool: ${WIF_POOL_ID}…"
if ! gcloud iam workload-identity-pools describe "${WIF_POOL_ID}" \
     --location=global \
     --project="${GCP_PROJECT}" &>/dev/null; then
  gcloud iam workload-identity-pools create "${WIF_POOL_ID}" \
    --location=global \
    --project="${GCP_PROJECT}" \
    --display-name="GitHub Actions Pool" \
    --description="Workload Identity Pool for GitHub Actions CI/CD"
  log "Workload Identity Pool created."
else
  log "Workload Identity Pool already exists — skipping creation."
fi

# Retrieve the pool's full resource name for use in later steps
WIF_POOL_NAME=$(gcloud iam workload-identity-pools describe "${WIF_POOL_ID}" \
  --location=global \
  --project="${GCP_PROJECT}" \
  --format="value(name)")

# ---------------------------------------------------------------------------
# 5. Create GitHub OIDC provider inside the pool, or update to expected config
#
# The attribute-condition restricts the deployer identity to:
#   - this exact repository
#   - push events only (not pull_request, schedule, workflow_dispatch, etc.)
#   - refs/heads/sandbox only
#   - the terraform.yml workflow file on that branch
#
# On rerun, any existing provider is always updated to the expected mapping
# and condition, making the script convergent rather than merely non-destructive.
# ---------------------------------------------------------------------------
log "Step 5 — Configuring OIDC provider: ${WIF_PROVIDER_ID}…"
if ! gcloud iam workload-identity-pools providers describe "${WIF_PROVIDER_ID}" \
     --workload-identity-pool="${WIF_POOL_ID}" \
     --location=global \
     --project="${GCP_PROJECT}" &>/dev/null; then
  gcloud iam workload-identity-pools providers create-oidc "${WIF_PROVIDER_ID}" \
    --workload-identity-pool="${WIF_POOL_ID}" \
    --location=global \
    --project="${GCP_PROJECT}" \
    --issuer-uri="${GITHUB_OIDC_ISSUER}" \
    --attribute-mapping="${DEPLOYER_ATTRIBUTE_MAPPING_STR}" \
    --attribute-condition="${DEPLOYER_CONDITION}" \
    --display-name="GitHub Actions OIDC (deployer)"
  log "OIDC provider created."
else
  log "OIDC provider already exists — enforcing expected mapping and condition…"
  gcloud iam workload-identity-pools providers update-oidc "${WIF_PROVIDER_ID}" \
    --workload-identity-pool="${WIF_POOL_ID}" \
    --location=global \
    --project="${GCP_PROJECT}" \
    --issuer-uri="${GITHUB_OIDC_ISSUER}" \
    --attribute-mapping="${DEPLOYER_ATTRIBUTE_MAPPING_STR}" \
    --attribute-condition="${DEPLOYER_CONDITION}"
  log "OIDC provider configuration enforced."
fi

# ---------------------------------------------------------------------------
# 6. Create Terraform deployment service account
# ---------------------------------------------------------------------------
log "Step 6 — Creating service account: ${SA_EMAIL}…"
if ! gcloud iam service-accounts describe "${SA_EMAIL}" \
     --project="${GCP_PROJECT}" &>/dev/null; then
  gcloud iam service-accounts create "${SA_NAME}" \
    --project="${GCP_PROJECT}" \
    --display-name="Terraform Deployer" \
    --description="Service account used by GitHub Actions to run Terraform against ${GCP_PROJECT}"
  log "Service account created."
else
  log "Service account already exists — skipping creation."
fi

# ---------------------------------------------------------------------------
# 7. Bind the exact Enki GitHub repository to the service account
#    (attribute.repository == GITHUB_REPO, enforced by the provider condition
#    AND by the principalSet binding below — defence in depth)
# ---------------------------------------------------------------------------
log "Step 7 — Binding repository '${GITHUB_REPO}' → service account…"
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --project="${GCP_PROJECT}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WIF_POOL_NAME}/attribute.repository/${GITHUB_REPO}"
log "Binding applied."

# ---------------------------------------------------------------------------
# 8. Grant minimum Terraform permissions to the service account
#
# Role justification:
#   roles/editor is used here as a bootstrap grant because Terraform must be
#   able to create, update, and delete the full set of managed resources
#   (Cloud Run, Cloud SQL, Artifact Registry, Secret Manager, networking,
#   storage) whose exact shapes are not yet known at bootstrap time.
#   roles/iam.securityAdmin and roles/resourcemanager.projectIamAdmin are
#   added separately because roles/editor alone does not grant the ability
#   to write IAM policies, which Terraform needs for resource-level bindings.
#
#   IMPORTANT: Once the Terraform resource set is stable, replace roles/editor
#   with the minimum resource-specific roles actually required (e.g.
#   roles/run.developer, roles/cloudsql.client, etc.) and remove this comment.
#   This tightening should be treated as a follow-on security hardening task.
# ---------------------------------------------------------------------------
log "Step 8 — Granting Terraform permissions to ${SA_EMAIL}…"

TERRAFORM_ROLES=(
  "roles/editor"                           # bootstrap broad grant — see note above
  # roles/iam.securityAdmin and roles/resourcemanager.projectIamAdmin are the
  # only permissions NOT covered by roles/editor that Terraform needs to manage
  # resource-level and project-level IAM bindings.
  "roles/iam.securityAdmin"                # write IAM policies on individual resources
  "roles/resourcemanager.projectIamAdmin"  # write project-level IAM bindings
)

for ROLE in "${TERRAFORM_ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "${GCP_PROJECT}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${ROLE}" \
    --condition=None
  log "  Granted ${ROLE}"
done

# Also grant the service account the ability to read its own token (required for impersonation flows)
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --project="${GCP_PROJECT}" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --member="serviceAccount:${SA_EMAIL}"

log "Permissions granted."

# ---------------------------------------------------------------------------
# Output — values needed for GitHub Actions and Terraform configuration
# ---------------------------------------------------------------------------
WIF_PROVIDER_NAME=$(gcloud iam workload-identity-pools providers describe "${WIF_PROVIDER_ID}" \
  --workload-identity-pool="${WIF_POOL_ID}" \
  --location=global \
  --project="${GCP_PROJECT}" \
  --format="value(name)")

echo ""
echo "============================================================"
echo " Bootstrap complete. Add the following to your repository:"
echo "============================================================"
echo ""
echo " GitHub Actions Variables (Settings → Secrets and variables → Actions → Variables):"
echo "   GCP_PROJECT           = ${GCP_PROJECT}"
echo "   GCP_REGION            = ${GCP_REGION}"
echo "   GCP_WIF_PROVIDER      = ${WIF_PROVIDER_NAME}"
echo "   GCP_SERVICE_ACCOUNT   = ${SA_EMAIL}"
echo "   TF_STATE_BUCKET       = ${STATE_BUCKET}"
echo ""
echo " No secrets are required — authentication uses keyless OIDC/WIF."
echo "============================================================"
