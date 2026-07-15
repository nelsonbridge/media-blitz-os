# Enki 1.0-rc1 Operating Runbook

## Current authorized operating context

The evidence-bearing candidate is authorized for governed repository-local TEST execution only. Supported operations include canonical governance, state writes, reconciliation, disclosure, transitions, model-use packaging without production dispatch, forensic reconstruction, portability, policy simulation, observability, retention lifecycle, concurrency recovery, stable consumer contract execution, and downstream no-effect product proofs.

## Standard TEST operation

1. Resolve the exact namespace, tenant, subject, domain, audience, and TEST execution boundary.
2. Resolve the exact versioned contract and required authorization.
3. Validate provenance, hashes, privacy/purpose restrictions, and lifecycle state.
4. Execute only through the declared governed application service.
5. Persist or reconstruct immutable journal and receipt evidence where the operation is state-changing.
6. Run deterministic generated-view and repository-audit checks after structural or canonical work-control changes.
7. Fail closed on stale, ambiguous, mismatched, unsupported, cross-context, cross-product, or privilege-escalating inputs.
8. Preserve TEST qualification on every TEST receipt and campaign result.

## Incident handling

- Stop the affected operation when authority, boundary, hash, receipt, or reconstruction integrity is uncertain.
- Use forensic reconstruction to classify the operation before retrying.
- Resume only through exact retry or the declared recovery strategy.
- Do not repair canonical state by direct repository mutation.
- Record unresolved ambiguity as a finding rather than manufacturing a successful state.

## Entry conditions for production-control validation

Before any production deployment decision, separately provision and validate cloud IAM, production identity federation, managed database row-level isolation, network segmentation, per-tenant production key management, production secrets management, and independent penetration testing.

The presence of this runbook does not satisfy those controls and does not authorize production deployment.
