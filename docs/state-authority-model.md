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

Generated authoritative projections are deterministic, human-readable views derived from Class 1 state.

Current examples include files under `generated/`, such as publication, proof, visual, event, feedback, capability, and repository-audit indexes.

Rules:

- Class 2 files must be produced by a documented generator or audit command.
- Class 2 files must never be manually maintained.
- Every Class 2 file must identify its generator, input scope, and generation timestamp or source revision when practical.
- A change to a Class 2 file without the corresponding canonical or generator change is invalid.
- Regeneration must be idempotent for unchanged canonical input.
- When two generated projections conflict, the projection produced from the broader or more recent canonical input does not automatically win; the conflict must be treated as a generator or input-scope defect and reconciled against Class 1.

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

- `generated/publication-index.md`
- `generated/proof-index.md`
- `generated/visual-package-index.md`
- `generated/visual-request-index.md`
- `generated/event-index.md`
- `generated/feedback-index.md`
- `generated/ecosystem-capabilities.md`
- `generated/audit/repository-audit.md`
- `generated/audit/repository-audit.json`

### Class 3

- `runtime/STATUS.md` until it is generated from canonical state.
- `docs/master-state-index.md` until it is generated from canonical state.
- `docs/project-state.md`, retained as an historical project ledger.
- Audit narratives, architecture documents, ADRs, plans, and backlog documents unless explicitly generated.

## Required Repository Controls

The runtime and repository audit should eventually enforce the following:

1. Every status-like document declares its authority class.
2. Every Class 2 artifact is reproducible through a documented command.
3. CI fails when regenerated Class 2 output differs from committed output.
4. CI fails when a Class 2 file is changed without a canonical-input or generator change.
5. The repository audit identifies stale Class 3 claims that contradict canonical state.
6. Generated files carry a warning that manual edits will be overwritten.
7. A single generated state manifest records canonical counts, active gates, generation revision, and projection inventory.

## Transitional Decision

`runtime/STATUS.md` and `docs/master-state-index.md` currently contain useful reconciled summaries, but they are manually maintained. They are therefore Class 3 transitional documents and are not authoritative.

They may become Class 2 only after a deterministic generator owns their complete contents and CI verifies regeneration.

## Operating Rule

Do not ask which status document is newest.

Regenerate the authoritative projections from canonical state, inspect any discrepancy as a defect, and reconcile the cause.