# Branch Strategy

## Governing Model

The repository maintains exactly two long-lived branches:

- `main` — canonical, releasable authority.
- `sandbox` — continuous manufacturing and integration.

All other branches are temporary execution artifacts.

## Rules

1. Temporary branches must be merged or explicitly abandoned promptly.
2. Merged branches are deleted automatically.
3. A nonmerged branch may be deleted only after its tip is preserved by an immutable archive tag.
4. Historical truth is preserved through commits, pull requests, evidence records, and tags—not branch accumulation.
5. `main` must represent a validated canonical state.
6. `sandbox` may advance ahead of `main` while work is being manufactured and validated.
7. Release milestones use immutable tags rather than long-lived release branches.
8. No permanent `develop`, `release/*`, `hotfix/*`, `feature/*`, `agent/*`, `execution/*`, `governance/*`, `roadmap/*`, `product/*`, `security/*`, `sprint/*`, or `ci/*` branches are permitted.

## Cleanup Invariant

After repository cleanup, the complete long-lived branch set is:

```text
main
sandbox
```

Any future third branch must be short-lived and removed automatically after merge or explicit abandonment.