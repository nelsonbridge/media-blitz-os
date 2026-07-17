# Operating Runbook

## Current operating mode

RC2 operates in repository-local and CI `TEST` context only. No production effect is authorized.

## Validation sequence

1. Verify the two corrected architecture documents are present and unchanged relative to the candidate manifest.
2. Verify canonical sprint/work-control projections and repository audit.
3. Run CI, Runtime Coverage, Work Control Authority, State Authority, Canonicalization Security, and publication-regression gates.
4. Verify Sprint 31 temporal-authority paths.
5. Verify Sprint 32 governed retrieval/model gateway paths.
6. Verify Sprint 33 downstream consumer boundaries.
7. Verify Sprint 34 concurrent multi-consumer isolation, retry, rollback, telemetry, and portability.
8. Verify Sprint 35 production-control readiness contracts remain distinct from production validation.
9. Rebuild RC2 manifests deterministically and compare hashes.
10. Confirm deployment decision state remains `PENDING_HUMAN_DECISION` unless an explicit human decision record exists.

## Hosted validation stop conditions

Stop before hosted execution when provider TEST identity, scoped TEST credentials, teardown authority, or the `$0` boundary cannot be guaranteed.

Stop before production when any of the seven production controls lacks qualifying production evidence, when no hosting architecture is explicitly selected, or when rollback cannot restore the last validated state.

## Incident handling

Preserve immutable receipts, hashes, correlation identifiers, and incident lineage. Do not include canonical protected content or credentials in telemetry. Failed or incomplete evidence remains failed or incomplete in the release manifest.
