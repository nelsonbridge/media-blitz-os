# Test Coverage Policy

## Purpose

Quantitative coverage complements functional and contract testing. It does not replace proof that workflows behave correctly.

## Required Metrics

The runtime measures:

- statement coverage;
- branch coverage;
- uncovered line locations;
- machine-readable JSON and XML reports.

## Initial Runtime Floor

Runtime v0.1 uses an initial whole-package floor of **70% branch-aware coverage**.

This is a baseline, not the target architecture.

## Target Thresholds

As the runtime matures:

| Package area | Target |
|---|---:|
| Domain models and policies | 90%+ |
| Application services | 85%+ |
| Portable adapters | 80%+ |
| External adapters | Contract tests first; integration coverage added per available environment |

## Rules

1. A passing percentage does not override a failed functional gate.
2. Coverage exclusions require an explicit reason in configuration or code.
3. New domain policy must include positive and negative tests.
4. Adapter error paths must include conflict, permission, timeout, and not-found behavior where applicable.
5. Coverage reports must be reproducible locally without GitHub Actions.
6. GitHub Actions may verify coverage but is not the sole execution surface.
7. Thresholds should rise; they must not be reduced merely to make a build pass.

## Generated Artifacts

A complete run produces:

- terminal missing-line report;
- `coverage.json`;
- `coverage.xml`.

## Release Gate

Runtime changes may not be called coverage-complete unless:

- all functional tests pass;
- the configured whole-package floor passes;
- domain/policy gaps are reviewed against the target thresholds;
- uncovered critical paths are placed in the technical backlog.
