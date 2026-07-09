# Integration Evaluation Matrix

## Purpose

Evaluate free/open-source publishing and distribution solutions as replaceable buy-layer modules beneath the NKS contract layer.

## Evaluation Principle

The winning solution is not the one with the prettiest UI. It is the one that can best implement the NKS Publication Contract and Adapter Contract while preserving modularity, security, approval gates, and replaceability.

## Search Scope

- GitHub public repositories.
- GitLab/public web search for comparable projects.
- Free/open-source and self-hostable solutions prioritized.
- Hosted SaaS free tiers considered only as temporary manual fallback, not architecture.

## Candidate Summary

| Rank | Candidate | Repo / Project | License | Self-host | API / Automation | Platforms | NKS Fit | Notes |
|---:|---|---|---|---|---|---|---:|---|
| 1 | TryPost | github.com/trypostit/trypost | AGPL-3.0 | Yes | REST API + MCP | 12 listed | 9.2 | Best fit for AI/agent integration; strong platform coverage; explicit MCP support. |
| 2 | Postiz | github.com/gitroomhq/postiz-app | AGPL-3.0 | Yes | Public API, SDK, N8N/Make/Zapier references | Broad listed platform icons | 8.8 | Strong community signal, API story, automation fit, large repo activity. |
| 3 | BrightBean Studio | github.com/brightbeanxyz/brightbean-studio | AGPL-3.0 | Yes | Django app, self-hostable | Facebook, Instagram, LinkedIn, TikTok, YouTube, Pinterest | 8.0 | Good platform fit and inbox/insights support; no releases yet observed during initial scan. |
| 4 | Mixpost | github.com/inovector/mixpost | MIT | Yes | Laravel/PHP; API needs deeper validation | Cross-platform social scheduler | 7.6 | Strong license advantage, active releases, simpler legal posture. Need confirm platform/API depth. |
| 5 | Socioboard 5.0 | github.com/socioboard/Socioboard-5.0 | License present; needs review | Yes | Needs deeper validation | Social management platform | 5.5 | Legacy/known project; lower current fit pending maintenance/security review. |
| 6 | Buffer Free Tier | buffer.com | Proprietary SaaS free tier | No | Platform APIs hidden behind SaaS | Broad | 4.5 | Useful temporary manual fallback only; not a modular NKS architecture component. |

## Scoring Criteria

| Criterion | Weight |
|---|---:|
| Self-hostable / no subscription dependency | 15 |
| Open-source license compatibility | 15 |
| API / automation support | 20 |
| Platform coverage | 15 |
| Approval / review workflow potential | 10 |
| Adapter simplicity | 10 |
| Maintenance/community signal | 10 |
| Security boundary fit | 5 |

## Candidate Notes

### TryPost

Strengths:
- Self-hostable.
- AGPL-3.0.
- Native publishing to 12 networks.
- REST API and MCP server.
- AI assistant integration is explicitly part of positioning.
- Supports brand profiles, carousels, automations, webhooks, asset library, workspaces, and analytics.

Concerns:
- AGPL obligations must be respected if modified and network-served.
- Requires deployment validation.
- Need inspect API docs before adapter prototype.

Recommended role:
- Primary candidate for Distribution Engine v1.

### Postiz

Strengths:
- Self-hosted social media scheduling.
- Public API and Node SDK references.
- N8N/Make/Zapier integration references.
- Large repo/community signal.
- Broad platform support including LinkedIn, Facebook, Instagram, Pinterest, X, Threads, Mastodon, Bluesky, Discord, Slack, YouTube, TikTok, Reddit.

Concerns:
- AGPL obligations.
- Need validate approval workflow and API payload coverage.
- Need assess deployment weight.

Recommended role:
- Primary alternate / comparative prototype candidate.

### BrightBean Studio

Strengths:
- Open-source/self-hostable social media management.
- Supports publish/comment/DM/insights by platform matrix.
- Includes LinkedIn personal/company, Instagram, Facebook, YouTube, TikTok, Pinterest.
- Django/Python stack may be accessible for adapter work.

Concerns:
- Initial scan showed no releases published.
- Need evaluate maturity and deployment reliability.

Recommended role:
- Strong evaluation candidate; maybe better for dashboard/inbox than first automation path.

### Mixpost

Strengths:
- MIT license.
- Self-hostable.
- Active releases observed.
- Server-side content scheduling and publishing.

Concerns:
- Need validate API automation and platform support in detail.
- Laravel/PHP stack may be less aligned with current NKS tooling unless self-contained.

Recommended role:
- Best license posture; evaluate as low-friction/manual dashboard option.

### Socioboard

Strengths:
- Social management product lineage.
- Self-host oriented.

Concerns:
- Needs deeper maintenance, license, and security review before serious consideration.
- Lower confidence than newer candidates.

Recommended role:
- Reference candidate only unless other tools fail.

## Recommendation

Proceed with a two-track evaluation:

1. TryPost as the primary API/MCP-aligned candidate.
2. Postiz as the primary automation/community candidate.

Do not directly couple NKS to either. Build a first `Publishing Adapter Prototype` that accepts Publication Contract v1 and maps to the selected tool.

## Immediate Next Actions

1. Inspect TryPost API/MCP docs.
2. Inspect Postiz public API docs.
3. Create adapter mapping sheets for both.
4. Select first dry-run target.
5. Build publication contract payload for NKS-PUB-000001.
6. Execute dry-run validation before any external publishing.

## Current Decision

No vendor selected as authoritative. TryPost and Postiz advance to first technical validation.