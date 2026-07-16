# Enki Multi-Finalist Hosted Validation

Status: **NON-PRODUCTION VALIDATION PREPARATION**

Decision: `VALIDATE_MULTIPLE_FINALISTS`

Execution context: `TEST`

External-services budget: `$0`

Production approval: `NO`

## Purpose

Convert the Sprint 24 architecture shortlist into one comparable validation program before any hosting winner is selected.

Finalists:

- `CF-NATIVE`
- `CF-NEON-R2`
- `GCP-NEON-R2`

The canonical validation contract is `contracts/enki-hosting-validation-v1.json`. The executable validation model is `nks.application.hosting_validation`.

## Required ordered phases

1. Preflight.
2. Deploy TEST runtime.
3. Import synthetic fixtures through governed paths.
4. Validate namespace, tenant, subject, domain, audience, and execution-context isolation.
5. Exercise transaction interruption, exact retry, rollback, and recovery.
6. Exercise export, import, clean reconstruction, and disaster-recovery paths.
7. Validate privacy-preserving logs, metrics, and traces.
8. Inject declared failure modes.
9. Capture cost, quota, latency, and egress evidence.
10. Tear down the hosted TEST environment and reconstruct from governed exports.

## Capability gate

Repository-local preparation can proceed without provider access. Actual hosted execution requires, for each finalist, all of the following TEST-only capabilities:

- provider TEST identity;
- provider TEST credentials;
- teardown authority.

Missing any one of these capabilities yields `BLOCKED_EXTERNAL_CAPABILITY`. No missing capability may be silently bypassed and no production credential may satisfy this TEST gate.

## Production boundary

This program does not select a production host. It does not validate the seven unresolved Sprint 23 production prerequisites and cannot create production approval. Comparable hosted TEST evidence, or a later explicit human waiver naming missing evidence, is required before finalist selection.
