# Integration Evaluation Matrix

## Purpose

Evaluate publishing and distribution solutions as replaceable modules beneath the NKS-owned Publication Contract and Adapter Contract.

## Evaluation Principle

The winning solution is not the one with the broadest marketing claim. It is the one that best implements the NKS contracts while preserving approval, proof boundaries, auditability, security, failure recovery, and replaceability.

## Revalidation Date

2026-07-10

## Current Decision Summary

| Use Case | Selected Path | Status |
|---|---|---|
| Universal release fallback | Manual Publication Adapter | Production-safe default |
| First social-distribution trial | TryPost | Technical validation candidate |
| Social comparison/fallback | Postiz | Secondary validation candidate |
| Medium release | Manual-first | Production-safe default |
| Medium automation | patnaikd/publish-to-medium | Controlled local POC only |

Full rationale: `integrations/direct-publication-adapter-decision.md`.

## Medium Candidate

### patnaikd/publish-to-medium

Current strengths:

- Active repository.
- Local Playwright browser automation.
- Persistent local Medium session.
- Markdown-to-HTML conversion.
- Recent file-to-post mapping and republish/update support.

Current risks:

- No confirmed license identified during evaluation.
- Repository documents fragile Medium selectors.
- Unlisted visibility may fail and fall back to default visibility.
- Update-button behavior has not been verified in a live Medium session.
- Browser automation depends on Medium UI behavior rather than an official stable API.

Decision:

**POC only.** It may be used for a controlled local test after explicit user approval. It is not the production-default adapter and its code may not be copied into NKS until licensing is clarified.

## Social Distribution Candidates

| Rank | Candidate | License | Self-host | Programmatic Surface | Required Platforms | Current Fit |
|---:|---|---|---|---|---|---:|
| 1 | TryPost | AGPL-3.0 confirmed | Yes | REST API + MCP | LinkedIn, X, Instagram, Facebook, Pinterest | 9.3 |
| 2 | Postiz | AGPL-3.0 confirmed | Yes | Public API, Node SDK, N8N, Make | LinkedIn, X, Instagram, Facebook, Pinterest | 9.0 |
| 3 | Mixpost | MIT previously recorded | Yes | Requires deeper API validation | Social scheduling | 7.4 |
| 4 | BrightBean Studio | AGPL-3.0 previously recorded | Yes | Requires deeper API validation | Required visual/social channels | 7.2 |
| 5 | Buffer Free Tier | Proprietary SaaS | No | Vendor-managed | Broad | 4.5 |

## TryPost Verification

Verified from the current repository:

- AGPL-3.0 license in `LICENSE.md`.
- Active development.
- README documents self-hosted and hosted deployment.
- README documents a first-class REST API and MCP server.
- README documents native publishing through official APIs to twelve platforms.
- README lists the five required derivative channels.
- README documents workspaces, roles, approval flows, comments, analytics, assets, and automation.

Remaining validation:

- exact request and response schema;
- approval-rejection behavior;
- credentials and minimum scopes;
- external IDs and public URL receipts;
- duplicate/idempotency behavior;
- retryable versus terminal failures;
- live controlled test workspace.

## Postiz Verification

Verified from the current repository:

- AGPL-3.0 license in `LICENSE`.
- Active development, including current platform-provider work.
- README documents self-hosting and hosted service.
- README links a public API and Node SDK.
- README documents N8N and Make integrations.
- README lists all five required derivative channels plus additional platforms.
- README states official OAuth/platform flows for the hosted service.

Remaining validation:

- exact public API schema;
- self-hosted API parity;
- approval handling;
- external IDs, URLs, and analytics receipts;
- idempotency and retry semantics;
- credential storage and log redaction;
- live controlled test workspace.

## NKS Contract Requirements

Every candidate must pass the same adapter tests:

1. Reject dispatch when `approval.approved` is false.
2. Validate source, proof, narrative, and visual fields.
3. Preserve the approved body and visual IDs.
4. Map channel/account targets without changing canonical IDs.
5. Support dry-run behavior.
6. Return a structured success or failure result.
7. Capture external IDs, URLs, and timestamps.
8. Classify retryable and terminal failures.
9. Avoid secret exposure in records and logs.
10. Prevent duplicate dispatch through an idempotency key.
11. Queue manual fallback when external dispatch fails.

## Security Boundary

- User approval is authoritative in NKS, not in the vendor system.
- Tokens, OAuth secrets, cookies, and browser profiles remain outside canonical records.
- Credentials are environment or local-runner references.
- Minimum practical scopes are required.
- Logs must redact secrets.
- External systems may not modify proof, narrative, visual, or approval state.

## Current Execution Sequence

1. Implement a vendor-neutral social adapter port.
2. Create a publication derivative fixture.
3. Add contract tests for approval, validation, idempotency, receipts, failures, and secret-free logs.
4. Map the neutral contract to TryPost.
5. Execute a dry-run and controlled test.
6. Validate Postiz against the same contract if TryPost fails or as a comparison.
7. Retain the manual adapter throughout.

## Final Decision

- **Manual Adapter:** current production-safe release path.
- **TryPost:** first social-distribution technical trial.
- **Postiz:** second candidate and fallback comparison.
- **publish-to-medium:** controlled local Medium POC only.
