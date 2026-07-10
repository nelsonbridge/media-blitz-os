# Runtime v0.1 Status

## Current State

Wave 1 portable runtime implementation is committed on the `sandbox` branch.

The internal runtime, canonical record set, policy suite, filesystem adapter, and GitHub adapter contract are implemented. The functional core has now been executed locally from the committed runtime contents.

## Implemented

- Python project definition and package entry point.
- Platform-neutral domain records for sources, artifacts, proof, narrative, visuals, publications, and workflow events.
- Repository ports containing no GitHub or Google dependencies.
- Local filesystem JSON adapter.
- Append-only JSONL event adapter with duplicate-event protection.
- Executable governance validators for source, proof, narrative, visual, editorial, and user-approval gates.
- Application service that persists one complete publication package and evaluates readiness.
- CLI entry point.
- Idempotent end-to-end functional test.
- Negative gate tests for missing source, incomplete narrative arc, missing signature diagram, and missing user approval.
- Offline dependency-extraction tests for core imports and open JSON records.
- Canonical JSON records for NKS-SRC-000001, NKS-ART-000001, NKS-PRF-000001, NKS-NAR-000001, NKS-VIS-000001, and NKS-PUB-000001.
- Real-record readiness test for NKS-PUB-000001.
- GitHub repository adapter behind a minimal client protocol.
- GitHub adapter contract test using an in-memory fake client.
- GitHub Actions workflow configured to run the complete test suite.

## Architectural Boundaries Preserved

- Domain code imports no platform connector libraries.
- Application workflow depends on repository interfaces.
- GitHub-specific behavior is isolated in the GitHub adapter.
- GitHub Actions contains orchestration only, not business rules.
- Canonical records serialize as open JSON.
- Filesystem execution does not require network access.
- Repeated execution does not duplicate records or events.
- The GitHub adapter uses platform-neutral record models and the same repository behavior.

## Test Suite Scope

The committed suite covers:

Source
→ Artifact
→ Proof
→ Narrative Arc
→ Visual Package
→ Publication Package
→ Persistence
→ Readiness Validation
→ Event Audit
→ Idempotent Re-run

It also covers:

- explicit negative gate behavior;
- real publication readiness state;
- dependency leakage detection;
- canonical-record format checks;
- GitHub adapter contract behavior.

## Real Publication State

NKS-PUB-000001 is represented in canonical JSON.

Expected readiness result:

- Source: pass
- Proof: pass
- Narrative arc: pass
- Visual package: pass
- Editorial gate: pass
- User approval: pending

The real-record test expects `user approval is needed` as the sole publication-readiness failure.

## Verified Functional Result

Recent plugin reassessment established that local command execution is available even though direct network cloning of the repository is not.

The committed runtime core and tests were reconstructed from verified GitHub file contents and executed in the local isolated runtime.

Observed result:

- Test command: `pytest -q`
- Tests executed: 6
- Tests passed: 6
- Tests failed: 0
- Runtime: 0.14 seconds

This verifies the implemented functional core, idempotent filesystem workflow, negative readiness gates, and GitHub adapter record contract represented in the reconstructed suite.

## GitHub Actions Boundary

The GitHub workflow lookup previously used only returns pull-request-triggered runs. Its empty response did not prove that no push-triggered workflow existed.

The current connector surface can inspect jobs, logs, steps, artifacts, and rerun known jobs, but it does not currently expose a general workflow-run listing or manual workflow-dispatch action. GitHub Actions therefore remains an integration-observability limitation, not a blocker to functional runtime verification.

## Revised Next Work

1. Commit a formal local functional-test report.
2. Implement generated indexes from canonical records.
3. Add event persistence through the GitHub adapter.
4. Execute a full offline export/import dependency-extraction scenario.
5. Expand the reconstructed local suite to include the committed real-publication test and dependency-extraction tests if exact GitHub content retrieval is automated.
6. Reassess GitHub Actions when a general run-list or dispatch capability becomes available.
