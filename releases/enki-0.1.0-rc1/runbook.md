# Enki 0.1.0-rc1 Internal TEST Runbook

## Preconditions

- Repository state matches source commit `cb84fbc8eef6096e8a707e1b922dfa2eddb23e51`.
- Execution context is `TEST`.
- Approval grants are exact, current, unrevoked, and TEST-scoped.
- No production transport, credential, endpoint, callback, or external publication adapter is configured.

## Validation sequence

1. Run the full test suite and coverage gate.
2. Run Work Control Authority.
3. Run State Authority.
4. Run Canonicalization Security.
5. Run Publication 000001 asset regression.
6. Verify generated backlog, roadmap, authority, and audit projections have no drift.
7. Verify repository audit reports zero findings.
8. Recompute release artifact and candidate hashes.
9. Confirm the decision request contains no decision.

## Integrated proof sequence

1. Construct the publication-shaped proof lane.
2. Validate all required content, visual, configuration, identity, byline, brand, channel, and review hashes.
3. Consume an exact TEST approval through the governed transaction executor.
4. Execute through the no-effect adapter.
5. Record the no-effect receipt.
6. Process attributed feedback or a zero-response window.
7. Produce calibration and forensic reconstruction.
8. Repeat through the nonpublication lane.
9. Build the candidate manifest from both loop receipts and release artifacts.

## Failure response

- **Before approval consumption:** release the reservation and retain the rollback receipt.
- **After approval consumption:** preserve evidence and perform an exact retry using the same transaction.
- **Hash, context, authority, or subject mismatch:** fail closed; do not compensate by widening scope.
- **Conflicting immutable record:** quarantine for governing review.
- **Any observed external effect:** stop immediately; treat the candidate as invalid and investigate the capability boundary.

## Release gate

Present the human decision package with these options:

- `APPROVE`
- `APPROVE_WITH_CONDITIONS`
- `DEFER`
- `REJECT`

The system must not populate the decision or deciding identity.

## Prohibited operations

This runbook does not permit production mutation, public publication, audience exposure, external model dispatch, production feedback ingestion, or release self-approval.
