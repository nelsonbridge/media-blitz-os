# ADR-0001: Context-Bound Approvals and Execution Isolation

- Status: Accepted for implementation in Sprint 5
- Date: 2026-07-12
- Governing scope: Sprints 5–11 and every runtime operation that can satisfy a gate or cause an external or behavioral effect

## Context

The runtime must exercise approval-dependent workflows in automated tests without allowing test fixtures to impersonate real authority. A Boolean approval field is insufficient because it does not identify the execution lane, authorized action, subject, exact content, authority level, validity period, or consumption state.

The system therefore needs approvals that can legitimately evaluate as approved during testing while remaining structurally incapable of authorizing production effects.

## Decision

The runtime will support two execution contexts:

```text
TEST
PRODUCTION
```

`REAL`, `SYNTHETIC`, and `REPLAY` remain provenance classifications. They are not approval or execution contexts.

Every approval-dependent operation must evaluate a governed `ApprovalGrant` containing at least:

```text
approval_id
decision
execution_context
permitted_actions
subject_id
content_sha256
authorized_by
authority_class
issued_at
expires_at
revoked_at
consumption_status
consumed_by_transaction_id
```

A gate is satisfied only when all applicable dimensions match:

```text
decision == APPROVED
and grant.execution_context == runtime.execution_context
and requested_action in grant.permitted_actions
and grant.subject_id == requested_subject
and grant.content_sha256 == current_content_sha256
and grant.authority_class is sufficient
and grant is not expired or revoked
and grant consumption is compatible with the current transaction
```

## Mandatory Invariants

1. A TEST approval is rejected by a PRODUCTION runtime.
2. A PRODUCTION approval is never synthesized by a test fixture.
3. TEST approvals cannot authorize external publication, production model ingestion, REAL feedback creation, production receipts, or production release decisions.
4. TEST execution uses adapters that are technically incapable of external side effects.
5. Every transaction, event, receipt, rollback, recovery action, export, import, and migration preserves execution context.
6. Import, replay, migration, rollback, recovery, and adapter substitution cannot promote TEST authority or evidence into PRODUCTION.
7. An exact retry may resolve to the same transaction and receipt; it may not consume the approval a second time or create duplicate authority.
8. TEST receipts remain permanently marked TEST and cannot satisfy production evidence gates.
9. Approval context participates in deterministic hashes and forensic reconstruction.
10. Ambiguous context or authority fails closed and is quarantined for review.

## Adapter Isolation

Policy checks are necessary but not sufficient. TEST execution must use adapters with no credential or capability path to external publication, production model dispatch, production notification, or production record mutation.

The runtime therefore requires both:

```text
Policy isolation
TEST approval cannot authorize a production effect

Capability isolation
TEST adapter cannot perform a production effect
```

## Sprint Ownership

- Sprint 5 owns `ExecutionContext`, `ApprovalGrant`, approval evaluation, reservation and consumption, context-bound journals and receipts, TEST adapters, and escalation tests.
- Sprint 6 applies test-scoped consent, privacy, correction, transition, revocation, and model-use approvals to the human-state reference implementation.
- Sprint 7 generalizes approval applicability across governed subject classes while preserving stricter human rights and authority overlays.
- Sprint 8 binds every transition approval and receipt to execution context and exact before-and-after state hashes.
- Sprint 9 separates TEST package generation from PRODUCTION model dispatch and external effects.
- Sprint 10 proves that import, migration, recovery, clean-room operation, and adapter substitution preserve context without escalation.
- Sprint 11 runs fully automated TEST loops and a separately authorized PRODUCTION loop. TEST evidence cannot satisfy production gates.

## Consequences

### Positive

- Approval-dependent workflows become fully testable.
- Test success cannot be mistaken for real authority.
- External side effects are blocked both by policy and by adapter capability.
- Approval use, retries, recovery, and migration become auditable.
- The release process can distinguish machinery proof from production proof.

### Cost

- Approval context must be propagated through domain models, services, adapters, events, receipts, migrations, generated views, audits, and tests.
- Existing naked Boolean approval fields must be treated as compatibility inputs only until migrated into governed grants.
- Cross-context test coverage becomes a permanent security requirement.

## Rejected Alternatives

### Temporarily setting production approval fields to true

Rejected because it makes test evidence indistinguishable from real authorization and permits accidental external effects.

### Separate test and production domain models

Rejected because duplicated models would drift. The system uses shared contracts with distinct governed contexts and adapters.

### A separate simulation runtime as the immediate solution

Deferred. Strong adapter isolation is required now; a fully separate runtime may be added later if operational risk justifies the duplication.
