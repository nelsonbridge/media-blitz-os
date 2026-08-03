# ChatGPT Handover

## Handover Context

- Repository: `nelsonbridge/media-blitz-os`, pending administrative rename to the Project Enki repository slug.
- Date: `2026-08-02` local / `2026-08-03` UTC.
- Current goal: continue Project Enki execution without losing branch, architecture, hosting, issue, identity, or release-integrity governance alignment.

## Authoritative Current State

- The only approved persistent branches are `main` and `sandbox`.
- `main` was independently verified at `2b978d65787dd7a7b8db9f191aba6e73285559c8` immediately before the final branch-governance cleanup cycle.
- Do not rely on a hand-written `sandbox` SHA. Publishing this handover and merging validation work advances `sandbox`; query GitHub before using an exact tip as authority.
- Temporary validation branches must be removed after merge. The branch-governance workflow is responsible only for the exact merged PR head and must never move either protected branch.
- Preserved archive tags for retired branch tips include:
  - `archive/branches/ep-12-handoff-835518c33dda`
  - `archive/branches/ep-12-handoff-1ebd3bb000f6`
  - `archive/branches/copilot-restore-canonical-identity-fb4cdb043d24`
- No production deployment, publication, Terraform apply, spending authorization, architecture-authority change, or issue-state change was performed during repository validation.

## Completed Work

- Removed unapproved remote branches and restored the two-branch invariant.
- Preserved unique retired branch tips through archive tags before deletion.
- Reconciled hosting-direction narrative documents so they do not conflict with RC2 lock authority.
- Added an explicit open-issue reassessment matrix using `keep`, `update`, and `consolidate` dispositions.
- Updated issue `#137` with governance-alignment language and left it open and fail-closed.
- Completed and merged PR `#165`, establishing **Project Enki** as the authoritative parent-system identity across current documentation, governance, package metadata, runtime surfaces, generated projections, and release-integrity records.
- Preserved **Media Blitz** as a governed downstream publishing and career-opportunity product rather than rewriting valid product-scoped records.
- Added automated identity regression enforcement distinguishing current authority from historical truth.
- Completed repository-wide validation and remediation through PRs `#168` and `#169`.
- Corrected Windows filesystem portability, line-ending determinism, stale release-integrity evidence, current-authority identity exceptions, and branch-governance behavior.

## Repository-Wide Validation Evidence

### Integrated cross-platform baseline

PR `#168` validated the integrated repository before the final branch-governance hardening:

- Linux, Python `3.11.15`: `860` tests passed with `88.25%` branch-aware coverage.
- Windows Server 2025, Python `3.11.9`: `860` tests passed with `88.28%` branch-aware coverage.
- State Authority: passed.
- Work Control Authority: passed.
- Canonicalization Security: passed.
- Publication `000001` assets: passed.
- Runtime Coverage: passed.
- Docker build: passed.
- Terraform offline validation: passed.
- GCP bootstrap shell syntax: passed.
- Repository audit: `0` findings.

### Final branch-governance baseline

After expanding the cleanup guardrails and tests, PR `#169` validated the current code and governance surface:

- Linux, Python `3.11.15`: `867` tests passed.
- Exact branch-aware coverage: `88.2547661374364%` (`88.25%` reported).
- Linux, Python `3.12`: Runtime Coverage passed.
- State Authority, Work Control Authority, Canonicalization Security, Publication Assets, CI, and Runtime Coverage all passed on the final validation head.
- The focused branch-cleanup suite now covers explicit-target enforcement, protected-branch rejection, complete preflight, archive-before-delete behavior, merged-tip handling, dry-run immutability, absent-target recording, and protected-tip preservation.

## Branch Governance Authority

The branch cleanup path is now fail-closed:

- Non-destructive audit is the default.
- Destructive execution requires one explicit `--branch` value per target.
- `main` and `sandbox` are rejected as cleanup targets.
- The script verifies the complete projected final branch set before any mutation.
- A destructive run cannot proceed unless all live unapproved branches are explicitly named and the projected result is exactly `main` plus `sandbox`.
- Unique unmerged tips are archived before deletion.
- Merged tips may be deleted without redundant archives.
- The script does not update repository settings.
- The script does not move `main` or `sandbox`.
- The script verifies both protected branch SHAs remain unchanged.
- The standing workflow handles only the exact head branch of a merged PR into `sandbox`.
- Manual workflow execution is audit-only and produces no deletion.
- Branch-governance evidence is written to the GitHub Actions run summary and logs.

Historical note: the prior workflow did force-align `main` to `sandbox`. That behavior was discovered during top-to-bottom validation and removed. Preserve this as historical truth; do not describe the old workflow as having always been non-destructive.

## Project Identity Authority

- The authoritative parent-system identity is **Project Enki**.
- Media Blitz is a governed downstream product and does not own core Enki canonical knowledge or mutation authority.
- Historical, source, audit, schema, receipt, exact-URL, and product-scoped artifacts may retain legacy language where required for provenance and reconstructability.
- Current-authority documentation, navigation, package metadata, runtime text, and governance surfaces must use Project Enki.
- The Python package is `project-enki`; the primary CLI entry point is `enki`.
- The GitHub repository slug remains `nelsonbridge/media-blitz-os` until a separate repository-administration rename is performed. Do not report that administrative rename as complete until GitHub metadata confirms it.
- Three current GCP/bootstrap files retain the live repository slug because Workload Identity Federation trust claims must match actual GitHub metadata. These are temporary operational exceptions, not parent-system identity exceptions.
- After the repository rename, migrate and verify the WIF trust boundary, redirects, remotes, Actions variables, external references, and exact-URL fixtures; then remove obsolete current-authority slug exceptions without rewriting immutable historical evidence.

## EP-12 Recurrence and Remediation

The retired `ep-12-handoff` branch reappeared after the initial cleanup. The recurrence was remediated again without changing the approved two-branch policy. Its reappeared tip was preserved under:

- `archive/branches/ep-12-handoff-1ebd3bb000f6`

Treat any future reappearance of `ep-12-handoff`, or any other non-approved branch, as a governance-control recurrence requiring exact-ref inspection, archive preservation where appropriate, explicit deletion, and final two-branch verification.

## Key Decisions Already Made

- Do not auto-close open issues.
- Keep issue chain `#143` through `#157` open as the active GCP runway.
- Keep issues `#89`, `#120`, and `#121` open in their blocked/planned canonical states.
- Keep issue `#137` open after its governance-alignment update. It remains the fail-closed production-control gate.

## Architecture Authority

- The RC2 architecture lock remains `CF-NEON-R2` as the production authority baseline.
- GCP documentation and issues represent a prepared TEST/control-plane path only.
- GCP work does not amend, replace, or override the RC2 architecture lock.
- Any architecture-authority change requires an explicit governed decision.

## Immediate Next Actions

1. Complete the GitHub repository administrative rename when repository-administration access is available.
2. After rename, migrate and verify GCP Workload Identity Federation repository and workflow claims before removing the live-slug exceptions.
3. Verify branch state, open PR state, and current `sandbox` SHA after every governance merge rather than relying on a static handover value.
4. Keep issue `#137` aligned with the RC2 architecture lock and open GCP TEST runway.
5. Keep the issue queue unchanged unless canonical sprint status or architecture authority changes.

## Local Workspace Warning

The local working tree was reported as heavily dirty with unrelated modified and untracked files.

- Do not run destructive cleanup against the local tree.
- Do not stage all changes.
- Scope commits to explicitly named files only.
- Distinguish local-only edits from remote authoritative state before reporting completion.
- Use the remote GitHub repository, not an uncommitted local tree, as the source of truth for repository status.

## Primary Evidence Artifacts

- `README.md`
- `pyproject.toml`
- `.gitattributes`
- `governance/enki-charter.md`
- `governance/media-blitz-product-charter.md`
- `docs/system-charter.md`
- `docs/governance/project-enki-identity-policy.md`
- `docs/infrastructure/gcp-execution-control-plane.md`
- `infrastructure/bootstrap/README.md`
- `infrastructure/bootstrap/bootstrap-gcp.sh`
- `tests/test_project_identity.py`
- `tests/test_release_integrity_evidence.py`
- `generated/audit/repository-audit.md`
- `generated/audit/branch-cleanup.json`
- `docs/audits/AUDIT-0002-Branch-Cleanup-Assessment.md`
- `docs/architecture/gcp-test-reference-architecture.md`
- `docs/roadmaps/gcp-hosted-platform-roadmap.md`
- `docs/chatgpt-handover.md`
- `scripts/cleanup_branches.py`
- `.github/workflows/branch-consolidation.yml`
- `tests/test_branch_cleanup.py`
