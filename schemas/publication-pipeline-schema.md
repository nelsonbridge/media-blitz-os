# Publication Pipeline Schema

The publication pipeline tracks how an idea becomes public intellectual property.

## Workflow States

1. `Captured`
2. `Classified`
3. `Evidence Needed`
4. `Drafting`
5. `Drafted`
6. `Editorial Review`
7. `Ready for Medium`
8. `Published on Medium`
9. `Derivatives Needed`
10. `Distributed`
11. `Archived`
12. `Review Scheduled`

## Required Pipeline Fields

| Field | Description |
|---|---|
| Pipeline ID | Stable workflow identifier. |
| Artifact ID | Links to artifact metadata record. |
| Current State | One workflow state. |
| Owner | Human, assistant, or shared. |
| Next Action | Concrete next action required. |
| Blocker | Exact blocker if any. |
| Medium Draft URL | Canonical draft location if available. |
| Published Medium URL | Public canonical URL after publishing. |
| Derivative Status | Not Started, In Progress, Complete. |
| Archive Status | Not Archived, Archived. |
| Review Date | Future review/update date. |

## State Transition Rule

An artifact cannot move to `Ready for Medium` until its evidence posture, audience, and brand-risk fields are complete.

## Public Publishing Rule

The assistant may draft and package assets. The user remains final public-publishing approver until explicitly delegated otherwise.
