# Runtime v0.1 Status

## Current State

Wave 1 portable runtime implementation is committed on the `sandbox` branch.

## Implemented

- Python project definition and package entry point.
- Platform-neutral domain records for sources, artifacts, proof, narrative, visuals, publications, and workflow events.
- Repository ports that contain no GitHub or Google dependencies.
- Local filesystem JSON adapter.
- Append-only JSONL event adapter with duplicate-event protection.
- Executable governance validators for source, proof, narrative, visual, editorial, and user-approval gates.
- Application service that persists one complete publication package and evaluates readiness.
- CLI entry point.
- Idempotent end-to-end pytest fixture.
- GitHub Actions workflow that invokes the same pytest test used locally.

## Architectural Boundaries Preserved

- Domain code imports no platform connector libraries.
- Application workflow depends on repository interfaces.
- GitHub Actions contains orchestration only, not business rules.
- Canonical records serialize as JSON.
- Filesystem execution does not require network access.
- Repeated execution does not duplicate records or events.

## Functional Test Scope

The committed test exercises:

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

## Current Verification Boundary

Repository structure and test implementation are verified by readback. The CI workflow has been committed, but a completed workflow result has not yet been observed through the available connector surface in this execution session.

Therefore:

- Implementation status: Complete for Wave 1 code skeleton.
- Functional-test definition: Complete.
- Runtime test result: Pending CI or local pytest execution.

## Next Work

1. Observe and resolve the first pytest run.
2. Add negative gate tests.
3. Convert NKS-PUB-000001 records into canonical JSON.
4. Run the same workflow against those real records.
5. Implement the GitHub repository adapter against the existing ports.
6. Execute the dependency-extraction test offline.
