# Partial backend configuration.
# bucket and prefix are supplied at init time via -backend-config flags
# so that this file can be validated offline with -backend=false.
terraform {
  backend "gcs" {}
}
