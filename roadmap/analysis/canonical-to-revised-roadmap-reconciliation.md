# Canonical-to-Revised Roadmap Reconciliation

> **Authority class: Class 3 — roadmap reconciliation analysis.**
> This document compares the current eleven-sprint canonical roadmap with the proposed thirteen-sprint roadmap, including the approved automated path-complete TEST policy. It does not change canonical sprint status.

## Structural reconciliation

| Current canonical topology | Revised topology |
|---|---|
| `S1 → S2 → S3(blocked) → S4 → S5 → … → S11` | Historical foundation: `S1 → S2 → S4`; internal lane: `S5 → … → S13`; parallel production lane: `S3` |
| Sprint 3 is positioned as an early sequential dependency | Sprint 3 becomes a parallel controlled-production and post-release calibration lane |
| Internal TEST proof and production proof are mixed in Sprint 11 | Internal TEST proof and release candidacy move to Sprint 13; actual production remains in Sprint 3 |
| Testing requirements are embedded unevenly in sprint prose | Path-complete automated TEST policy applies across Sprints 5–13 |

## Side-by-side sprint reconciliation

| Canonical sprint | Current canonical purpose | Revised destination | Reconciliation treatment | Why |
|---|---|---|---|---|
| **S1 — Canonical identity and repository truth** | Establish schema-aware canonical identity and reconcile stale branches | **S1 — unchanged** | Preserve complete | Historical scope and evidence remain valid |
| **S2 — Canonical backlog and roadmap control plane** | Make work status evidence-bearing, machine-readable, and deterministically projected | **S2 — unchanged** | Preserve complete | This control plane governs the roadmap revision itself |
| **S3 — First live publication cycle** | Complete Publication 000001 through approval, publication, receipts, and real feedback | **S3 — First Controlled Production Publication and Post-Release Calibration** | Reframe as parallel production lane | Publication is an external validation event, not a prerequisite for unrelated internal construction; audience response may be absent, so zero-feedback evidence is valid |
| **S4 — Restricted canonical writer** | Enforce one canonical source mutation boundary | **S4 — unchanged** | Preserve complete | Later work extends rather than bypasses this boundary |
| **S5 — Journaled promotion and approval isolation** | Recoverable canonical promotion plus TEST/PRODUCTION approval isolation | **S5 — Context-Bound Approval and Transaction Foundation** | Expand and generalize | The approval lifecycle becomes one reusable transaction foundation for promotion, state write, migration, disclosure, model use, transition, feedback, and work control |
| **S6 — Temporal human-state testable reference implementation** | Productionize human-state operations before generic generalization | **Primarily S8**, with support from **S5, S7, S9, and S11** | Move from reference implementation to governed human overlay and migration | Human-state behavior remains valid, but it must no longer define the generic Enki ontology |
| **S7 — Governed Adaptive Knowledge state and approval substrate** | Generalize human-state into platform-neutral state and approval contracts | **S6 + S7** | Split core boundary from state-write substrate | Constitutional Enki contracts and persistence-neutral boundaries are reviewed separately from governed state creation |
| **S8 — Governed transition, conflict, and approval engine** | Transactional state change with conflict semantics and recovery | **S10 — Governed Transition and Conflict Engine** | Move later after state, migration, and reconciliation stabilize | Transition semantics depend on stable generic state and human compatibility boundaries |
| **S9 — Interpretation resolution and context-bound model-use boundary** | Deterministic interpretation and purpose-limited model-use publication | **S9 + S11** | Split reconciliation/disclosure from downstream model influence | Internal reconciliation, external disclosure, and model-use dispatch require separate authority and review boundaries |
| **S10 — Forensic reconstruction, migration, and approval-context portability** | Reconstruction, migration, recovery, adapter parity, and escalation prevention | **S8 + S12** | Split migration from system-wide forensics and portability | Human migration belongs beside the human overlay; cross-operation reconstruction and portability are later integration capabilities |
| **S11 — Two-lane operational proof, hardening, and release candidate** | TEST loops, production cycle, chaos, hardening, and release decision | **S11 + S12 + S13 + S3** | Decompose into model-use hardening, forensics, integrated TEST proof, and production validation | One sprint previously mixed internal proof, external effects, recovery, release packaging, and audience evidence |
| **No canonical S12** | — | **S12 — Forensic Reconstruction, Portability, and Governed Work Completion** | New explicit sprint | Gives system-wide reconstruction, adapter parity, clean-room recovery, and evidence-bound completion their own review boundary |
| **No canonical S13** | — | **S13 — Integrated TEST Proof, Pre-Production Feedback Validation, and Release Candidate** | New explicit sprint | Proves the full production-shaped mechanism before production using synthetic, replay, and controlled real-human TEST evidence |

## Capability lineage

### Approval and transaction integrity

```text
Canonical S5
→ Revised S5 shared transaction foundation
→ consumed by S7, S8, S9, S10, S11, S12, and S13
```

### Human-state lineage

```text
Canonical S6 temporal human-state reference
→ Revised S8 human overlay and governed migration
→ generic storage supplied by S7
→ reconciliation supplied by S9
→ transition supplied by S10
→ model use supplied by S11
```

### Generic Enki lineage

```text
Canonical S7 generic state substrate
→ Revised S6 constitutional core and contracts
→ Revised S7 governed generic state creation
```

### Interpretation and model-use lineage

```text
Canonical S9
→ Revised S9 reconciliation and disclosure separation
→ Revised S11 interpretation and capability-isolated model use
```

### Reconstruction and release lineage

```text
Canonical S10 + S11
→ Revised S12 system-wide reconstruction and governed completion
→ Revised S13 integrated TEST proof and release candidate
→ Revised S3 final production transaction and post-release calibration
```

## Testing-policy reconciliation

The automated path-complete TEST policy is a cross-cutting completion rule, not a new sequential sprint.

Every governed operation in Sprints 5–13 must:

1. declare every success, denial, invalid-input, stale-input, duplicate, conflict, interruption, rollback, recovery, replay, and escalation path;
2. automate each declared path;
3. prove rollback, compensation, isolated discard, or exact recovery for state-changing paths;
4. prove TEST cannot reach an unapproved production effect;
5. fail coverage when a declared path is untested; and
6. bind immutable evidence to the exact implementation commit.

This changes the meaning of the roadmap gaps:

- testing permission is resolved;
- design for TEST execution is resolved;
- remaining gaps are executable operation construction, path declaration, automation, rollback/recovery proof, and evidence-bearing completion.

## Status reconciliation

| Sprint | Canonical status now | Revised planning treatment | Implementation assessment |
|---|---|---|---|
| S1 | complete | preserve complete | complete |
| S2 | complete | preserve complete | complete |
| S3 | blocked | keep open as parallel production boundary | TEST mechanics belong to S13; final production evidence pending |
| S4 | complete | preserve complete | complete |
| S5 | planned | rescope and generalize | partial |
| S6 | planned | replace scope with Enki core boundary | ready for completion review |
| S7 | planned | replace scope with governed generic state write | partial |
| S8 | planned | replace scope with human compatibility and migration | partial |
| S9 | planned | replace scope with reconciliation and disclosure | partial |
| S10 | planned | replace scope with transition/conflict engine | implementation missing |
| S11 | planned | replace scope with governed interpretation/model use | partial, strong substrate |
| S12 | absent | create | partial capability evidence; sprint record absent |
| S13 | absent | create | design and TEST authority resolved; integrated implementation missing |

## Canonical promotion transaction

The reconciliation becomes governing only after the following transaction:

```text
human approval of PR #28
→ create/update canonical Sprint 3 and Sprint 5–13 records
→ create/update BL-003 and BL-005–BL-013 work-item records
→ preserve S1, S2, and S4 records and evidence unchanged
→ incorporate path-complete TEST criteria
→ regenerate canonical roadmap and backlog
→ regenerate authority manifest and repository audit
→ run all required workflows
→ verify deterministic projections and zero authority drift
```

## Reconciled roadmap

```text
HISTORICAL FOUNDATION
S1 Canonical identity
→ S2 Work-control plane
→ S4 Restricted canonical writer

INTERNAL CONSTRUCTION AND PRE-PRODUCTION VALIDATION
S5 Approval and transaction foundation
→ S6 Enki core boundary and generic contracts
→ S7 Governed generic state write
→ S8 Human compatibility and governed migration
→ S9 Reconciliation and disclosure separation
→ S10 Transition and conflict engine
→ S11 Governed interpretation and model use
→ S12 Reconstruction, portability, and governed completion
→ S13 Integrated TEST proof and release candidate

PARALLEL PRODUCTION LANE
S3 independently reviewed content, visuals, and configuration
→ exact PRODUCTION approval
→ external publication
→ observation window
→ REAL/PRODUCTION feedback or zero-feedback receipt
→ post-release calibration
```

## Final reconciliation finding

No completed historical sprint is rewritten.

The revision does four things:

1. removes Sprint 3 from the internal critical path;
2. separates constitutional core, generic state, human migration, reconciliation, transition, model use, reconstruction, integrated TEST proof, and production validation into independently reviewable capabilities;
3. applies automated rollback-capable path completeness across all internal governed operations; and
4. preserves Sprint 3 as the only lane that may claim actual external publication and production evidence.
