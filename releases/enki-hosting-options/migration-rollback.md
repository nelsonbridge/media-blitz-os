# Migration and Rollback Considerations

## Current starting point

Enki is presently validated through repository-local TEST services, deterministic fixtures, local adapters, GitHub-hosted CI, and no-effect downstream integrations. No production hosting state exists to preserve.

## Migration sequence shared by finalists

1. Freeze an exact Enki candidate and evidence manifest.
2. Deploy a non-production runtime adapter with TEST execution context only.
3. Load synthetic canonical fixtures through governed import paths rather than direct database writes.
4. Configure provider identities and secrets using disposable TEST credentials.
5. Exercise namespace, tenant, subject, domain, audience, and execution-context isolation.
6. Exercise exact retry, interruption, rollback, reconstruction, export, import, and disaster-recovery paths.
7. Measure latency, egress, resource use, quota behavior, and failure recovery.
8. Validate that provider logs and telemetry preserve privacy restrictions.
9. Destroy the hosted TEST environment and prove clean reconstruction from governed exports.
10. Only after successful evidence review consider a separate production-control validation program.

## CF-NATIVE migration

Primary work is runtime adaptation from Python/Pydantic service execution to Workers-compatible boundaries and persistence adaptation to D1. Preserve the stable consumer contract and governed transaction semantics while replacing adapters beneath them.

Rollback: remove hosted TEST bindings, return consumers to no-effect repository-local adapters, and reconstruct the last TEST state from governed exports. No canonical production history exists to rewrite.

## CF-NEON-R2 migration

Adapt the runtime to Workers while preserving relational canonical storage in Neon. Introduce scoped database and R2 credentials and explicit cross-provider failure handling.

Rollback: disable Workers TEST ingress, revoke provider credentials, export/reconstruct canonical TEST fixtures, and return to local Postgres-shaped or repository-local adapters.

## GCP-NEON-R2 migration

Containerize the current Python service for Cloud Run, bind it to TEST-only Neon credentials and R2 evidence credentials, then execute the existing consumer, transaction, recovery, and portability suites against hosted adapters.

Rollback: route no consumers to the hosted TEST service, revoke Cloud Run/Neon/R2 credentials, preserve evidence exports, destroy hosted TEST resources, and return to repository-local execution.

## Rollback invariants

- Historical evidence is preserved rather than rewritten.
- No TEST approval or hosted TEST credential becomes production authority.
- Provider teardown cannot silently erase the evidence required to reconstruct the test campaign.
- Canonical and evidence planes remain distinguishable.
- A failed hosted experiment returns to the prior known repository-local TEST state without manufacturing a successful deployment claim.
