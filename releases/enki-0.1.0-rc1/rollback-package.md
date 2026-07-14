# Enki 0.1.0-rc1 Rollback Package

## Rollback target

The Sprint 13 implementation can be removed by reverting merge commit:

`cb84fbc8eef6096e8a707e1b922dfa2eddb23e51`

The preceding governed baseline is the Sprint 12-complete `sandbox` state.

## Data handling

Sprint 13 implementation tests create only ephemeral TEST data. No external publication, provider effect, audience exposure, or production mutation is expected.

For persisted internal TEST evidence:

- preserve immutable transaction events and receipts;
- preserve approval consumption and recovery lineage;
- mark the candidate superseded or rejected rather than deleting history;
- revoke any candidate-scoped TEST approvals that remain available;
- do not relabel TEST records as PRODUCTION or REAL production evidence.

## Rollback verification

After rollback:

1. run CI and Runtime Coverage;
2. run Work Control Authority, State Authority, and Canonicalization Security;
3. regenerate authoritative projections and repository audit;
4. confirm zero unexpected external-effect records;
5. confirm Sprint 13 completion or release claims are removed or superseded through governed work control.

## Recovery preference

Use exact retry for interrupted transactions after approval consumption. Use rollback only for pre-consumption failures or an explicit governing decision to remove the implementation.

Rollback does not erase historical evidence.
