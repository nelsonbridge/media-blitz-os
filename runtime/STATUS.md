# Runtime v0.1 Status

## Current State

Wave 1 portable runtime implementation is committed on the `sandbox` branch.

The internal runtime, canonical record set, policy suite, filesystem adapter, and GitHub adapter contract are implemented. Actual test execution remains blocked because GitHub created no workflow run for commits matching the workflow trigger.

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

The test therefore expects `user approval is needed` as the sole failure.

## Current Verification Boundary

GitHub returned no workflow runs and no commit statuses for matching `sandbox` commits, including a commit that changed the workflow itself.

Therefore:

- Runtime implementation: complete for current Wave 1 scope.
- Functional-test definition: complete.
- Canonical real-record conversion: complete for NKS-PUB-000001.
- Filesystem and GitHub adapter contract definitions: complete.
- Executed pytest result: blocked by unavailable CI execution and absence of a local command-execution connector for this repository.

No test pass is claimed until an actual pytest result is observed.

## Next Work After Test Execution Is Available

1. Run `python -m pip install -e ".[test]"`.
2. Run `python -m pytest`.
3. Repair any observed failure.
4. Record the verified result in a test report.
5. Implement generated indexes from canonical records.
6. Add event persistence through the GitHub adapter.
7. Execute a full offline export/import dependency-extraction scenario.
