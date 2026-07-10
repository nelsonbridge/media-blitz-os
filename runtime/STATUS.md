# Runtime v0.1 Status

## Current State

Wave 1 portable runtime implementation is committed on the `sandbox` branch.

The internal runtime, canonical record set, policy suite, filesystem adapter, GitHub adapters, generated views, and local verification path are implemented for the current canonical publication set.

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
- GitHub record repository adapter behind a minimal client protocol.
- GitHub append-only event repository using immutable per-event JSON files.
- Concrete GitHub contents client with optimistic concurrency and classified errors.
- Generated Markdown views for publications, proofs, visual packages, and ecosystem capabilities.
- CLI `generate-views` command.
- GitHub Actions workflow configured to run the complete test suite.
- First real manufacturing event persisted for NKS-PUB-000001.

## Architectural Boundaries Preserved

- Domain code imports no platform connector libraries.
- Application workflow depends on repository interfaces.
- GitHub-specific behavior is isolated in adapters.
- Platform version/SHA metadata remains inside the concrete GitHub client.
- GitHub Actions contains orchestration only, not business rules.
- Canonical records serialize as open JSON.
- Filesystem execution does not require network access.
- Repeated execution does not duplicate records or events.
- Generated Markdown is a deterministic view rather than canonical state.

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
- GitHub record-adapter behavior;
- GitHub event idempotence and immutable-ID conflict detection;
- GitHub contents-client create/read/update/list behavior;
- optimistic concurrency conflict classification;
- permission and retryable timeout classification;
- deterministic generated-view output.

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

## Verified Functional Results

### Runtime Core

Observed result:

- Test command: `pytest -q`
- Tests executed: 6
- Tests passed: 6
- Tests failed: 0
- Runtime: 0.14 seconds

### Generated Views

- Deterministic generation verification: passed.
- Tests executed: 1
- Tests passed: 1
- Runtime: 0.13 seconds

### GitHub Event Repository

- Idempotent append and conflict verification: passed.
- Tests executed: 2
- Tests passed: 2
- Runtime: 0.08 seconds

### GitHub Contents Client

- Create/read/update/list, stale-version conflict, permission, and timeout verification: passed.
- Tests executed: 1
- Tests passed: 1
- Runtime: 0.12 seconds

These local isolated runs verify the implemented code paths reconstructed from committed GitHub contents. No hosted GitHub Actions result is claimed.

## Generated View State

Committed generated views:

- `generated/publication-index.md`
- `generated/proof-index.md`
- `generated/visual-package-index.md`
- `generated/ecosystem-capabilities.md`

The generated visual index correctly reports one canonical visual package, replacing the stale operational assumption of zero.

## GitHub Actions Boundary

The current connector surface can inspect known jobs, logs, steps, artifacts, and rerun known jobs, but it does not expose a general workflow-run listing or manual workflow-dispatch action.

GitHub Actions remains an optional secondary integration check, not a blocker to functional verification.

## Revised Next Work

1. Execute the full offline export/import dependency-extraction scenario.
2. Add generated event and runtime-state summaries.
3. Reconcile or retire stale manually maintained indexes after canonical conversion expands beyond NKS-PUB-000001.
4. Implement Drive/Docs/Sheets adapter contracts.
5. Implement the visual renderer adapter for NKS-PUB-000001.
6. Implement the manual publication adapter.
7. Reassess GitHub Actions when general run-list or dispatch capability becomes available.
