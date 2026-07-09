# Publication Readiness Gate

## Purpose

This document defines the minimum conditions required before any artifact can move from internal draft to public release.

## Gate Sequence

```text
Source
  ↓
Proof
  ↓
Narrative Arc
  ↓
Editorial Review
  ↓
User Approval
  ↓
Publication
  ↓
Derivatives
```

## Gate 1 — Source

A publication must have traceable source lineage.

Required:

- Source record ID.
- Source artifact ID.
- Canonical artifact ID.
- Source location or reference.

Failure condition:

- No source lineage.
- Source is remembered but not recorded.
- Source cannot be separated from unsupported assertion.

## Gate 2 — Proof

A publication must identify proof posture before claim strength is finalized.

Required:

- Proof category.
- Proof status.
- Public risk level.
- Citation or evidence requirement.

Failure condition:

- Strong claims with weak proof.
- Quantitative claims without verification.
- Public/current claims without current sourcing.
- Personal or experiential claims framed as universal fact.

## Gate 3 — Narrative Arc

A publication must move the reader through a coherent arc.

Required:

- Recognition.
- Reframe.
- Framework.
- Proof.
- Application.
- Consequence.
- Invitation.

Failure condition:

- Starts too abstractly.
- Argues without reader recognition.
- Provides framework without application.
- Critiques without consequence.
- Ends without useful invitation.

## Gate 4 — Editorial Review

A publication must pass tone, brand, evidence, and strategic review.

Required:

- Review checklist complete.
- Brand-risk check complete.
- Proof posture and narrative arc aligned.
- Derivative boundaries confirmed.

Failure condition:

- Overclaiming.
- Generic thought-leadership tone.
- Unverified technical or market claims.
- Derivatives stronger than source publication.

## Gate 5 — User Approval

Public release remains user-approved unless explicitly delegated.

Required:

- User approval recorded.
- Platform target selected.
- Final version identified.

Failure condition:

- Draft is internal only.
- Approval is implied but not explicit.
- Platform action not authorized.

## Derivative Gate

Derivatives inherit source, proof, and arc constraints from the source publication.

A derivative may compress the arc, but it may not increase claim strength.

## Release Status Values

- `Internal Draft`
- `Proof Needed`
- `Citation Needed`
- `Arc Retrofit Needed`
- `Editorial Review Needed`
- `User Approval Needed`
- `Ready to Publish`
- `Published`

## Operating Principle

Nothing public without source, proof, arc, review, and approval.
