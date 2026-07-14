# Architectural Self-Review — Thirteen-Sprint Proposal

> **Authority class: Class 3 — analytical review.**
> This is a design-quality assessment, not the governing human approval required to promote the roadmap.

- Proposal reviewed: `roadmap/proposals/revised-thirteen-sprint-plan.md`
- Review result: `RECOMMEND APPROVAL WITH EXPLICIT CLARIFICATIONS`
- Blocking architectural defects found: none after applying the dependency interpretations below

## Review conclusion

The revised roadmap is structurally stronger than the eleven-sprint plan because it replaces broad mixed-capability sprints with smaller evidence boundaries and separates internal construction from external validation.

The strongest correction is the distinction between:

- Sprint 13: internally complete and reconstructable release candidate; and
- Sprint 3: explicitly authorized external publication, receipts, and REAL feedback.

This preserves the value of production evidence without allowing an unavailable adapter, unreviewed visual, publishing account decision, or audience response to halt unrelated internal construction.

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

- the blockers apply to Sprint 3's external-effect completion only;
- Sprints 5–13 do not depend on Sprint 3;
- Sprint 3 and Sprint 13 converge as separate evidence lanes.

## Finding 5 — Sprint 13 is not a disguised production release

Sprint 13 may approve an internal release candidate and production-readiness handoff. It may not assert:

- public publication;
- successful production transport;
- REAL feedback;
- production model ingestion;
- production validation;
- authorization to cause an external effect.

Those claims remain with Sprint 3 or a later explicitly authorized production operation.

## Review of sprint ordering

The proposed order is coherent:

1. authority before effects;
2. constitutional core before generic persistence;
3. generic persistence before human migration;
4. human semantic protection before authoritative reconciliation;
5. reconciliation before transitions derived from findings;
6. transitions before downstream model influence;
7. operation families before system-wide reconstruction;
8. reconstruction before integrated release-candidate proof.

No ordering inversion requires correction.

## Scope-pressure review

The densest revised sprint is Sprint 12. Its scope remains acceptable only because the common outcome is one capability: forensic portability of governed authority and state. During execution, it should be implemented as independently testable operation-family reconstructions and then closed by one cross-family recovery proof.

Sprint 13 should remain an execution-and-evidence sprint. New domain features discovered there return to the backlog unless required to satisfy an already approved exit criterion.

## Recommendation

Approve the roadmap proposal with the four dependency interpretations above incorporated into the canonical amendment:

- existing work control is sufficient for pre-Sprint-12 evidence-bearing completion;
- Sprint 12 hardens rather than bootstraps work control;
- adapter parity is contract-bounded;
- Sprint 3's blocked state is lane-local;
- Sprint 13 remains an internal release-candidate claim only.

The proposal itself changes planning authority only. Implementation status must be reviewed sprint by sprint after canonical promotion.
