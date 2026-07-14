# Enki Deliverable and Production Deferral Decision

> **Authority class: Class 3 — governing roadmap decision for proposed promotion.**
> This decision revises the proposed roadmap. It does not alter canonical status until promoted through governed work control.

- Decision date: 2026-07-13
- Applies to: the Enki core roadmap, Publication 000001, Sprint 3, Sprints 5–13, and downstream product-line testing

## Governing decision

Enki is the deliverable.

The repository began with a first-live-publication proof of concept, but Enki is not a publication engine. Publication and media distribution belong to the downstream Media Blitz product line. They may consume Enki after Enki is internally complete and separately authorized for production, but they do not define Enki completion.

All Enki testing remains internal until every governed capability lane has passed rigorous automated path-complete TEST proof and Enki has received an explicit release decision.

No publication, disclosure, model transmission, external distribution, audience observation, or other production effect is required to complete the Enki internal roadmap.

## Sprint 3 treatment

Sprint 3 is reclassified from an active Enki production lane to a preserved historical proof-of-concept and deferred downstream product validation workstream.

Its artifacts remain valuable as:

- historical evidence of the original proof-of-concept;
- a production-shaped internal fixture;
- a downstream consumer contract for Media Blitz;
- a no-effect publication rehearsal and feedback-pipeline scenario;
- future post-Enki-launch product validation.

Sprint 3 does not block, gate, or close Enki Sprints 5–13.

The canonical promotion should preserve its history and move its unfinished production work out of the Enki core critical path. Appropriate canonical treatment may be `deferred`, `not_planned` within the Enki roadmap, or transfer to a downstream Media Blitz backlog, provided the historical record is not erased.

## Internal production prohibition

Before Enki release:

- all execution contexts are TEST;
- production transports, credentials, endpoints, callbacks, and side-effect adapters are unreachable;
- publication is simulated, rehearsed through a no-effect adapter, or executed only in a disposable isolated environment;
- audience behavior is represented through `SYNTHETIC/TEST`, `REPLAY/TEST`, and controlled `REAL/TEST` evidence;
- TEST evidence cannot satisfy a production gate;
- rollback, compensation, discard, or exact recovery is proven for every state-changing path.

## Enki release gate

Enki may be considered ready for a production release decision only after:

1. Sprints 5–12 have completed their governed capabilities and path-complete TEST evidence;
2. Sprint 13 has executed the integrated cross-operation TEST matrix;
3. all success, denial, invalid-input, stale-input, duplicate, conflict, interruption, retry, rollback, recovery, replay, and privilege-escalation paths are covered;
4. all TEST execution is proven incapable of causing an unapproved production effect;
5. clean-room reconstruction and rollback are proven;
6. the release candidate, threat model, runbooks, limitations, rollback package, and evidence manifests are bound to an exact commit;
7. governing authority explicitly approves or rejects Enki release.

## Downstream product treatment

Media Blitz, Career Intelligence and Placement, Personal Cognitive Continuity, research, executive support, and future products consume Enki through explicit governed boundaries.

Media Blitz production publication occurs only after Enki is live and only under its own product release, content, identity, channel, legal, publication, observation, and calibration authority.

A successful Media Blitz publication may validate that downstream product. It does not retroactively establish or define Enki correctness.

## Dependency effect

This decision removes the following from the Enki completion path:

- visual approval for Publication 000001;
- final article-body publication approval;
- channel, account, identity, byline, and brand production configuration;
- production publication credentials and transport;
- external publication and distribution receipts;
- production observation windows;
- audience response or zero-feedback production receipts;
- post-publication calibration.

These remain valid downstream work, but they no longer gate Enki.

The remaining Enki dependencies are internal and executable:

- shared transaction and path engine;
- Enki core contracts and architecture acceptance;
- governed generic state write;
- governed human migration and protections;
- reconciliation and disclosure governance;
- transition and conflict engine;
- privacy-governed model use;
- forensic reconstruction, portability, and governed completion;
- integrated path-complete TEST proof and Enki release candidate.
