# Direct Publication Adapter Decision

## Decision Date

2026-07-10

## Decision

The Nelson Knowledge System will use a layered publication strategy:

1. **Manual Publication Adapter** — production-safe default and universal fallback.
2. **TryPost Adapter Trial** — first broader social-distribution technical validation.
3. **Postiz Adapter Comparison** — second social-distribution validation and fallback candidate.
4. **publish-to-medium Browser POC** — controlled Medium proof-of-concept only; not production-approved.

No adapter may publish until the NKS Publication Contract records explicit user approval.

## Why Manual Publication Remains the Default

The manual adapter already satisfies the stable NKS contract boundary:

- it consumes an approved publication package;
- preserves the approved body and visual IDs;
- produces a platform-specific checklist and payload;
- records the resulting public URL and receipt;
- works when no API or connector is available;
- does not require credentials in canonical records.

Manual publication is therefore an implementation, not an architectural failure.

## TryPost — First Social Adapter Trial

### Verified posture

- Active public repository.
- AGPL-3.0 license confirmed in `LICENSE.md`.
- Self-hosted and hosted deployment options.
- README documents a first-class REST API and MCP server.
- README documents native publication through official APIs to twelve networks.
- Includes workspaces, roles, approval flows, comments, analytics, assets, and automation.
- Required NKS derivative channels listed: LinkedIn, X, Instagram, Facebook, and Pinterest.

### NKS fit

TryPost is the strongest first trial for broad derivative distribution because it most closely matches the Adapter Contract:

- programmatic dispatch through REST or MCP;
- multi-channel scheduling;
- approval-oriented workflow support;
- external IDs and analytics suitable for receipt and feedback mapping;
- self-hosting and data-control options.

### Constraints

- AGPL obligations must be respected if a modified network service is operated.
- Credentials and platform tokens remain external to canonical NKS records.
- Medium is not among the documented supported platforms.
- Platform connection and API-scope behavior require a live validation environment.
- NKS approval remains authoritative even when TryPost also provides approval features.

### Trial result required

The adapter is not production-approved until it passes:

1. dry-run payload mapping;
2. approval rejection test;
3. one test workspace connection;
4. one private or controlled scheduled derivative;
5. structured receipt capture;
6. duplicate/idempotency test;
7. retry and manual-fallback test;
8. credential and log review.

## Postiz — Second Social Adapter Candidate

### Verified posture

- Active public repository with current platform-provider development.
- AGPL-3.0 license confirmed in `LICENSE`.
- Self-hostable and hosted options.
- Public API, Node SDK, N8N node, and Make integration documented.
- Broad platform support includes LinkedIn, X, Instagram, Facebook, Pinterest, Threads, Bluesky, Mastodon, and others.
- README states official OAuth/platform flows for its hosted service.

### NKS fit

Postiz is a mature comparison candidate with strong API and automation surfaces. It should be validated after TryPost or used if TryPost fails the NKS contract tests.

### Constraints

- AGPL obligations apply to modified network-service deployments.
- Its broader application model is heavier than the minimal NKS adapter requirement.
- Live API behavior, self-hosted parity, idempotency, receipts, and error structure must be validated.
- Medium is not a documented native platform.

## publish-to-medium — POC Only

### Verified posture

- Active repository.
- Uses Playwright with a persistent local Medium browser profile.
- Converts Markdown to HTML and publishes through the Medium editor.
- Recent work added local file-to-post mappings and republish/update behavior.

### Disqualifying production risks

- No confirmed license was identified in the evaluated repository.
- The project itself documents fragile Medium selectors.
- Unlisted visibility selection may fail and fall back to default visibility.
- Update-button behavior is not verified against a live Medium session.
- Browser UI automation is inherently more brittle than an official API adapter.

### Permitted use

- Controlled local proof-of-concept only.
- Explicit user approval required immediately before execution.
- First result must be unlisted or otherwise controlled.
- The user must complete Medium authentication locally.
- No source code may be copied or modified into NKS until licensing is clarified.
- Failure must fall back to the manual adapter.

## Contract Mapping

| NKS Contract Field | TryPost / Postiz Mapping | Medium Browser POC | Manual Adapter |
|---|---|---|---|
| `package_id` | Idempotency key / external metadata | Local mapping record | Checklist and receipt ID |
| `approval.approved` | Must be checked before API dispatch | Must be checked before browser launch | Must be checked before checklist release |
| `publication.title` | Platform post/article title where supported | First Markdown H1 | Copy field |
| `publication.body_markdown` | Transformed to channel body | Converted to HTML | Copy-ready body |
| `visuals.*` | Uploaded media IDs | Medium editor upload step | File checklist |
| `distribution.channels` | Connected provider/account IDs | Medium only | Human-selected targets |
| `distribution.schedule` | API scheduling fields | Immediate/controlled publish | Human schedule |
| `audit` | External ID, URL, status, timestamps | URL and local mapping | Receipt record |

## Security Boundary

- Tokens, cookies, OAuth secrets, and browser profiles never enter canonical publication records.
- Credentials are environment or local-runner references.
- Adapter logs must redact credentials and session data.
- Minimum practical platform scopes are required.
- No adapter may mutate proof, narrative, visual, or approval state.

## Final Selection

### Current production-safe release path

**Manual Publication Adapter**

### First technical social-distribution validation

**TryPost**

### Comparison/fallback validation

**Postiz**

### Medium automation

**Manual-first, with `patnaikd/publish-to-medium` permitted only as a controlled local POC after explicit approval.**

## Next Executable Work

1. Create a vendor-neutral social adapter payload fixture from NKS-PUB-000001 derivatives.
2. Add contract tests for approval, idempotency, structured receipts, failure classification, and secret-free logs.
3. Implement a generic HTTP social adapter port before any TryPost/Postiz-specific client.
4. Validate TryPost in dry-run mode.
5. Validate Postiz against the same tests if required.
6. Keep manual publication available throughout.
