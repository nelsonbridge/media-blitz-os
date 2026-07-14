# Enki 0.1.0-rc1 Calibration Report

> Execution context: **TEST**  
> Candidate source commit: `cb84fbc8eef6096e8a707e1b922dfa2eddb23e51`  
> External effects authorized: **No**

## Proof lanes

The Sprint 13 implementation executes two required adaptive loops:

1. **Publication-shaped lane** using a `PUBLICATION` subject and production-shaped content, visual, identity, byline, brand, channel, review, approval, packaging, feedback, calibration, recovery, and reconstruction inputs.
2. **Nonpublication lane** using an `ORGANIZATION` subject and the same governed approval, transaction, feedback, calibration, recovery, and reconstruction machinery.

Both lanes use capability-isolated no-effect adapters. They have no transport, credential, endpoint, callback, audience, or production-mutation capability.

## Feedback calibration

The proof preserves these provenance classes without collapsing them:

- `SYNTHETIC/TEST`
- `REPLAY/TEST`
- `CONTROLLED_REAL/TEST`

The classification layer distinguishes accepted, duplicate, irrelevant, malformed, contradictory, adversarial, unauthorized, mismatched, conflicting, and zero-response inputs. Exact feedback identifiers and content hashes are retained for attribution and replay analysis.

## Failure and recovery

Automated tests exercise:

- rollback before approval consumption;
- exact retry after an interrupted no-effect operation;
- duplicate-effect prevention;
- cross-plan replay rejection;
- content and context tamper rejection;
- TEST-to-PRODUCTION authority mismatch;
- deterministic forensic reconstruction.

## Calibration conclusion

The implementation demonstrates that Enki can execute repeatable, reconstructable adaptive loops and production-shaped downstream rehearsals without creating external effects or allowing TEST evidence to satisfy a PRODUCTION gate.

This report does not authorize Enki release or production operation.
