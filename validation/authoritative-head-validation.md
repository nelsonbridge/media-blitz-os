# Authoritative Head Validation Protocol

## Purpose

Prevent false-green validation caused by running checks against a stale, divergent, or non-authoritative workspace branch.

A passing local test suite is not evidence that the current Enki repository head is valid unless the tested commit is first proven to match the authoritative remote head.

## Authoritative branch

The repository default development authority is the remote `sandbox` branch unless an explicit governed repository decision changes that authority.

Validation must begin from the exact `origin/sandbox` commit, not from the currently checked-out local branch.

## Required provenance gate

Before any tests or diagnostics:

1. Record the current workspace branch, HEAD SHA, and `git status --short`.
2. Fetch `origin/sandbox`.
3. Resolve and record the exact `origin/sandbox` SHA.
4. Create a fresh isolated detached worktree from that exact SHA.
5. Record the isolated worktree HEAD SHA and `git status --short`.
6. Verify the isolated HEAD SHA exactly matches the recorded `origin/sandbox` SHA.
7. Stop and fail closed if the SHAs differ.

Pre-existing workspace changes are out of scope and must not be cleaned, reset, stashed, or incorporated into the validation run.

## Executable runner

Use the repository-owned runner for repeatable authoritative validation:

```bash
python scripts/validate_authoritative_head.py --repository-root .
```

The runner fetches `origin/sandbox`, creates a disposable detached worktree at the exact resolved SHA, verifies commit identity and initial cleanliness, executes the credential-free validation matrix below, rejects governed drift, emits a machine-readable JSON report, and removes the temporary worktree when complete.

Use `--keep-worktree` only when an investigator intentionally needs to retain the isolated validation worktree after the run. The runner must never reset, stash, clean, or otherwise alter pre-existing changes in the invoking workspace.

## Core CI-equivalent validation

Run from the SHA-verified isolated worktree:

1. Install the project and test dependencies with `.[test]`.
2. Generate the release-integrity evidence required by the current CI workflow.
3. Run the full pytest suite using repository-configured pytest and coverage settings.
4. Do not suppress the configured branch-coverage requirement or coverage fail-under threshold.

The final report must record the exact test count, warnings, total coverage, and coverage-gate result.

## Governed local validation surfaces

Execute every credential-free repository-local validation surface currently defined by `.github/workflows`, including where applicable:

- State Authority focused tests.
- State authority manifest verification.
- Generated projection regeneration and drift rejection.
- Work Control Authority focused tests.
- Work-control projection regeneration.
- Authority-manifest regeneration and verification.
- Canonicalization and restricted-writer security tests.
- Repository audit generation and drift rejection.
- Publication-asset deterministic rendering and verification.
- Runtime functional tests.
- Coverage validation.
- Credential-free branch-consolidation governance checks.

Workflow steps that require GitHub-hosted artifact services, remote branch mutation, repository-settings mutation, external credentials, spending authority, deployment authority, or human approval must remain skipped unless separately authorized. Each skipped check must be named with its exact reason.

## Drift policy

Any governed generated-state drift is a validation failure until its root cause is understood and corrected through an isolated change set.

Non-governed execution byproducts such as coverage reports, local logs, and bytecode caches must be distinguished from governed repository drift.

## Failure handling

If validation fails:

1. Identify the smallest root cause.
2. Modify only the isolated change set required to correct it.
3. Add or strengthen regression coverage where appropriate.
4. Re-run the complete affected validation surface.
5. Preserve all unrelated pre-existing changes.
6. Do not cross production, deployment, credential, spending, or human-authority gates.

## Required final report

Every authoritative-head validation report must include:

- exact `origin/sandbox` SHA;
- exact isolated worktree HEAD SHA;
- confirmation that the SHAs match;
- initial isolated `git status --short` result;
- Python version;
- exact full-suite test count;
- warnings count;
- total coverage and coverage-gate result;
- result of every governed local validation surface;
- generated-drift result;
- every skipped check and exact reason;
- comparison with any earlier workspace result when the earlier result materially differed.

## Reference validation baseline

The protocol was established after a stale workspace produced a misleading green result of 51 passing tests. The authoritative `origin/sandbox` head was then validated from an isolated worktree and produced 694 passing tests with 88.38% coverage and all credential-free governed validation surfaces passing.

The stale workspace was on `feature/canonical-record-path`, four commits ahead and 847 commits behind `origin/sandbox`. This demonstrated that local green status alone is insufficient evidence of current repository health.

Future validation runs must therefore prove commit identity before interpreting test success.
