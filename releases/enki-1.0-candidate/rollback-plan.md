# Enki 1.0-rc1 Rollback Plan

## Scope

This plan governs rollback of the `1.0-rc1` candidate and its TEST evidence package. There is no approved production deployment to roll back.

## Candidate rollback triggers

- Readiness-manifest hash mismatch or evidence-pointer drift.
- Canonical work-control or repository-audit projection drift.
- Regression in authority, privacy, isolation, recovery, compatibility, or supply-chain checks.
- Discovery that a TEST result has been represented as production certification or approval.
- Discovery of an unresolved evidence conflict that materially changes a prior completion claim.

## Rollback actions

1. Mark the candidate decision state as deferred; do not alter historical sprint evidence.
2. Revert the candidate release branch or tag to the last verified commit while preserving the failed candidate evidence for audit.
3. Re-run forensic reconstruction on affected governed operations.
4. Regenerate authority projections and repository audit from canonical state.
5. Re-run CI, runtime coverage, work-control authority, state authority, canonicalization security, and applicable publication regressions.
6. Issue a new candidate version rather than rewriting the meaning of the prior candidate.

## Production boundary

Because `1.0-rc1` has no production approval, rollback must not be interpreted as a production incident response plan. A production rollback plan must be validated against the actual production identity, database, network, key, secret, deployment, and provider architecture before go-live.
