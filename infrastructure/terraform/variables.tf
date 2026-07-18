variable "project" {
  description = "GCP project ID (set via TF_VAR_project in CI)."
  type        = string
}

variable "region" {
  description = "Default GCP region (set via TF_VAR_region in CI)."
  type        = string
  default     = "us-central1"
}
