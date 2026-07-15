# Sprint 16 Test-Data Validation Decision

- Decision date: 2026-07-15
- Applies to: `NKS-SPR-016`, `BL-016`, and the Enki 1.0 readiness package
- Authority: explicit human direction in the governed project conversation

## Decision

Path-complete adversarial validation using governed TEST data is sufficient to complete Sprint 16.

Sprint 16 validates Enki software isolation semantics across namespace, tenant, subject, domain, audience, and execution context. It does not wait for a production cloud account, managed database, commercial identity provider, managed key service, network control plane, or external penetration vendor.

## Required TEST proof

The evidence must exercise:

- shared logical storage and physically separated local storage;
- identical record identifiers across different tenants;
- cross-tenant, cross-subject, cross-domain, cross-audience, and TEST-to-PRODUCTION denial;
- forged identities and locally signed envelopes using disposable per-tenant TEST keys;
- export, import, migration-shaped package handling, replay, rollback-shaped denial, and recovery;
- exact duplicate idempotency and divergent duplicate conflict;
- path traversal, hash tampering, stale or mismatched authority, and privilege escalation;
- privacy-preserving diagnostics without protected content leakage;
- human consent, purpose, correction, retraction, revocation, and ownership rules that remain stricter than tenant authorization;
- a distinct local-process adversarial probe;
- zero network use, zero production credentials, zero paid services, and zero external effects.

## Completion meaning

A completed Sprint 16 means:

> Enki software isolation has passed the declared, automated, adversarial TEST matrix using representative governed test data.

It does not mean:

- a particular cloud IAM deployment is configured correctly;
- a production database has row-level isolation enabled;
- production network segmentation has been certified;
- production per-tenant keys have been installed;
- independent infrastructure penetration testing has occurred;
- Enki has received production release authority.

Those are deployment-readiness questions and must not reopen or invalidate Sprint 16 software completion.

## Sprint 23 reporting

Sprint 23 will report two independent conclusions:

1. `ENKI_SOFTWARE_ISOLATION`: validated or failed from Sprint 16 evidence.
2. `SPECIFIC_PRODUCTION_DEPLOYMENT`: ready, blocked, failed, or not assessed from deployment-specific evidence.

TEST evidence cannot be relabeled as production-deployment evidence, but unavailable production infrastructure cannot block the TEST software-validation lane.
