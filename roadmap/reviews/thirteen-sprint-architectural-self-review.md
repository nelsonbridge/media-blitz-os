# Architectural Self-Review — Thirteen-Sprint Proposal

> **Authority class: Class 3 — analytical review.**
> This is a design-quality assessment, not the governing human approval required to promote the roadmap.

- Proposal reviewed: `roadmap/proposals/revised-thirteen-sprint-plan.md`
- Required correction: `roadmap/proposals/feedback-validation-amendment.md`
- Review result: `RECOMMEND APPROVAL WITH EXPLICIT CLARIFICATIONS AND FEEDBACK AMENDMENT`
- Blocking architectural defects found: none after applying the dependency and feedback interpretations below

## Review conclusion

The revised roadmap is structurally stronger than the eleven-sprint plan because it replaces broad mixed-capability sprints with smaller evidence boundaries and separates internal construction from external validation.

The strongest architectural distinction remains:

- Sprint 13: internally complete, reconstructable, and pre-production validated release candidate; and
- Sprint 3: explicitly authorized production publication, observation, and post-release calibration.

The original thirteen-sprint draft still contained one defect: it required actual audience feedback in Sprint 3 without first proving the feedback subsystem before production and without accounting for the valid possibility that no audience member responds. The feedback-validation amendment corrects this by requiring synthetic, replay, and controlled human TEST validation before production, while allowing Sprint 3 to record either observed production feedback or a zero-feedback receipt after a defined observation window.

## Finding 1 — No work-control bootstrap paradox

### Risk

Sprint 12 includes a stronger governed work-completion transaction. Read literally, that could create a circular dependency in which Sprints 5–11 cannot be completed until Sprint 12 exists, while Sprint 12 cannot be reached until Sprints 5–11 are complete.

### Governing interpretation

There are two distinct capabilities:

1. **Existing evidence-bearing work control.** The current canonical work records, restricted write path, deterministic projections, pull-request review, and repository checks are sufficient to record completion of Sprints 5–11 when qualifying evidence exists.
2. **Sprint 12 hardening.** Sprint 12 adds journaled amendment execution, recovery, reconstruction, and privilege-escalation resistance for future work-control mutations.

Sprint 12 hardening is not a retroactive prerequisite for earlier completion records. Earlier completion transactions must use the strongest currently available governed path and remain reconstructable from commits, reviews, canonical records, evidence references, and generated projections.

### Required canonical wording

The Sprint 12 amendment should state that it **hardens and generalizes** work-control mutation; it does not invalidate prior evidence-bearing work-control operations performed under the existing authority model.

## Finding 2 — Adapter parity must be bounded

### Risk

“Filesystem and GitHub adapter parity” can become an unbounded requirement if interpreted as identical implementation internals or support for every future operation.

### Governing interpretation

Sprint 12 requires behavioral parity only for the contract surface declared supported by both adapters:

- authorization semantics;
- transaction identity;
- idempotency;
- recovery result;
- receipt content;
- audit reconstruction;
- context preservation.

Unsupported capabilities must be declared explicitly and fail closed. Implementation mechanisms do not need to be identical.

## Finding 3 — PR #27 must be treated as an evidence source, not a sprint

### Risk

The open Enki core refactor contains implementation spanning several revised sprint boundaries. Merging or rejecting it as a single unit could recreate the coupling this roadmap is intended to remove.

### Governing interpretation

PR #27 may be merged as an implementation substrate after its code and architecture review passes, but sprint completion must be assessed separately:

- map files, tests, schemas, receipts, and validation results to the revised exit criteria;
- reuse evidence across sprints only where the same artifact legitimately proves distinct claims;
- do not infer Sprint 10, Sprint 12, or Sprint 13 completion from the size of the PR;
- record gaps as bounded follow-on work rather than reopening satisfied criteria.

## Finding 4 — Sprint 3 may remain blocked without blocking the roadmap

### Risk

The word `blocked` can be misread as a global dependency rather than the state of one work item.

### Governing interpretation

Sprint 3 may remain canonically `blocked` or transition to another valid open state according to the work-control schema. Its dependency metadata and generated views must make clear that:

- the blockers apply to Sprint 3's production-effect completion only;
- Sprints 5–13 do not depend on Sprint 3;
- Sprint 3 and Sprint 13 converge as separate evidence lanes.

## Finding 5 — Sprint 13 is not a disguised production release

Sprint 13 may approve an internal release candidate and production-readiness handoff. It may not assert:

- public publication;
- successful production transport;
- production audience feedback;
- production model ingestion;
- production validation;
- authorization to cause an external effect.

Those claims remain with Sprint 3 or a later explicitly authorized production operation.

## Finding 6 — Real feedback and production context must remain separate

### Defect in the prior draft

The prior draft used “REAL feedback” as though it necessarily followed public production and could be required as controllable sprint work.

### Governing interpretation

Feedback uses two independent dimensions:

- provenance: `REAL | SYNTHETIC | REPLAY`;
- execution context: `TEST | PRODUCTION`.

A real human evaluator may produce `REAL/TEST` feedback through a non-side-effecting interface. That is genuine human feedback, but it cannot satisfy a production evidence gate.

Pre-production validation must combine:

- `SYNTHETIC/TEST` for coverage and adversarial cases;
- `REPLAY/TEST` for regression where historical cases exist;
- `REAL/TEST` for controlled human interaction;
- deterministic pipeline, disposition, audit, zero-feedback, and calibration proof.

After production, the observation window yields either:

- `REAL/PRODUCTION` feedback records; or
- an immutable zero-feedback receipt.

The system controls collection readiness and evidence capture. It does not control whether an audience chooses to respond.

## Review of sprint ordering

The proposed order is coherent:

1. authority before effects;
2. constitutional core before generic persistence;
3. generic persistence before human migration;
4. human semantic protection before authoritative reconciliation;
5. reconciliation before transitions derived from findings;
6. transitions before downstream model influence;
7. operation families before system-wide reconstruction;
8. reconstruction and pre-production feedback validation before release-candidate approval;
9. production authorization before external publication and post-release calibration.

No ordering inversion requires correction after applying the feedback amendment.

## Scope-pressure review

The densest revised sprint is Sprint 12. Its scope remains acceptable only because the common outcome is one capability: forensic portability of governed authority and state. During execution, it should be implemented as independently testable operation-family reconstructions and then closed by one cross-family recovery proof.

Sprint 13 is also substantial after adding feedback validation. It must remain an execution-and-evidence sprint. The synthetic scenario corpus, replay harness, controlled human evaluation, and calibration report all serve one outcome: proving the release candidate before production. New domain features discovered there return to the backlog unless required to satisfy an approved exit criterion.

## Recommendation

Approve the roadmap proposal only with the feedback-validation amendment incorporated into the canonical amendment:

- existing work control is sufficient for pre-Sprint-12 evidence-bearing completion;
- Sprint 12 hardens rather than bootstraps work control;
- adapter parity is contract-bounded;
- PR #27 is an evidence source spanning sprints;
- Sprint 3's blocked state is lane-local;
- Sprint 13 remains an internal release-candidate claim only;
- the feedback pipeline is proven before production with SYNTHETIC/TEST, REPLAY/TEST where available, and controlled REAL/TEST evidence;
- Sprint 3 records observed REAL/PRODUCTION feedback or a zero-feedback receipt rather than requiring an audience response.

The proposal changes planning authority only. Implementation status must be reviewed sprint by sprint after canonical promotion.
