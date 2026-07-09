# ADR-0001 — Own the Contract Layer

## Status

Accepted.

## Context

The Nelson Knowledge System must integrate with external publishing, storage, visual, analytics, and automation tools while preserving modularity and long-term negotiating leverage.

Free/open-source packages still represent buy decisions. Their capital cost may be zero, but their architectural cost can become high if the system couples directly to their data models, workflow assumptions, approval models, or security boundaries.

## Decision

The Nelson Knowledge System will own its interface contracts.

External products may be used, forked, hosted, replaced, or bypassed, but they shall not own:

- corpus structure,
- source lineage,
- proof posture,
- narrative arc,
- visual package structure,
- approval state,
- publication package metadata,
- security boundary,
- audit trail,
- or prioritization logic.

All external systems integrate through NKS-owned contracts and replaceable adapters.

## Consequences

### Positive

- Vendors remain optional.
- Integration leverage is preserved.
- Security boundaries stay under NKS control.
- Platform changes do not require redesigning corpus/publication logic.
- Multiple distribution engines can be evaluated or replaced.

### Negative

- Increased upfront complexity.
- Requires schemas, adapters, validation, and technical backlog.
- Requires discipline to avoid bypassing the contract layer for convenience.

## Implementation Requirements

1. Define Publication Contract v1.
2. Define Visual Contract v1.
3. Define Adapter Contract v1.
4. Define Integration Security Boundary v1.
5. Score vendor packages by how cleanly they implement NKS contracts.

## Current Rule

Buy the infrastructure. Own the interface.