# Enki Hosted Architecture Decision Package

Package: `enki-hosting-options-v1`

Decision state: **HUMAN_DECISION_REQUIRED**

External-services budget used by this sprint: **$0**

Production infrastructure provisioned: **NO**

Production approval: **NO**

This package evaluates hosted deployment options for Enki using current official provider pricing and service documentation captured for architecture decision support. It compares single-cloud, provider-split, control-plane/data-plane split, and portability-preserving patterns.

## Evaluated options

1. `CF-NATIVE` — Cloudflare Workers + D1 + R2.
2. `GCP-NATIVE` — Google Cloud Run + Firestore + Cloud Storage.
3. `AWS-NATIVE` — AWS Lambda + DynamoDB + S3 candidate.
4. `CF-NEON-R2` — Cloudflare Workers + Neon Postgres + Cloudflare R2.
5. `GCP-NEON-R2` — Google Cloud Run + Neon Postgres + Cloudflare R2.
6. `PORTABLE-CONTAINER-POSTGRES-OBJECT` — provider-neutral container/Postgres/object-store pattern.

## Shortlist

- `CF-NATIVE`: lowest-operations zero-cost prototype candidate, with the largest runtime/data adaptation from the current Python/Postgres-shaped design.
- `CF-NEON-R2`: explicit provider split with relational canonical custody, but requires Workers runtime adaptation and cross-provider operations.
- `GCP-NEON-R2`: lowest-change split-cloud path for the current Python/Pydantic runtime, but introduces three-provider operational and trust complexity.

No winner is selected by this package. The subsequent human hosting-direction decision must choose, defer, or reject the shortlist. A later validation sprint must test the selected architecture before any production-hosting decision.

## Package contents

- `options-matrix.md`
- `single-cloud-reference-architecture.md`
- `split-cloud-reference-architecture.md`
- `threat-trust-failure-analysis.md`
- `cost-model.md`
- `migration-rollback.md`
- `hosting-direction-decision-request.md`

The unresolved Sprint 23 controls remain unresolved. Architecture diagrams and provider feature availability are not validation evidence for cloud IAM, production identity federation, managed database isolation, network segmentation, per-tenant production keys, production secrets management, or independent penetration testing.
