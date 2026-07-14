# Automated Path-Complete Testing and Rollback Policy

> **Authority class: Class 3 — governing roadmap decision for proposed promotion.**
> This policy authorizes TEST execution under the conditions below. It does not authorize PRODUCTION effects or alter canonical sprint status until promoted through governed work control.

- Decision date: 2026-07-13
- Applies to: Sprints 5–13 and every governed operation family

## Governing decision

Testing is approved as an automated engineering activity when the operation:

1. executes under TEST-scoped authority;
2. is technically incapable of causing an unapproved PRODUCTION effect;
3. has a deterministic rollback, compensating action, isolated discard path, or exact recovery route;
4. preserves immutable evidence of the attempted path and resulting disposition; and
5. can be rerun without creating duplicate authority, state, receipts, or external effects.

A separate human approval is not required for each automated TEST case once its path definition, isolation boundary, expected result, and rollback or recovery contract are declared.

This approval applies to **executing tests**. It does not pre-approve:

- the implementation as correct;
- a sprint as complete;
- migration of TEST evidence into PRODUCTION evidence;
- an external publication, disclosure, model transmission, or other production effect;
- destructive rewriting of canonical history.

## Path-complete design rule

Every governed operation must be designed as an explicit path graph before completion is claimed.

At minimum, the graph must include:

- valid success;
- invalid input;
- missing authority;
- denied authority;
- wrong action;
- wrong subject;
- wrong content hash;
- wrong execution context;
- insufficient authority class;
- expired authority;
- revoked authority;
- stale input;
- duplicate request;
- exact retry;
- competing transaction;
- conflict after preflight;
- interruption before reservation;
- interruption after reservation;
- interruption after authority consumption;
- interruption during persistence;
- interruption after persistence but before receipt;
- receipt conflict;
- rollback or compensation;
- recovery to a single documented terminal state;
- cross-context replay or privilege-escalation attempt.

Operation-specific paths must be added where relevant, including privacy denial, redaction, supersession, branch, merge, split, zero-feedback, provider failure, and malformed external evidence.

## Automation standard

Each declared path must have an automated test or generated test case that records:

- operation and path identifier;
- fixture and input hashes;
- approval or denial fixture;
- execution context;
- expected terminal state;
- expected records and receipts;
- prohibited records and effects;
- rollback, compensation, discard, or recovery action;
- observed terminal state;
- pass, fail, or unresolved result;
- immutable test evidence reference.

The test suite must fail when a declared path has no executable coverage.

## Rollback definition

Rollback does not mean erasing history.

An acceptable rollback mechanism may be:

- release of an unconsumed approval reservation;
- atomic discard of an uncommitted temporary write set;
- compensating append-only record;
- restoration from a pre-operation snapshot in an isolated TEST repository;
- deterministic replay that completes the original transaction exactly once;
- a documented rollback receipt proving no authoritative effect remains;
- destruction and recreation of an isolated TEST environment from immutable fixtures.

A rollback mechanism is unacceptable when it:

- rewrites or deletes canonical historical evidence without a governed record;
- converts TEST authority into PRODUCTION authority;
- hides a partial external effect;
- permits duplicate receipts or ambiguous terminal state;
- relies on an unrecorded manual correction.

## Test approval threshold

A TEST path is considered authorized for execution when all of the following are true:

- its path definition and expected result are machine-readable;
- TEST authority is exact and context-bound;
- no production adapter, credential, endpoint, or side-effect capability is reachable;
- rollback, compensation, discard, or recovery has been declared;
- the path generates auditable evidence;
- exact retry and duplicate prevention are defined;
- failure cannot silently promote state or authority.

The path is considered **validated** only after the automated test passes and its rollback or recovery assertion passes.

## Completion standard

A sprint may treat testing as complete when:

1. every declared path has executable coverage;
2. all required paths pass;
3. rollback or recovery is proven for every state-changing path;
4. coverage reports show no undeclared or untested terminal path;
5. TEST evidence cannot satisfy PRODUCTION gates;
6. the resulting evidence manifest is bound to the exact implementation commit; and
7. any unresolved path is explicitly accepted as a limitation by governing authority.

## Sprint application

### Sprint 5

Automate every approval and transaction path, including reservation, consumption, release, rollback, exact retry, interruption, conflict, and cross-context escalation.

### Sprint 6

Automate every constitutional and contract boundary, including objective substitution, product leakage, unknown references, schema incompatibility, and interpretation-version behavior.

### Sprint 7

Automate every generic state-write path, including preflight, known-reference validation, partial multi-record writes, duplicate writes, receipt loss, tampering, rollback, and reconstruction across all reference subject classes.

### Sprint 8

Automate every migration and human-protection path, including expression-origin choices, privacy and consent denial, correction, retraction, expiry, revocation, interruption, duplicate migration, semantic mismatch, and rollback or recovery.

### Sprint 9

Automate every reconciliation and disclosure path, including temporal exclusion, context mismatch, uncertainty, competing interpretations, subject request, privacy denial, redaction, external authority, revocation, receipt conflict, and recovery.

### Sprint 10

Automate every transition, conflict, branch, merge, split, cycle, stale-input, authority-conflict, rollback, and exact-retry path.

### Sprint 11

Automate every interpretation, privacy filtering, package construction, approval, TEST dispatch, production-gate rejection, provider failure simulation, revocation, and recovery path.

### Sprint 12

Automate reconstruction, clean-room recovery, import, export, migration, replay, rollback, adapter parity, work-control amendment, and privilege-escalation paths.

### Sprint 13

Execute the complete cross-operation path matrix through synthetic, replay, and controlled human TEST evidence, including chaos injection and release rollback.

## Production boundary

Rollback-capable TEST execution is approved. Production remains separately governed.

An operation with an irreversible or externally visible effect must be tested through a no-effect adapter, simulator, disposable isolated environment, or governed rehearsal. The actual external effect still requires explicit PRODUCTION authority bound to the final exact objects.
