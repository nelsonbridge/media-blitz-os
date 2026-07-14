# Enki Deliverable, Internal POC Validation, and Production Deferral Decision

> **Authority class: Class 3 — governing roadmap decision for proposed promotion.**
> This decision revises the proposed roadmap. It does not alter canonical status until promoted through governed work control.

- Decision date: 2026-07-13
- Applies to: the Enki roadmap, Publication 000001, Sprint 3, Sprints 5–13, and downstream product-line validation

## Governing decision

Enki is the deliverable.

The repository began with a first-live-publication proof of concept, but Enki is not a publication engine. Media Blitz is a downstream product line that consumes Enki through governed boundaries.

That distinction does **not** remove the publication proof of concept from testing.

The publication-shaped lane remains a required internal end-to-end validation scenario before Enki release. What is deferred is the actual external production effect, not the test.

All Enki and downstream-consumer testing remains internal until every governed capability lane has passed rigorous automated path-complete TEST proof and Enki has received an explicit release decision.

## Corrected Sprint 3 treatment

Sprint 3 is decomposed into two separately governed parts.

### Part A — Mandatory internal publication POC validation

The complete publication-shaped path must be executed internally as part of integrated Enki validation. It must exercise:

- exact content-body and visual-manifest objects;
- configuration, identity, byline, brand, and channel-shaped fixtures;
- exact-hash review and TEST approval;
- publication-package construction;
- no-effect publication and distribution adapters;
- publication and distribution TEST receipts;
- simulated observation windows;
- `SYNTHETIC/TEST`, `REPLAY/TEST`, and controlled `REAL/TEST` feedback;
- feedback lineage, classification, routing, deduplication, disposition, and calibration;
- denial, mismatch, expiry, revocation, duplicate, interruption, retry, rollback, recovery, tamper, and privilege-escalation paths;
- deterministic reconstruction of the entire lane.

This is mandatory internal evidence that Enki can safely serve a downstream consumer. It is not evidence that Enki is itself a publication engine.

### Part B — Deferred external Media Blitz production validation

The following remain deferred until Enki is released and Media Blitz receives its own product-level production authority:

- live publication or distribution;
- real production accounts, credentials, endpoints, callbacks, and transports;
- actual audience observation;
- `REAL/PRODUCTION` publication feedback or production zero-feedback receipts;
- post-publication production calibration.

The external event validates Media Blitz in production. It does not define Enki correctness.

## Internal production prohibition

Before Enki release:

- all execution contexts are TEST;
- production transports, credentials, endpoints, callbacks, and side-effect adapters are unreachable;
- publication and distribution execute only through no-effect adapters, simulators, or disposable isolated environments;
- audience behavior is represented through `SYNTHETIC/TEST`, `REPLAY/TEST`, and controlled `REAL/TEST` evidence;
- TEST evidence cannot satisfy a production gate;
- rollback, compensation, discard, or exact recovery is proven for every state-changing path;
- every publication-shaped terminal state is journaled, receipted, and reconstructable.

## Enki release gate

Enki may be considered ready for a production release decision only after:

1. Sprints 5–12 have completed their governed capabilities and path-complete TEST evidence;
2. Sprint 13 has executed the integrated cross-operation TEST matrix;
3. the internal publication POC lane has passed end to end through no-effect adapters;
4. at least one additional downstream-consumer or nonpublication adaptive lane has passed end to end;
5. all success, denial, invalid-input, stale-input, duplicate, conflict, interruption, retry, rollback, recovery, replay, tamper, and privilege-escalation paths are covered;
6. all TEST execution is proven incapable of causing an unapproved production effect;
7. clean-room reconstruction and rollback are proven;
8. the release candidate, threat model, runbooks, limitations, rollback package, and evidence manifests are bound to an exact commit; and
9. governing authority explicitly approves or rejects Enki release.

## Artifact treatment

Publication 000001 artifacts remain active internal test assets:

- article body and visual work;
- review and approval models;
- configuration worksheets;
- publication package and receipt designs;
- observation-window and feedback scenarios;
- downstream Media Blitz interface contracts.

They must not be discarded, merely archived, or treated as optional historical decoration. They are production-shaped fixtures used to prove one complete downstream-consumer lane internally.

## Dependency effect

This decision removes external dependencies from the Enki completion path:

- live publishing accounts and credentials;
- reachable production transports;
- actual external publication and distribution;
- real audience availability or response;
- production observation-window passage;
- production feedback and production calibration.

It retains the corresponding internal TEST obligations:

- exact content, visual, configuration, approval, package, receipt, observation, feedback, calibration, rollback, and reconstruction behavior;
- every successful and unsuccessful path;
- complete no-effect execution through the downstream publication POC lane.

## Remaining Enki dependencies

The remaining dependencies are internal and executable:

- shared transaction and path engine;
- Enki core contracts and architecture acceptance;
- governed generic state write;
- governed human migration and protections;
- reconciliation and disclosure governance;
- transition and conflict engine;
- privacy-governed model use;
- forensic reconstruction, portability, and governed completion;
- integrated path-complete TEST proof across the publication POC and at least one other adaptive lane;
- versioned Enki release candidate and explicit release decision.

## Final distinction

```text
NOT REQUIRED BEFORE ENKI RELEASE
actual live publication and production audience evidence

REQUIRED BEFORE ENKI RELEASE
complete internal publication-shaped execution and proof of every path
```
