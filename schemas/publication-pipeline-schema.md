# Publication Pipeline Schema

The publication pipeline tracks how an idea becomes public intellectual property.

## Workflow States

1. `Captured`
2. `Classified`
3. `Source Recorded`
4. `Proof Needed`
5. `Proof Logged`
6. `Citation Needed`
7. `Narrative Arc Needed`
8. `Narrative Arc Drafted`
9. `Drafting`
10. `Drafted`
11. `Editorial Review`
12. `User Approval Needed`
13. `Ready for Medium`
14. `Published on Medium`
15. `Derivatives Needed`
16. `Distributed`
17. `Archived`
18. `Review Scheduled`

## Required Pipeline Fields

| Field | Description |
|---|---|
| Pipeline ID | Stable workflow identifier. |
| Artifact ID | Links to artifact metadata record. |
| Publication ID | Links to publication package. |
| Source Record ID | Links to source lineage. |
| Current State | One workflow state. |
| Proof Category | Experiential, document-derived, repository-derived, publicly verified, quantitative, or unverified. |
| Proof Status | Current proof posture. |
| Narrative Arc Status | Arc Needed, Partial Arc, Arc Drafted, Arc Review Needed, or Arc Approved. |
| Public Risk | Low, Medium, High. |
| Owner | Human, assistant, or shared. |
| Next Action | Concrete next action required. |
| Blocker | Exact blocker if any. |
| Medium Draft URL | Canonical draft location if available. |
| Published Medium URL | Public canonical URL after publishing. |
| Derivative Status | Not Started, In Progress, Complete. |
| Archive Status | Not Archived, Archived. |
| Review Date | Future review/update date. |

## State Transition Rule

An artifact cannot move to `Ready for Medium` until:

1. Source lineage is recorded.
2. Proof posture is complete.
3. Required citations or evidence references are identified.
4. Narrative arc has reached at least `Arc Review Needed`.
5. Audience, brand-risk, and public-risk fields are complete.
6. User approval is recorded.

## Public Publishing Rule

The assistant may draft, package, proof, and queue assets. The user remains final public-publishing approver until explicitly delegated otherwise.

## Operating Principle

Source first. Proof second. Narrative arc third. Publication fourth.
