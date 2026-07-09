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
9. `Visual Package Needed`
10. `Visual Package Briefed`
11. `Signature Diagram Needed`
12. `Signature Diagram Briefed`
13. `Drafting`
14. `Drafted`
15. `Editorial Review`
16. `User Approval Needed`
17. `Ready for Medium`
18. `Published on Medium`
19. `Derivatives Needed`
20. `Distributed`
21. `Archived`
22. `Review Scheduled`

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
| Visual Package ID | Links to required visual package. |
| Signature Diagram ID | Links to required signature diagram for flagship assets. |
| Visual Status | Planned, Briefed, Generated, Reviewed, Approved, Published, or Archived. |
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
5. Visual Package is created or explicitly waived.
6. Signature Diagram is briefed for flagship publications or explicitly waived.
7. Audience, brand-risk, and public-risk fields are complete.
8. User approval is recorded.

## Public Publishing Rule

The assistant may draft, package, proof, visually brief, and queue assets. The user remains final public-publishing approver until explicitly delegated otherwise.

## Operating Principle

Source first. Proof second. Narrative arc third. Visual package fourth. Publication fifth.