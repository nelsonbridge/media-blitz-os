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
log "Step 2 — Creating Terraform state bucket: gs://${STATE_BUCKET}"
if ! gsutil ls -b "gs://${STATE_BUCKET}" &>/dev/null; then
  gsutil mb \
    -p "${GCP_PROJECT}" \
    -l "${GCP_REGION}" \
    -b on \
    "gs://${STATE_BUCKET}"
  log "Bucket created."
else
  log "Bucket already exists — skipping creation."
fi

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
# 5. Create GitHub OIDC provider inside the pool
# ---------------------------------------------------------------------------
log "Step 5 — Creating OIDC provider: ${WIF_PROVIDER_ID}…"
if ! gcloud iam workload-identity-pools providers describe "${WIF_PROVIDER_ID}" \
     --workload-identity-pool="${WIF_POOL_ID}" \
     --location=global \
     --project="${GCP_PROJECT}" &>/dev/null; then
  gcloud iam workload-identity-pools providers create-oidc "${WIF_PROVIDER_ID}" \
    --workload-identity-pool="${WIF_POOL_ID}" \
    --location=global \
    --project="${GCP_PROJECT}" \
    --issuer-uri="${GITHUB_OIDC_ISSUER}" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
    --attribute-condition="assertion.repository == '${GITHUB_REPO}'" \
    --display-name="GitHub Actions OIDC"
  log "OIDC provider created."
else
  log "OIDC provider already exists — skipping creation."
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
# ---------------------------------------------------------------------------
log "Step 8 — Granting Terraform permissions to ${SA_EMAIL}…"

TERRAFORM_ROLES=(
  "roles/editor"                    # broad create/update/delete for managed resources
  "roles/iam.securityAdmin"         # manage IAM policies on resources
  "roles/resourcemanager.projectIamAdmin"  # set project-level IAM bindings
  "roles/storage.admin"             # manage GCS (state bucket + application buckets)
  "roles/secretmanager.admin"       # manage secrets
  "roles/artifactregistry.admin"    # manage Artifact Registry
  "roles/run.admin"                 # manage Cloud Run services
  "roles/cloudsql.admin"            # manage Cloud SQL instances
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
