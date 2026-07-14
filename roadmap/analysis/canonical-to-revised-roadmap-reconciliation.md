# Canonical-to-Revised Roadmap Reconciliation

> **Authority class: Class 3 — roadmap reconciliation analysis.**
> This revision incorporates Enki as the deliverable, mandatory internal publication-POC validation, and deferral of only the external production effect. It does not change canonical sprint status until promoted through governed work control.

## Governing correction

Enki is the deliverable. The first-live-publication work originated as the proof of concept for a downstream Media Blitz product line.

The correction is not to stop testing that lane. It is to distinguish:

1. **mandatory internal publication-shaped validation before Enki release**; from
2. **actual external Media Blitz production publication after Enki release**.

All Sprints 5–13 remain TEST-only until every governed lane has passed automated path-complete proof and an explicit Enki release decision is recorded.

## Structural reconciliation

| Current canonical topology | Incorrect interpretation | Corrected Enki topology |
|---|---|---|
| `S1 → S2 → S3(blocked) → S4 → S5 → … → S11` | Remove or defer the publication POC entirely until after Enki release | Foundation `S1 → S2 → S4`; Enki construction `S5 → … → S13`; mandatory internal publication-POC test lane converges in S13; only live external publication is deferred |
| Sprint 3 is positioned as an early production dependency | Sprint 3 becomes irrelevant to Enki testing | Sprint 3 is decomposed: its internal no-effect test obligations move into integrated Enki validation; its external production effect moves to downstream Media Blitz release |
| Production publication appears to validate the platform | No publication-shaped validation occurs | Enki is validated internally using a full publication-shaped downstream-consumer path plus at least one other adaptive lane |
| Testing requirements are uneven | POC artifacts are merely historical | POC artifacts remain active mandatory fixtures under path-complete automated TEST policy |

## Side-by-side sprint reconciliation

| Canonical sprint | Current canonical purpose | Corrected destination | Reconciliation treatment | Why |
|---|---|---|---|---|
| **S1 — Canonical identity and repository truth** | Establish schema-aware canonical identity and reconcile stale branches | **S1 — unchanged** | Preserve complete | Historical scope and evidence remain valid |
| **S2 — Canonical backlog and roadmap control plane** | Make work status evidence-bearing and deterministically projected | **S2 — unchanged** | Preserve complete | Governs this roadmap revision |
| **S3 — First live publication cycle** | Approve, publish, receipt, observe, and collect feedback for Publication 000001 | **Internal POC obligations distributed into S5–S13, culminating in S13; external production transferred to Media Blitz** | Decompose, do not discard | The production-shaped path must be tested internally; only the live external effect is deferred |
| **S4 — Restricted canonical writer** | Enforce one canonical mutation boundary | **S4 — unchanged** | Preserve complete | Later work extends this boundary |
| **S5 — Journaled promotion and approval isolation** | Recoverable promotion and TEST/PRODUCTION approval isolation | **S5 — Context-Bound Approval and Transaction Foundation** | Expand and generalize | Supplies approval, transaction, rollback, recovery, and receipt semantics used by the POC and every other lane |
| **S6 — Temporal human-state testable reference implementation** | Productionize human-state behavior before generalization | **Primarily S8**, supported by **S5, S7, S9, S10, and S11** | Recast as governed human overlay and migration | Human-state cannot define generic Enki ontology |
| **S7 — Governed Adaptive Knowledge state and approval substrate** | Generalize state and approval contracts | **S6 + S7** | Split constitutional core from governed state creation | Architecture and persistence require separate proof boundaries |
| **S8 — Governed transition, conflict, and approval engine** | Govern state change and conflict | **S10 — Governed Transition and Conflict Engine** | Move after state, migration, and reconciliation stabilize | Transition semantics consume those capabilities |
| **S9 — Interpretation resolution and model-use boundary** | Resolve interpretation and govern model use | **S9 + S11** | Split reconciliation/disclosure from downstream influence | These operations have different authority and privacy boundaries |
| **S10 — Forensics, migration, and portability** | Reconstruction, migration, adapter parity, and recovery | **S8 + S12** | Split human migration from system-wide reconstruction | Migration belongs with human compatibility; forensics is cross-operation |
| **S11 — Two-lane proof, hardening, and release candidate** | TEST loops, production cycle, chaos, hardening, release | **S11 + S12 + S13**, with external production transferred to Media Blitz | Retain full internal publication-shaped proof; remove only live external effect | Enki release requires rigorous internal consumer-lane proof, not live publication |
| **No canonical S12** | — | **S12 — Forensic Reconstruction, Portability, and Governed Work Completion** | Create | Gives reconstruction and evidence-bearing completion an explicit boundary |
| **No canonical S13** | — | **S13 — Integrated Internal TEST Proof and Enki Release Candidate** | Create | Executes every Enki path, including the complete no-effect publication POC lane, before release |

## Sprint 3 decomposition

### Internal obligations retained before Enki release

The following remain mandatory:

- exact content-body and visual-manifest objects;
- production-shaped configuration fixtures;
- review and exact-hash TEST approval;
- publication-package construction;
- no-effect publication and distribution adapters;
- TEST publication and distribution receipts;
- simulated observation windows;
- `SYNTHETIC/TEST`, `REPLAY/TEST`, and controlled `REAL/TEST` feedback;
- feedback classification, routing, deduplication, disposition, and calibration;
- all denial, mismatch, stale, expiry, revocation, duplicate, interruption, retry, rollback, recovery, tamper, and privilege-escalation paths;
- deterministic reconstruction.

These obligations are distributed across Sprints 5–13 and must converge in Sprint 13 as one complete downstream-consumer lane.

### External obligations deferred until after Enki release

- live publication and distribution;
- production accounts, credentials, endpoints, callbacks, and transports;
- actual audience observation;
- `REAL/PRODUCTION` feedback or production zero-feedback receipts;
- post-publication production calibration.

## Capability lineage

### Publication POC lineage

```text
Canonical S3 artifacts and workflow
→ S5 approval and transaction semantics
→ S7 governed object/state creation
→ S9 reconciliation and disclosure decisions
→ S11 package construction and no-effect dispatch
→ S12 receipts, reconstruction, portability, and recovery
→ S13 complete internal publication-shaped lane
→ Enki release decision
→ later Media Blitz production release
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
→ Revised S13 integrated internal TEST proof across multiple lanes
→ explicit Enki release decision
```

## Testing-policy reconciliation

The automated path-complete TEST policy is cross-cutting and mandatory for Sprints 5–13.

Every governed operation and every integrated consumer lane must:

1. declare success, denial, invalid-input, stale-input, duplicate, conflict, interruption, rollback, recovery, replay, tamper, and escalation paths;
2. automate every declared path;
3. prove rollback, compensation, isolated discard, or exact recovery for each state-changing path;
4. prove no TEST path can reach production capability;
5. fail coverage when any path is absent or untested; and
6. bind immutable evidence to the exact implementation commit.

All testing remains internal until S13 completes and governing authority approves Enki release.

## Status reconciliation

| Sprint | Canonical status now | Corrected planning treatment | Implementation assessment |
|---|---|---|---|
| S1 | complete | preserve complete | complete |
| S2 | complete | preserve complete | complete |
| S3 | blocked | decompose: retain mandatory internal POC test obligations; transfer only external production effect to Media Blitz | internal lane required; live effect not required |
| S4 | complete | preserve complete | complete |
| S5 | planned | rescope and generalize | partial |
| S6 | planned | replace scope with Enki core boundary | ready for completion review |
| S7 | planned | replace scope with governed generic state write | partial |
| S8 | planned | replace scope with human compatibility and migration | partial |
| S9 | planned | replace scope with reconciliation and disclosure | partial |
| S10 | planned | replace scope with transition/conflict engine | implementation missing |
| S11 | planned | replace scope with governed interpretation/model use | partial, strong substrate |
| S12 | absent | create | partial capability evidence; record absent |
| S13 | absent | create as integrated internal proof across publication POC and at least one other lane | design and TEST authority resolved; implementation missing |

## Dependencies removed from Enki

The following no longer gate Enki release:

- reachable live publishing accounts and credentials;
- actual external publication and distribution;
- real production audience availability;
- production observation-window passage;
- production feedback or production zero-feedback receipts;
- production post-publication calibration.

## Dependencies retained inside Enki testing

The corresponding internal behaviors remain mandatory:

- content, visual, configuration, approval, package, dispatch, receipt, observation, feedback, and calibration paths;
- no-effect adapters and production-shaped fixtures;
- every positive and negative path;
- rollback, recovery, tamper resistance, and reconstruction;
- integrated publication-POC proof plus at least one additional adaptive lane.

## Corrected execution topology

```text
HISTORICAL FOUNDATION
S1 → S2 → S4

ENKI CAPABILITY CONSTRUCTION
S5 → S6 → S7 → S8 → S9 → S10 → S11 → S12

INTEGRATED INTERNAL VALIDATION
S13
├─ complete publication-shaped POC lane through no-effect adapters
├─ complete at least one additional adaptive lane
├─ execute full cross-operation path matrix and chaos proof
└─ produce versioned Enki release candidate

RELEASE
explicit Enki release decision

AFTER ENKI RELEASE
separate Media Blitz production authorization and live publication
```

## Canonical promotion transaction

```text
record approval of the corrected roadmap
→ preserve S1, S2, and S4 unchanged
→ decompose S3 without erasing history
→ migrate its internal TEST obligations into revised S5–S13 exit criteria
→ transfer only its external production work to downstream Media Blitz backlog
→ create/update canonical S5–S13 and corresponding backlog records
→ incorporate path-complete internal TEST criteria
→ regenerate canonical roadmap, backlog, authority manifest, and audit
→ run all required workflows
→ verify deterministic projections and zero authority drift
```

## Final reconciliation finding

The publication lane is not removed from testing.

It remains a mandatory internal production-shaped proof of Enki's ability to serve a downstream consumer. The correction removes only the need to cause a real external publication effect before Enki itself is ready to release.
