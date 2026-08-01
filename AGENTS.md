# AGENTS.md

## Purpose

This repository is a governed Python runtime for the Nelson Knowledge System. Treat repository state as an authority-managed system, not a conventional docs-heavy project.

## Read First

1. [docs/state-authority-model.md](docs/state-authority-model.md)
2. [docs/canonicalization-security-boundary.md](docs/canonicalization-security-boundary.md)
3. [docs/execution-protocol.md](docs/execution-protocol.md)
4. [README.md](README.md)

Use [architecture/enki/enki-canonical-nine-layer-architecture.md](architecture/enki/enki-canonical-nine-layer-architecture.md) and [architecture/adr/](architecture/adr/) when a task depends on architecture intent or boundary placement.

## Operating Rules

- Class 1 canonical records are the source of truth. Do not infer operational state from narrative Markdown when canonical or generated state exists.
- Files under `generated/` are Class 2 deterministic projections. Do not edit them manually. Change canonical inputs or generators, then regenerate.
- Class 3 documents explain or plan work but are not authoritative unless the repository explicitly marks them otherwise.
- Any canonical write path must preserve provenance, authority, and append-only audit semantics. Route behavior through the governed runtime instead of adding direct adapter-side mutations.
- Keep changes minimal and local. Do not rewrite unrelated status, backlog, or narrative files to make them match code.

## Code Map

- `src/nks/domain/`: domain models and state contracts.
- `src/nks/enki/`: authority, retrieval, contracts, versioning, and model gateway logic.
- `src/nks/governance/`: approvals, boundaries, capabilities, entitlements.
- `src/nks/adapters/`: filesystem, GitHub, social, and governed persistence adapters.
- `src/nks/application/`: orchestration, manifests, and sprint-scoped application paths.
- `src/nks/views/`: deterministic projection generation and authority verification.
- `tests/`: repo-wide pytest suite, including authority, governance, manifest, and sprint coverage.

## Working Conventions

- Prefer changing canonical logic, validators, or generators at the owning layer instead of patching generated outputs or narrative summaries.
- When a task touches authority, projections, records, or manifests, check whether [generated/state-authority-manifest.json](generated/state-authority-manifest.json) and [tests/test_state_authority.py](tests/test_state_authority.py) are part of the controlling surface.
- If a task involves provenance, promotion, or source creation, inspect [src/nks/adapters/canonicalization.py](src/nks/adapters/canonicalization.py), [src/nks/validation/enki_records.py](src/nks/validation/enki_records.py), and related tests before editing.
- If a task involves temporal or current authority, start with [src/nks/enki/temporal_authority.py](src/nks/enki/temporal_authority.py), [src/nks/enki/governed_retrieval.py](src/nks/enki/governed_retrieval.py), and their sprint tests.
- Many application modules are sprint-scoped. Preserve existing sprint numbering and path-manifest patterns rather than inventing new naming schemes.

## Setup And Validation

- Python: `>=3.11`
- Install dev dependencies: `python -m pip install -e ".[test]"`
- Run tests: `python -m pytest`
- Regenerate standard projections: `nks generate-views .`
- Verify state authority and generated outputs: `python -m nks.views.authority verify .`

After changing logic that affects generated views or authority rules, run the smallest relevant pytest slice first, then rerun the projection or authority command if the touched code participates in those flows.

## Common Pitfalls

- Do not treat manually maintained status files as implementation truth.
- Do not add direct writes that bypass governed approval, entitlement, provenance, or receipt logic.
- Do not check in edited generated files without the corresponding canonical or generator change.
- Do not assume hosted services are required; core behavior is designed to remain portable and offline-friendly.
