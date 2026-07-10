# Dependency Extraction Test Report — 2026-07-10

## Purpose

Verify that canonical Nelson Knowledge System state can leave GitHub and operate as a portable offline bundle without changing domain identifiers or depending on platform metadata.

## Implemented Capability

The runtime now exports:

- canonical records;
- schemas;
- contracts;
- a deterministic manifest;
- per-file SHA-256 checksums;
- file sizes and portable relative paths.

The runtime imports the bundle into a clean filesystem store and verifies every file against its manifest checksum.

## Security and Integrity Controls

- Absolute archive paths are rejected.
- Parent-directory traversal paths are rejected.
- Non-empty destinations require an explicit replace option.
- Tampered content fails checksum validation.
- GitHub SHAs, repository IDs, and proprietary platform identifiers are not required in the portable manifest.

## CLI Commands

```text
nks export-state <repository-root> <archive-path>
nks import-state <archive-path> <destination-root>
```

The import command performs post-import verification before reporting success.

## Local Verification

Observed result:

```text
3 passed in 0.10 seconds
```

Verified scenarios:

1. Records, schemas, and contracts survive an export/import round trip.
2. A non-empty destination is protected unless replacement is explicit.
3. Tampered archive content is rejected.

## Architectural Result

PASS — dependency extraction capability.

The NKS canonical state can be packaged and restored without GitHub connectivity. GitHub remains the current persistence adapter, not a required runtime identity.

## Remaining Expansion

- Run the export against the complete repository canonical set.
- Add workflow-event export summaries.
- Add generated-view regeneration after import.
- Add migration mapping for a future database adapter.
