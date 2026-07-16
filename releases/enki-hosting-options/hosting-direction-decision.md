# Enki Hosting-Direction Decision

Decision date: 2026-07-16

Decision-maker: `nelsonbridge`

Disposition: **VALIDATE MULTIPLE FINALISTS**

Source instruction: **Execute Nonstop @GitHub**

## Decision

Proceed with controlled, non-production validation of all three Sprint 24 finalists:

1. `CF-NATIVE` — Cloudflare Workers + D1 + R2.
2. `CF-NEON-R2` — Cloudflare Workers + Neon Postgres + R2.
3. `GCP-NEON-R2` — Google Cloud Run + Neon Postgres + R2.

This decision is intentionally the least-committing path that preserves the Sprint 24 shortlist while converting architecture assumptions into comparable evidence. It authorizes validation work and repository changes required to prepare and execute those validations.

## Authority boundary

This decision does **not**:

- select a production hosting architecture;
- authorize production deployment;
- authorize production data, credentials, or traffic;
- validate cloud IAM, production identity federation, managed database isolation, network segmentation, per-tenant production key management, production secrets management, or independent penetration testing;
- authorize paid infrastructure or spending beyond the standing `$0 external-services` boundary without a later explicit human decision.

## Execution rule

Validation proceeds continuously through the next unblocked sprint packets. Work stops only at an explicit human approval gate, unavailable external capability, a failed invariant requiring human choice, or a material security ambiguity.

Hosted execution that requires provider credentials remains separately capability-gated. Repository-local preparation, deterministic validation contracts, no-effect adapters, preflight checks, failure matrices, and evidence packaging may proceed immediately.
