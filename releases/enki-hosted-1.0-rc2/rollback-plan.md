# Rollback Plan

## Repository and software rollback

- Revert to the last merged, fully green canonical baseline.
- Preserve failed-candidate evidence and do not rewrite historical sprint records.
- Regenerate work-control projections, authority manifest, and repository audit from canonical state.
- Re-run the complete gate matrix before declaring the rollback baseline restored.

## Hosted TEST rollback

For any future finalist campaign:

1. Stop new TEST ingress.
2. Revoke temporary TEST authority and credentials.
3. Preserve hash-bound logs, receipts, exports, and failure evidence.
4. Destroy the scoped TEST environment using the authorized teardown path.
5. Reconstruct governed TEST state from the portable export package.
6. Compare canonical fingerprints and evidence manifests.

## Production rollback obligation

Production deployment is currently unauthorized. A later production validation must define and prove provider-specific rollback for IAM, identity federation, database isolation, network segmentation, tenant keys, secrets, and any selected runtime/data providers before approval can be considered.
