# Feedback Validation Amendment

> **Authority class: Class 3 — proposed roadmap amendment.**
> This amendment supersedes conflicting feedback language in `revised-thirteen-sprint-plan.md`. It does not alter canonical sprint state until accepted and promoted through governed work control.

- Proposed date: 2026-07-13
- Applies to: Sprint 3, Sprint 13, feedback provenance, release evidence, and production approval

## Problem

The thirteen-sprint draft requires attributable REAL feedback in Sprint 3 but does not explain how feedback behavior is validated before production. Read literally, it makes production exposure the first complete test of the feedback loop.

That is not acceptable.

The feedback subsystem must be proven before production. Actual public response remains useful operational evidence, but it cannot be the first evidence that ingestion, provenance, classification, routing, deduplication, disposition, promotion controls, and reporting work correctly.

A second defect is that audience response cannot be guaranteed. A publication may receive no observable feedback. Therefore, Sprint 3 cannot require that a third party chooses to respond. It may require a functioning collection mechanism, a defined observation window, and an explicit receipt for either observed feedback or a zero-feedback outcome.

## Governing distinction

Feedback provenance and execution context are separate dimensions.

### Provenance classes

- `REAL` — originated from an actual human action or an actually observed external event.
- `SYNTHETIC` — intentionally manufactured test input.
- `REPLAY` — immutable previously captured input replayed through the current system for regression or calibration.

### Execution contexts

- `TEST` — incapable of causing production effects or satisfying production evidence gates.
- `PRODUCTION` — authorized operational execution.

### Valid combinations

| Provenance | TEST | PRODUCTION | Meaning |
|---|---:|---:|---|
| REAL | allowed | allowed | Controlled human evaluation in TEST; actual audience or operational response in PRODUCTION |
| SYNTHETIC | allowed | prohibited as production evidence | Manufactured scenarios for coverage, failure, and adversarial testing |
| REPLAY | allowed | prohibited as production evidence | Historical or captured cases rerun through current logic |

`REAL` does not imply `PRODUCTION`. A real human evaluator may produce REAL feedback in a TEST environment. That evidence proves human interaction behavior while remaining structurally incapable of authorizing or causing production effects.

## Pre-production feedback validation gate

Before production approval, the release candidate must pass all of the following.

### 1. Synthetic scenario suite

Manufacture explicit `SYNTHETIC/TEST` feedback covering at least:

- supportive, critical, corrective, ambiguous, irrelevant, duplicate, contradictory, adversarial, and malformed responses;
- wrong-publication, wrong-subject, wrong-context, stale, expired, revoked, and unauthorized inputs;
- high-volume repetition and deduplication;
- proposed corrections that should and should not become knowledge-state candidates;
- feedback that must remain observational rather than controlling;
- zero-response and no-action outcomes.

Every scenario requires an expected classification, route, disposition, and prohibited side effects.

### 2. Replay and regression suite

Where captured cases exist, run them as `REPLAY/TEST` with immutable source lineage. Replay must preserve original provenance while ensuring that the current execution event cannot be mistaken for new REAL feedback.

Absence of a historical replay corpus does not waive the synthetic suite. It is recorded as a release limitation until real cases are available.

### 3. Controlled human evaluation

Run at least one controlled evaluation with an identified human reviewer against the TEST release candidate.

The evaluator reviews or responds to production-shaped artifacts through a non-side-effecting test interface. Their response is classified as `REAL/TEST`, not SYNTHETIC and not production evidence.

An evaluator may:

- assess whether the artifact communicates what the system claims it communicates;
- provide supportive, critical, corrective, or ambiguous feedback;
- challenge provenance, interpretation, disclosure, or disposition decisions;
- verify that the system records the response without silently converting it into authority.

An independent evaluator is preferred for broader validity, but the Sprint 13 minimum is one identified human evaluator distinct from any automated feedback generator. Production authorization may impose a stronger evaluator requirement.

### 4. Feedback-pipeline proof

The system must prove, in TEST, that it can:

- ingest feedback with explicit provenance and execution context;
- bind feedback to the correct publication, artifact, subject, and transaction lineage;
- validate malformed or mismatched records fail closed;
- classify and route without erasing uncertainty;
- deduplicate while retaining source lineage;
- distinguish observation from proposed knowledge change;
- prevent unauthorized canonical promotion;
- produce immutable disposition and audit receipts;
- replay the complete process deterministically;
- record a valid zero-feedback outcome.

### 5. Pre-production calibration report

Produce a release-candidate report comparing:

- expected synthetic outcomes;
- observed synthetic outcomes;
- replay outcomes where available;
- controlled `REAL/TEST` human outcomes;
- unresolved mismatches and accepted limitations.

Production approval must bind this exact report hash and its unresolved limitations.

## Revised Sprint 13 requirements

Sprint 13 becomes the complete pre-production feedback-validation boundary.

Add to Sprint 13 scope:

- synthetic feedback scenario manufacture and execution;
- replay/regression execution where source cases exist;
- controlled human evaluation producing `REAL/TEST` feedback;
- provenance and context matrix enforcement;
- deterministic classification, routing, deduplication, disposition, promotion-denial, and audit proof;
- zero-feedback outcome proof;
- pre-production calibration report.

Add to Sprint 13 exit criteria:

- the feedback subsystem has been exercised end to end without production effects;
- `SYNTHETIC`, `REPLAY`, and controlled `REAL/TEST` evidence remain distinguishable and reconstructable;
- at least one identified human evaluator has produced feedback in TEST;
- production evidence gates reject all TEST feedback regardless of provenance;
- expected and observed outcomes are compared in a hash-bound calibration report;
- unresolved limitations are explicit in the production-readiness handoff.

Sprint 13 may therefore establish that the feedback system is ready for production. It still may not claim actual audience response, production validation, or successful external publication.

## Revised Sprint 3 requirements

Rename Sprint 3:

> **First controlled production publication and post-release calibration**

Revise its objective:

Complete Publication 000001 through independently reviewed content and visuals, production configuration, explicit production authorization, external publication, publication receipts, a defined observation window, capture of any attributable `REAL/PRODUCTION` feedback, and comparison against pre-production expectations.

Replace the mandatory REAL-feedback occurrence criterion with:

- feedback collection is enabled and bound to the publication lineage;
- an observation window is defined before publication;
- at the end of the window, either:
  - attributable `REAL/PRODUCTION` feedback records exist; or
  - an immutable zero-feedback receipt records that no qualifying response was observed;
- any observed production feedback is classified, routed, and dispositioned through the governed pipeline;
- a post-release calibration report compares production outcomes with `SYNTHETIC/TEST`, `REPLAY/TEST`, and `REAL/TEST` expectations;
- mismatches become governed improvement candidates rather than silent behavior changes.

Sprint 3 is not complete merely because something was published. It is complete when the authorized production cycle and its observation window are receipted, whether the audience responds or not.

## Production approval boundary

Production approval may be granted only after Sprint 13 feedback validation passes or the governing authority explicitly accepts a recorded limitation.

Production approval cannot be based on:

- unlabelled synthetic feedback;
- test receipts represented as operational evidence;
- replay events represented as new audience response;
- assumed or fabricated engagement;
- the expectation that production will reveal whether the feedback subsystem works.

## Cross-environment calibration

After production, compare the four evidence forms without collapsing them:

1. `SYNTHETIC/TEST` — coverage and expected behavior;
2. `REPLAY/TEST` — regression and historical compatibility;
3. `REAL/TEST` — controlled human interaction;
4. `REAL/PRODUCTION` — actual operational response, including the valid possibility of no response.

The purpose is not to make test evidence impersonate reality. It is to measure how well pre-production evidence predicted production behavior and improve the scenario corpus accordingly.

## Required promotion changes

When the roadmap is promoted:

1. revise Sprint 13 and its work item with the complete pre-production feedback-validation gate;
2. rename and revise Sprint 3 as the controlled production and post-release calibration lane;
3. remove any exit criterion that requires an audience member to respond;
4. add a zero-feedback receipt and observation-window contract;
5. preserve `REAL | SYNTHETIC | REPLAY` as provenance and `TEST | PRODUCTION` as execution context;
6. prohibit TEST evidence from satisfying production evidence gates;
7. add the pre-production and post-release calibration reports to the evidence model.
