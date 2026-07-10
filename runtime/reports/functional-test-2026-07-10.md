# Runtime Functional Test Report — 2026-07-10

## Scope

Verified the Nelson Knowledge System Runtime v0.1 core using local isolated Python execution reconstructed from committed GitHub contents.

## Why Local Execution Was Used

The GitHub connector exposes job/log inspection for known Actions runs but its commit-run lookup is limited to pull-request-triggered runs. It does not expose general run listing or workflow dispatch in the current surface.

Local Python execution was available and therefore used as the primary functional verification surface. GitHub remained the persistence and audit surface.

## Test Command

```text
pytest -q
```

## Observed Result

```text
6 passed in 0.14 seconds
```

## Verified Behaviors

- Platform-neutral domain model construction.
- Filesystem JSON persistence.
- Idempotent repeated workflow execution.
- Duplicate event prevention.
- Source-lineage gate failure.
- Narrative completeness gate failure.
- Signature-diagram requirement.
- User-approval requirement.
- GitHub record-adapter contract through a fake client.

## Architectural Conclusion

The functional core does not require GitHub Actions or Google Drive to execute.

GitHub currently provides canonical persistence and source control. Local execution provides runtime verification. Both remain replaceable through adapters and CLI/test contracts.

## Limitations

- Direct repository cloning was unavailable because the local runtime is network isolated.
- The test environment was reconstructed from verified GitHub file contents.
- A complete hosted GitHub Actions run was not observed through the current connector surface.
- External Drive, image-generation, and publication adapters were outside this functional test.

## Result

PASS — Runtime v0.1 functional core.

This result does not constitute public-publication approval for NKS-PUB-000001. Its canonical readiness record correctly retains user approval as pending.