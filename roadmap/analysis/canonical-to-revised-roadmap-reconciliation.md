# Canonical-to-Revised Roadmap Reconciliation

> **Authority class: Class 3 — roadmap reconciliation analysis.**
> This revision incorporates the Enki deliverable and production-deferral decision. It does not change canonical sprint status until promoted through governed work control.

## Governing correction

Enki is the deliverable. The first-live-publication work was the original proof of concept and belongs to the downstream Media Blitz product line, not to the Enki core completion path.

All Sprints 5–13 remain internal and TEST-only until every governed lane has passed automated path-complete proof and an explicit Enki release decision is recorded.

Sprint 3 is therefore preserved as historical proof-of-concept evidence and deferred downstream validation. It is not an active Enki production lane.

## Structural reconciliation

| Current canonical topology | Earlier thirteen-sprint proposal | Corrected Enki topology |
|---|---|---|
| `S1 → S2 → S3(blocked) → S4 → S5 → … → S11` | Foundation `S1 → S2 → S4`; internal `S5 → … → S13`; parallel production `S3` | Foundation `S1 → S2 → S4`; internal TEST-only Enki lane `S5 → … → S13`; explicit Enki release decision; publication POC deferred outside core roadmap |
| Sprint 3 is positioned as an early dependency | Sprint 3 is parallel but still shown as an active production lane | Sprint 3 is removed from the Enki execution topology and retained as downstream historical/deferred work |
| Production publication appears to validate the platform | Production is separated but remains a convergence lane | Enki correctness is proven internally; downstream production validates only the downstream product |
| Testing requirements are uneven | Path-complete testing applies to S5–S13 | Path-complete automated TEST is mandatory across every Enki lane before any Enki production release |

## Side-by-side sprint reconciliation

| Canonical sprint | Current canonical purpose | Corrected destination | Reconciliation treatment | Why |
|---|---|---|---|---|
| **S1 — Canonical identity and repository truth** | Establish schema-aware canonical identity and reconcile stale branches | **S1 — unchanged** | Preserve complete | Historical scope and evidence remain valid |
| **S2 — Canonical backlog and roadmap control plane** | Make work status evidence-bearing and deterministically projected | **S2 — unchanged** | Preserve complete | Governs this roadmap revision |
| **S3 — First live publication cycle** | Approve, publish, receipt, observe, and collect feedback for Publication 000001 | **Historical publication POC / deferred Media Blitz validation** | Remove from Enki critical path; preserve artifacts and history | Enki is not a publication engine; external publication is a downstream product concern |
| **S4 — Restricted canonical writer** | Enforce one canonical mutation boundary | **S4 — unchanged** | Preserve complete | Later work extends this boundary |
| **S5 — Journaled promotion and approval isolation** | Recoverable promotion and TEST/PRODUCTION approval isolation | **S5 — Context-Bound Approval and Transaction Foundation** | Expand and generalize | Supplies the reusable internal transaction and rollback foundation |
| **S6 — Temporal human-state testable reference implementation** | Productionize human-state behavior before generalization | **Primarily S8**, with support from **S5, S7, S9, S10, and S11** | Recast as governed human overlay and migration | Human-state cannot define the generic Enki ontology |
| **S7 — Governed Adaptive Knowledge state and approval substrate** | Generalize state and approval contracts | **S6 + S7** | Split constitutional core from governed state creation | Architecture and persistence require separate proof boundaries |
| **S8 — Governed transition, conflict, and approval engine** | Govern state change and conflict | **S10 — Governed Transition and Conflict Engine** | Move after state, migration, and reconciliation stabilize | Transition semantics consume those capabilities |
| **S9 — Interpretation resolution and model-use boundary** | Resolve interpretation and govern model use | **S9 + S11** | Split internal reconciliation/disclosure from downstream influence | These operations have different authority and privacy boundaries |
| **S10 — Forensics, migration, and portability** | Reconstruction, migration, adapter parity, and recovery | **S8 + S12** | Split human migration from system-wide reconstruction | Migration belongs with human compatibility; forensics is cross-operation |
| **S11 — Two-lane proof, hardening, and release candidate** | TEST loops, production cycle, chaos, hardening, release | **S11 + S12 + S13** | Remove external production; retain internal model use, reconstruction, integrated proof, and release | Enki release does not depend on a live publication cycle |
| **No canonical S12** | — | **S12 — Forensic Reconstruction, Portability, and Governed Work Completion** | Create | Gives reconstruction and evidence-bearing completion an explicit boundary |
| **No canonical S13** | — | **S13 — Integrated Internal TEST Proof and Enki Release Candidate** | Create | Executes all production-shaped behavior internally before Enki release |

## Sprint 3 disposition

Sprint 3 artifacts remain governed historical evidence:

- article body and visual work;
- configuration decisions and worksheets;
- review and approval models;
- publication and feedback receipt designs;
- production-shaped internal scenarios.

They may be reused as:

- internal fixtures for Sprints 9, 11, 12, and 13;
- no-effect publication rehearsal cases;
- downstream Media Blitz interface contracts;
- future Media Blitz production validation after Enki release.

They do not provide Enki completion evidence and do not need to reach production before Enki release.

## Capability lineage

### Approval and transaction integrity

```text
Canonical S5
→ Revised S5 shared transaction and path foundation
→ consumed by S7, S8, S9, S10, S11, S12, and S13
```

### Human-state lineage

```text
Canonical S6 temporal human-state reference
→ Revised S8 human overlay and governed migration
→ storage supplied by S7
→ reconciliation supplied by S9
→ transition supplied by S10
→ model use supplied by S11
```

### Generic Enki lineage

```text
Canonical S7
→ Revised S6 constitutional Enki core
→ Revised S7 governed generic state creation
```

### Reconstruction and release lineage

```text
Canonical S10 + S11
→ Revised S12 system-wide reconstruction and governed completion
→ Revised S13 integrated internal TEST proof and Enki release candidate
→ explicit Enki release decision
```

Publication is not part of this lineage. Media Blitz consumes the released Enki engine separately.

## Testing-policy reconciliation

The automated path-complete TEST policy is cross-cutting and mandatory for Sprints 5–13.

Every governed operation must:

1. declare success, denial, invalid-input, stale-input, duplicate, conflict, interruption, rollback, recovery, replay, and escalation paths;
2. automate every declared path;
3. prove rollback, compensation, isolated discard, or exact recovery for each state-changing path;
4. prove no TEST path can reach production capability;
5. fail coverage when any path is absent or untested;
6. bind immutable evidence to the exact implementation commit.

All testing remains internal until S13 completes and governing authority approves Enki release.

## Status reconciliation

| Sprint | Canonical status now | Corrected planning treatment | Implementation assessment |
|---|---|---|---|
| S1 | complete | preserve complete | complete |
| S2 | complete | preserve complete | complete |
| S3 | blocked | preserve as historical POC; defer or transfer unfinished work to Media Blitz | no Enki dependency |
| S4 | complete | preserve complete | complete |
| S5 | planned | rescope and generalize | partial |
| S6 | planned | replace scope with Enki core boundary | ready for completion review |
| S7 | planned | replace scope with governed generic state write | partial |
| S8 | planned | replace scope with human compatibility and migration | partial |
| S9 | planned | replace scope with reconciliation and disclosure | partial |
| S10 | planned | replace scope with transition/conflict engine | implementation missing |
| S11 | planned | replace scope with governed interpretation/model use | partial, strong substrate |
| S12 | absent | create | partial capability evidence; record absent |
| S13 | absent | create as internal integrated proof and Enki release candidate | design and TEST authority resolved; implementation missing |

## Dependencies removed from Enki

The following no longer gate any Enki sprint:

- final visual approval for Publication 000001;
- final article publication approval;
- channel, account, identity, byline, or brand production configuration;
- production publication transport or credentials;
- publication and social-distribution receipts;
- production audience observation;
- REAL/PRODUCTION publication feedback or zero-feedback receipt;
- post-publication calibration.

These belong to Media Blitz or another downstream product release.

## Dependencies that remain

The remaining dependencies are internal and directly executable:

```text
S5 shared transaction and path engine
→ S6 Enki constitutional core acceptance
→ S7 governed generic state creation
→ S8 governed human migration and protection
→ S9 governed reconciliation and disclosure
→ S10 transition and conflict engine
→ S11 privacy-governed interpretation and model use
→ S12 system-wide reconstruction, portability, and governed completion
→ S13 complete internal path matrix, chaos proof, calibration, and Enki release candidate
→ explicit Enki release decision
```

## Canonical promotion transaction

```text
record approval of the corrected roadmap
→ preserve S1, S2, and S4 unchanged
→ reclassify S3 as historical/deferred downstream POC without erasing its history
→ create/update canonical S5–S13 records
→ create/update corresponding backlog records
→ incorporate path-complete internal TEST criteria
→ remove publication production evidence from Enki exit criteria
→ regenerate canonical roadmap and backlog
→ regenerate authority manifest and repository audit
→ run all required workflows
→ verify deterministic projections and zero authority drift
```

## Final reconciliation finding

Yes, this correction removes most nontechnical dependencies.

It removes the publication product line, external accounts, production transport, visual and content publication approval, audience observation, and publication calibration from the Enki roadmap.

It does not remove the genuine internal engineering sequence. Sprints 5–13 must still build and rigorously prove the Enki engine. The remaining blockers are governed-operation implementation and automated evidence, not external publication.