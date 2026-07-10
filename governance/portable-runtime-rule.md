# Portable Runtime Rule

## Decision

GitHub may host the Nelson Knowledge System runtime temporarily, but no platform may become the domain architecture.

The runtime must remain portable and modular.

## Mandatory Boundaries

1. Domain models and policies must not import platform-specific libraries.
2. GitHub, Google Drive, image generation, and publishing platforms must be accessed through explicit interfaces and adapters.
3. GitHub Actions may invoke workflows but may not contain business rules.
4. Canonical state must use open, exportable formats and platform-neutral identifiers.
5. Markdown documents are human-readable views; machine-readable records become the executable source of state.
6. External failures must be isolated, classified, queued, and retried without corrupting domain state.
7. A local filesystem adapter must exist before GitHub is accepted as a completed runtime adapter.
8. Every major runtime release must pass a dependency-extraction test without GitHub, Drive, or publication-platform access.

## Architectural Test

A design fails this rule when removing GitHub or any connector would require rewriting domain logic, governance validators, workflow state machines, or canonical records.

A design passes when the same application workflow can run through CLI, tests, GitHub Actions, or a future API by selecting different adapters.

## Release Guardrail

Runtime v0.1 is not architecturally complete until:

- domain/application/integration package boundaries exist;
- machine-readable canonical schemas exist;
- repository interfaces exist;
- a local filesystem adapter exists;
- the GitHub adapter implements the same contracts;
- governance gates execute as code;
- the functional test passes through both adapters;
- the dependency-extraction test passes offline.

## Backlog Authority

Implementation and acceptance criteria are maintained in `docs/technical-backlog.md`.
