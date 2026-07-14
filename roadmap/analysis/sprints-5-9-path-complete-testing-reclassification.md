# Sprints 5–9 — Path-Complete Testing Reclassification

> **Authority class: Class 3 — implementation assessment.**
> This analysis applies `automated-path-complete-testing-policy.md` to Sprints 5–9. It does not change canonical sprint status.

## Governing correction

Sprints 5–9 are not waiting for permission to exercise TEST paths individually.

TEST execution is approved when every path is:

- TEST-scoped;
- isolated from production effects;
- machine-declared with an expected result;
- automated;
- auditable;
- idempotent; and
- protected by rollback, compensation, isolated discard, or exact recovery.

The remaining gap is therefore not **approval to test**. It is **implementation and automated proof of every path**.

## Revised status summary

| Sprint | Revised testing status | What remains |
|---|---|---|
| 5 | TEST execution approved by policy | Build reusable transaction path graph and automate every authority, interruption, rollback, retry, conflict, and escalation path |
| 6 | TEST execution approved; implementation ready for review | Complete path coverage for constitutional boundaries, schema evolution, and confidence-contract behavior; record architecture acceptance and evidence mapping |
| 7 | TEST execution approved by policy | Build governed state-write plan and executor, then automate every partial-write, conflict, tamper, rollback, retry, and reconstruction path |
| 8 | TEST execution approved by policy | Build governed migration and human-protection workflows, then automate every semantic, privacy, consent, revocation, interruption, rollback, and recovery path |
| 9 | TEST execution approved by policy | Add temporal/privacy governance and transactional disclosure, then automate every eligibility, uncertainty, authority, redaction, revocation, rollback, and receipt path |

## Sprint 5

### Missing

- reusable transaction state machine shared across governed operation families;
- machine-readable path catalog;
- common journal and receipt contract;
- automated failure injection at every transaction boundary;
- deterministic rollback or recovery assertion for every state-changing path;
- coverage enforcement that fails when a declared path is untested;
- cross-context escalation and replay matrix.

### Why partial

Approval primitives exist, but the automated path-complete transaction system does not. The sprint closes when the transaction graph is executable and every terminal path is tested, not when a reviewer manually approves each test.

## Sprint 6

### Missing

- automated schema and contract-version compatibility paths;
- explicit tests for forward, backward, unsupported, and ambiguous contract evolution;
- final decision on the confidence assertion contract and tests for every resulting path;
- evidence manifest and architecture acceptance.

### Why not technically partial

The core boundary and principal implementation exist. Sprint 6 remains ready for completion review. The new policy removes any implication that individual TEST cases require separate human authority. Human acceptance is needed for the constitutional architecture, not for each automated path.

## Sprint 7

### Missing

- content-addressed state-write plan;
- approval-bound executor;
- journal and immutable receipt;
- automated paths for valid write, invalid reference, duplicate, conflict, stale preflight, interruption at each write stage, receipt loss, tampering, rollback, exact retry, and reconstruction;
- automated subject-class matrix for PERSON, ORGANIZATION, and PROJECT.

### Why partial

The repository proves storage behavior. It does not yet prove the governed operation or every path through it. Rollback or exact recovery must be designed alongside the write path and tested automatically.

## Sprint 8

### Missing

- content-addressed migration plan and executor;
- migration journal and receipt;
- human protection policy layer;
- automated paths for every expression-origin choice, privacy classification, consent state, purpose restriction, correction, retraction, expiry, revocation, interruption, duplicate migration, semantic mismatch, rollback, and exact recovery;
- semantic-parity assertions across all temporal states.

### Why partial

Projection is implemented, but migration is not yet an automated, rollback-capable governed operation. Testing permission is not the blocker.

## Sprint 9

### Missing

- temporal and context eligibility resolver;
- sensitivity, privacy, consent, purpose, and redaction contracts;
- transactional reconciliation and disclosure execution;
- approval consumption, rollback, retry, and receipts;
- automated paths for applicable, inapplicable, uncertain, conflicting, private, redacted, subject-requested, externally authorized, unauthorized, revoked, duplicate, interrupted, and receipt-conflict outcomes.

### Why partial

The conceptual boundary is implemented. The complete governed path graph and its automated rollback/recovery proof are not.

## Revised completion principle

For Sprints 5–9, the testing portion of completion is satisfied when:

1. the full operation path graph is machine-readable;
2. every declared path has an automated test;
3. every state-changing test proves rollback, compensation, discard, or exact recovery;
4. no TEST path can reach a production effect;
5. duplicate and cross-context escalation tests fail closed;
6. coverage fails when any path is undeclared or untested;
7. immutable test evidence is bound to the implementation commit.

No additional human approval is required merely to run those tests. Human authority remains required for architecture decisions, accepted limitations, canonical completion, and actual production effects.
