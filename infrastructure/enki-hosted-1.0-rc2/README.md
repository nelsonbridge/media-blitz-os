# Enki Hosted RC2 Infrastructure-as-Code Package

This directory contains the versioned Sprint 38 infrastructure definition for the human-approved `enki-hosted-1.0-rc2` architecture baseline.

## Locked architecture

- Architecture ID: `CF-NEON-R2`
- Compute and edge runtime: Cloudflare Workers
- Canonical structured-data system of record: Neon Postgres
- Evidence and object plane: Cloudflare R2
- Optional provider services: none

The definition is bound to:

- Candidate SHA-256: `sha256:c443b2ff6eeb00e6682f6c56dc00cd14bdee53940432e1b9d12e9f473c9346b4`
- Architecture-lock SHA-256: `sha256:8b79cdbcafd9080a22471fa12e3a176ee1da9963471fa494b90dca62af0d4813`

## Current execution mode

Sprint 38 deliberately separates **infrastructure definition** from **provider execution**.

The repository can currently execute the complete lifecycle against a credential-free no-effect adapter:

`PLAN -> CREATE -> VERIFY -> TEARDOWN -> REBUILD`

That path proves deterministic declarations, drift rejection, teardown behavior, reconstructable pre-teardown export identity, and clean rebuild without creating Cloudflare or Neon resources.

Real provider-side TEST creation remains disabled until the external capability gates supply:

- Cloudflare TEST identity and credentials;
- Neon TEST identity and credentials;
- explicit teardown authority;
- a governed secret mechanism;
- confirmation that execution remains within the standing `$0` external-services boundary.

## Secret bindings

The package contains references only. No credential value belongs in this repository.

Required TEST bindings:

- `github-actions://CLOUDFLARE_ACCOUNT_ID`
- `github-actions://CLOUDFLARE_API_TOKEN`
- `github-actions://NEON_DATABASE_URL`
- `github-actions://NEON_API_KEY`

Credential values must be supplied through GitHub Actions Secrets or another separately approved secret mechanism. They must not be committed to source, issues, pull requests, logs, generated evidence, or artifacts.

## Environment authority separation

### TEST

Provider execution is currently disabled. Enabling a real TEST adapter requires external TEST credentials and explicit teardown authority. TEST execution may not use production data, production credentials, or production authority.

### PRODUCTION

Provider execution remains disabled. The RC2 approval and Sprint 38 infrastructure definition do not authorize production execution. Production requires separate human authority plus qualifying production-control evidence.

## Drift and undeclared services

The declared provider service set is exact:

- `CLOUDFLARE:WORKERS`
- `NEON:POSTGRES`
- `CLOUDFLARE:R2`

Missing services, extra services, hidden manual resources, or optional provider services fail closed. Adding any provider service requires a separate governed architecture decision and a new hash-bound infrastructure definition.

## Zero-cost boundary

Every declared resource and environment policy retains an external-services budget ceiling of `$0`. No lifecycle operation represented by this package authorizes a charge.

## Teardown and reconstruction

The no-effect lifecycle produces a deterministic pre-teardown export-manifest hash before clearing the TEST environment state. A clean rebuild must reproduce the exact declared environment fingerprint. This preserves the contract that a TEST environment can be destroyed without losing the ability to reconstruct governed state from separately controlled exports and receipts.
