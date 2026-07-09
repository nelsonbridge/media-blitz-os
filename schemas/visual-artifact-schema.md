# Visual Artifact Schema

## Purpose

Defines the metadata structure for visual artifacts within the Nelson Knowledge System.

Visual artifacts are first-class corpus derivatives. They must be traceable to source material, proof posture, canonical artifacts, narrative arc status, publication package, and distribution channel.

## ID Prefixes

- `NKS-VIS` — visual artifact package
- `NKS-DGM` — diagram
- `NKS-HRO` — hero image
- `NKS-CAR` — carousel
- `NKS-QTC` — quote card
- `NKS-PIN` — Pinterest vertical
- `NKS-SLD` — presentation slide
- `NKS-PRF` — proof graphic

## Required Fields

| Field | Description |
|---|---|
| Visual ID | Stable identifier. |
| Title | Human-readable title. |
| Visual Type | Diagram, hero, carousel, proof graphic, quote card, etc. |
| Parent Artifact ID | Canonical corpus artifact. |
| Parent Publication ID | Publication package if applicable. |
| Source Record ID | Source lineage. |
| Proof Status | Unverified, partially sourced, sourced, evidence-complete. |
| Narrative Arc Segment | Recognition, Reframe, Framework, Proof, Application, Consequence, Invitation. |
| Intended Platform | Medium, LinkedIn, X, Instagram, Pinterest, Slides, Drive. |
| Format | Aspect ratio, dimensions, file type. |
| Core Claim | Claim the visual expresses. |
| Evidence Boundary | What the visual may and may not imply. |
| Text Elements | Labels, captions, callouts. |
| Visual Components | Shapes, icons, flow, layers. |
| Status | Planned, briefed, generated, reviewed, approved, published, archived. |
| Drive Sync Status | Pending, queued, synced, verified. |
| Review Owner | User, assistant, external reviewer. |
| Last Updated | Date or run marker. |

## Required Status Flow

Planned
→ Briefed
→ Generated
→ Proof Checked
→ Narrative Checked
→ Editorial Reviewed
→ User Approved
→ Published / Archived

## Minimum Acceptance Criteria

A visual artifact is not complete unless:

1. It has a stable ID.
2. It has a parent artifact or publication package.
3. Its claim is traceable to source/proof.
4. Its narrative purpose is explicit.
5. Its platform format is defined.
6. It is represented in the Visual Package Index.

## Notes

Visual artifacts should be generated only after source and proof status are understood. This prevents visually compelling but unsupported claims from entering the publication pipeline.