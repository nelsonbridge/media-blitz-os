# State Authority Model

## Purpose

This document defines which repository artifacts are authoritative, how conflicting state is resolved, and which files may be edited manually.

The repository must not contain multiple artifacts that independently claim to represent current system truth.

## Authority Classes

### Class 1 — Canonical Machine State

Canonical machine state is the source of truth for operational facts.

It consists of validated domain records and append-only workflow records persisted by the runtime, including canonical JSON records, events, receipts, approvals, feedback records, and other schema-governed state.

Rules:

- Canonical records may be changed only through validated runtime operations, migrations, reconciliation, or an explicitly documented recovery procedure.
- Canonical identifiers, lineage, approvals, provenance, and state transitions must not be inferred from narrative documents.
- When canonical records conflict with any Markdown summary, canonical records win.
- Human-readable convenience must never silently overwrite canonical state.

### Class 2 — Generated Authoritative Projections

Generated authoritative projections are deterministic views or payload families derived from Class 1 state.

Current examples include files under `generated/`, such as publication, proof, visual, event, feedback, capability, and repository-audit indexes, plus governed model-feedback payload and receipt pairs.

Rules:

- Class 2 files must be produced by a documented generator or audit command.
- Class 2 files must never be manually maintained.
- Every Class 2 file or output family must identify its generator and input scope in `generated/state-authority-manifest.json`.
- A change to a Class 2 file without the corresponding canonical or generator change is invalid.
- Regeneration must be idempotent for unchanged canonical input.
- When two generated projections conflict, the conflict is a generator or input-scope defect and must be reconciled against Class 1.
- An optional output family may be absent when no authorized operation has produced it.
- Once any member directory of an output family exists, every file required by that family must exist. Partial payload or receipt pairs fail verification.

### Class 3 — Non-Authoritative Narrative and Historical Material

Class 3 contains explanatory, planning, transitional, historical, and human-authored documents.

Examples include architecture explanations, audit narratives, decision records, historical project ledgers, plans, and manually maintained status summaries.

Rules:

- Class 3 documents may explain canonical state but cannot establish it.
- Every Class 3 document that resembles a current status source must carry an explicit non-authoritative notice.
- Historical documents should preserve the state and assumptions that existed when they were written rather than being repeatedly rewritten to resemble current state.
- Backlogs and execution queues govern intended work only when explicitly designated as the active queue; they do not prove implementation state.
- A narrative claim that conflicts with Class 1 or Class 2 must be corrected, archived, or clearly marked obsolete.

## Precedence

When repository artifacts disagree, use this order:

1. Validated Class 1 canonical machine state.
2. Class 2 projections regenerated from that canonical state.
3. Explicitly designated active policy and execution documents for intent, not implementation facts.
4. Class 3 narrative or historical material.
5. Conversational memory, external summaries, and unstored assumptions.

A lower-precedence artifact must never be used to overwrite a higher-precedence artifact without an explicit reconciliation or migration operation.

## Current Classification

### Class 1

- Runtime-managed canonical domain records.
- Append-only workflow events.
- Recorded approvals, publication receipts, feedback records, and promotion lineage.

### Class 2

The complete machine-readable inventory is `generated/state-authority-manifest.json`.

It currently includes:

- generated publication, proof, visual, event, feedback, graph, health, runtime, package, and capability projections;
- generated repository audit reports;
- optional `generated/model-feedback/*/` output-family members, each requiring both `payload.json` and `receipt.json` when present;
- no manually maintained status document.

### Class 3

- `runtime/STATUS.md` until it is generated from canonical state.
- `docs/master-state-index.md` until it is generated from canonical state.
- `docs/project-state.md`, retained as an historical project ledger.
- Audit narratives, architecture documents, ADRs, plans, and backlog documents unless explicitly generated.

## Implemented Repository Controls

The following controls are active:

1. `generated/state-authority-manifest.json` records Class 1 scope, Class 2 projection inventory, optional generated-output families, generator ownership, and source scope.
2. `python -m nks.views.authority verify .` rejects a missing, invalid, or stale manifest, missing required Class 2 projections, and incomplete generated-output family members.
3. `nks generate-views .` deterministically regenerates the standard Class 2 projections.
4. `.github/workflows/state-authority.yml` runs authority tests, verifies the manifest, regenerates projections, and fails when committed generated output differs.
5. Generated views carry a warning that they must not be manually edited.
6. Model-feedback output directories may be absent, but any present directory must contain both its payload and receipt.

Remaining controls:

1. Extend repository audit findings to detect undeclared status-like files and contradictory Class 3 claims.
2. Require canonical-input or generator changes whenever a Class 2 artifact changes.
3. Add source revision metadata where it improves diagnosis without compromising deterministic output.
4. Replace the legacy model-feedback generator reference after the governed writer becomes the production path.

## Transitional Decision

`runtime/STATUS.md` and `docs/master-state-index.md` currently contain useful reconciled summaries, but they are manually maintained. They are therefore Class 3 transitional documents and are not authoritative.

They may become Class 2 only after a deterministic generator owns their complete contents and CI verifies regeneration.

The current model-feedback output family is registered against the legacy `PublishHumanStateFeedback` generator because that is the implementation that presently writes the payload and receipt pair. The decomposed governed path must replace that generator declaration only when it owns production persistence and equivalent recovery controls.

## Operating Rule

Do not ask which status document is newest.

Regenerate the authoritative projections from canonical state, inspect any discrepancy as a defect, and reconcile the cause.
