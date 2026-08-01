# AUDIT-0002 Branch Cleanup Assessment

Status: Complete

## Objective

Record the live remote branch state, the completed remote-branch cleanup, and the issue backlog reassessment performed during that cleanup.

## Current State

The approved long-lived branch set is still exactly `main` and `sandbox`, as documented in `governance/branch-strategy.md`.

Live remote branch assessment after cleanup on 2026-08-01 UTC:

| Branch | Status | Action |
| --- | --- | --- |
| `main` | Approved long-lived branch | Retain |
| `sandbox` | Approved long-lived branch and current default branch | Retain |

The following refs are already absent as live remote refs:

- `agent/gcp00-current-sandbox`
- `agent/gcp00-validation-repair`
- `governance/promote-sprint-43-completion-v4`
- `copilot/clean-up-approved-branches`
- `copilot/cleanup-approved-branches`
- `copilot/audit-media-blitz-os-references`
- `ep-12-handoff`
- `copilot/restore-canonical-identity`

There is a material naming mismatch between `copilot/clean-up-approved-branches` and `copilot/cleanup-approved-branches`. They are distinct ref names. Both are now absent, but only the latter was a live branch that required deletion during this cleanup.

There are currently zero open pull requests in the repository.

There are 19 open issues. The active backlog is issue-driven and maps directly to the current GCP hosted platform roadmap rather than abandoned PR work.

Archive tags preserving deleted unique tips now exist for:

- `archive/branches/ep-12-handoff-835518c33dda`
- `archive/branches/copilot-restore-canonical-identity-fb4cdb043d24`

## Primary Findings

- The two redundant `copilot/*` branches were safe to delete because each tip matched `sandbox` exactly.
- `ep-12-handoff` was outside the approved branch set and not redundant, so it was preserved under an archive tag before branch deletion.
- `copilot/restore-canonical-identity` appeared during verification as a new unapproved agent branch carrying a unique tip; it was also preserved under an archive tag before deletion.
- The repository default branch remains `sandbox`; earlier cleanup evidence did not successfully update repository settings.
- The previous cleanup implementation mixed branch deletion with repository promotion and settings mutation.
- The previous automation path could force-update `main` to the `sandbox` SHA before deleting third branches.
- The open issues are not obvious stale noise; the repository roadmap still references Issues `#143` through `#157`, and other repository logic still records Sprint `26`, `27`, `28`, and `45` as blocked or incomplete rather than resolved.
- The GCP TEST narrative docs have been reconciled with the RC2 `CF-NEON-R2` architecture lock by marking them as retained prepared reference material rather than the selected hosted baseline.

## Remediation

1. Keep branch cleanup separate from default-branch changes, branch promotion, and repository-settings writes.
2. Resolve the architecture-governance split between the GCP TEST reference path and CF-NEON-R2 locked release artifacts before closing or rewriting related hosting issues.
3. If issue consolidation is desired later, do it through an explicit governed backlog rewrite rather than opportunistic closing during branch cleanup.

## Repository Changes From This Audit

- `scripts/cleanup_branches.py` now fails closed for destructive runs unless exact branch names are passed with `--branch`.
- `scripts/cleanup_branches.py` no longer force-aligns `main` or writes repository settings.
- `.github/workflows/branch-consolidation.yml` now produces a dry-run governance report instead of performing destructive branch mutation.
- The live remote refs `copilot/cleanup-approved-branches` and `copilot/audit-media-blitz-os-references` were deleted.
- The live remote refs `ep-12-handoff` and `copilot/restore-canonical-identity` were retired after preservation under archive tags.
- `docs/architecture/gcp-test-reference-architecture.md` and `docs/roadmaps/gcp-hosted-platform-roadmap.md` were updated so they no longer conflict with the RC2 architecture lock.
- The issue backlog was reassessed and no issue was auto-closed because the open set still maps to active or explicitly blocked repository-planned work.

## Open Issue Reassessment Matrix

| Issue | Title | Recommendation | Rationale |
| --- | --- | --- | --- |
| #157 | GCP-15 — TEST Completion Gate | KEEP | Terminal gate for the active GCP TEST execution chain. |
| #156 | GCP-14 — TEST Drift and State Reconciliation | KEEP | Required reconciliation gate immediately before completion gate. |
| #155 | GCP-13 — Security and Authority Regression | KEEP | Security and authority regression evidence remains required. |
| #154 | GCP-12 — Restart, Rollback, Backup, and Recovery Proof | KEEP | Recovery and rollback proof remains an explicit requirement. |
| #153 | GCP-11 — Observability and Runtime Identity | KEEP | Runtime identity and observability controls remain planned and unresolved. |
| #152 | GCP-10 — Hosted Functional Smoke Suite | KEEP | Hosted functional validation remains part of the execution sequence. |
| #151 | GCP-09 — First Enki Hosted Boot | KEEP | First hosted boot remains a required chain milestone. |
| #150 | GCP-08 — Enki TEST Application Deployment Pipeline | KEEP | Deployment pipeline milestone remains active and uncompleted. |
| #149 | GCP-07 — Cloud Run Runtime Foundation | KEEP | Runtime foundation is still in the active GCP chain. |
| #148 | GCP-06 — Hosted Persistence Adapter and Migration Proof | KEEP | Persistence migration proof remains unresolved. |
| #147 | GCP-05 — Hosted Persistence Foundation | KEEP | Persistence foundation remains a prerequisite in the same chain. |
| #146 | GCP-04 — Persistence Decision Lock | KEEP | Explicit planned human architecture gate in the current chain. |
| #145 | GCP-03 — Governed Build and Artifact Publication | KEEP | Artifact governance milestone remains active and unresolved. |
| #144 | GCP-02 — Enki Container Contract | KEEP | Container contract gate remains in the active GCP runway. |
| #143 | GCP-01 — TEST Resource Foundation | KEEP | First executable issue in the active GCP TEST runway. |
| #137 | Unblock Sprint 45: configure and independently validate production controls | UPDATE | Keep open; align wording references with reconciled architecture-governance language and add explicit cross-link to RC2 lock. |
| #121 | Unblock Sprint 28: provide GCP, Neon, and R2 TEST capabilities | KEEP | Canonical sprint state still records this campaign as planned/unexecuted. |
| #120 | Unblock Sprint 27: provide Cloudflare, Neon, and R2 TEST capabilities | KEEP | Canonical sprint state still records this campaign as planned/unexecuted. |
| #89 | Unblock Sprint 26: provide Cloudflare TEST execution capabilities | KEEP | Canonical sprint state still records this campaign as blocked on external capability. |

Consolidation decision: **No issue consolidation recommended yet**. A governed backlog rewrite should happen only when canonical sprint statuses or hosting-direction authority change, not during branch cleanup.

## Follow-up Command

The two-branch invariant is now restored. The next governance cleanup should target roadmap and issue consistency rather than additional branch deletion:

```bash
git ls-remote --heads origin
```
