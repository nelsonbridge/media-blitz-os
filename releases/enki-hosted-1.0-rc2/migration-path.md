# Migration Path

## Current state

Enki remains provider-neutral and repository-local for validated execution. The hosting direction is `VALIDATE_MULTIPLE_FINALISTS`; no production provider has been selected.

## Required sequence

1. Complete CF-NATIVE, CF-NEON-R2, and GCP-NEON-R2 hosted TEST campaigns under the common validation contract, or record an explicit human waiver naming omitted evidence.
2. Complete cross-finalist comparative evaluation without converting assumptions into measured evidence.
3. Obtain an explicit human hosting-direction decision.
4. Validate all seven production controls against the selected architecture with qualifying production-scope evidence.
5. Produce provider-specific infrastructure, migration, disaster-recovery, support, and rollback evidence.
6. Request an explicit human production-deployment decision.
7. Only after approval, migrate through governed export/import and reconstruction paths with exact canonical fingerprint comparison.

## Portability principle

Canonical structured state, evidence objects, receipts, manifests, and reconstruction lineage remain separable from provider-specific runtime bindings. Provider selection must not silently redefine Enki's canonical authority model or downstream consumer contracts.
