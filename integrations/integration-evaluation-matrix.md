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

## Current Medium POC Decision

For Publication Milestone 1, the immediate Medium automation POC candidate is:

**patnaikd/publish-to-medium**

Reason:

- It publishes local Markdown files to Medium using Playwright browser automation.
- It does not require a Medium API token.
- First run opens Chromium and requires manual login.
- After login, it saves the Medium browser session to `~/.publish-to-medium-profile`.
- Future runs can publish automatically using that saved session.
- It extracts the title from the first H1 heading.
- It converts Markdown to HTML.
- It publishes as an unlisted Medium post and returns the Medium URL.

Known limitation:

- No LICENSE file was found during inspection, so licensing must be clarified before copying or modifying code. For POC testing, treat the repository as an external reference/tool until license status is resolved.

## Medium Automation Candidate Summary

| Rank | Candidate | Repo / Project | License | Automation Type | Medium API Token Required | Fit | Notes |
|---:|---|---|---|---|---|---:|---|
| 1 | publish-to-medium | github.com/patnaikd/publish-to-medium | Not found | Playwright browser automation | No | 9.0 | Best immediate POC path for NKS-PUB-000001. |
| 2 | medium-publishing-without-api | github.com/iancarson/medium-publishing-without-api | MIT | Documentation / option analysis | No | 7.0 | Useful decision support; points to session-based publishing options. |
| 3 | aiagent-mcp-medium-publisher | github.com/umes4ever/aiagent-mcp-medium-publisher | MIT | Docker + MCP framing | Unknown / needs deeper inspection | 6.5 | Interesting future MCP candidate, but less direct than Playwright script. |
| 4 | content-distribution-mcp | github.com/AutomateLab-tech/content-distribution-mcp | MIT | MCP distribution layer | No direct Medium automation | 6.0 | Useful later; Medium channel returns browser fallback rather than full publish automation. |

## Broader Distribution Candidate Summary

| Rank | Candidate | Repo / Project | License | Self-host | API / Automation | Platforms | NKS Fit | Notes |
|---:|---|---|---|---|---|---|---:|---|
| 1 | TryPost | github.com/trypostit/trypost | AGPL-3.0 | Yes | REST API + MCP | 12 listed | 9.2 | Best fit for AI/agent integration; strong platform coverage; explicit MCP support. |
| 2 | Postiz | github.com/gitroomhq/postiz-app | AGPL-3.0 | Yes | Public API, SDK, N8N/Make/Zapier references | Broad listed platform icons | 8.8 | Strong community signal, API story, automation fit, large repo activity. |
| 3 | BrightBean Studio | github.com/brightbeanxyz/brightbean-studio | AGPL-3.0 | Yes | Django app, self-hostable | Facebook, Instagram, LinkedIn, TikTok, YouTube, Pinterest | 8.0 | Good platform fit and inbox/insights support; no releases yet observed during initial scan. |
| 4 | Mixpost | github.com/inovector/mixpost | MIT | Yes | Laravel/PHP; API needs deeper validation | Cross-platform social scheduler | 7.6 | Strong license advantage, active releases, simpler legal posture. Need confirm platform/API depth. |
| 5 | Socioboard 5.0 | github.com/socioboard/Socioboard-5.0 | License present; needs review | Yes | Needs deeper validation | Social management platform | 5.5 | Legacy/known project; lower current fit pending maintenance/security review. |
| 6 | Buffer Free Tier | buffer.com | Proprietary SaaS free tier | No | Platform APIs hidden behind SaaS | Broad | 4.5 | Useful temporary manual fallback only; not a modular NKS architecture component. |

## POC Flow for NKS-PUB-000001

```text
NKS Publication Contract
    ↓
Clean Medium Markdown file
    ↓
patnaikd/publish-to-medium Playwright script
    ↓
Medium authenticated browser session
    ↓
Unlisted Medium post URL
    ↓
NKS publication record update
```

## POC Requirements

1. Create clean Medium-ready Markdown for NKS-PUB-000001.
2. Set up local Python virtual environment.
3. Install requirements from `patnaikd/publish-to-medium`.
4. Install Playwright Chromium.
5. Run first publish command locally.
6. Complete Medium login in the opened Chromium window.
7. Capture returned Medium URL.
8. Update NKS publication record with the URL.

## Security Boundary

- Medium credentials must not be committed to GitHub.
- Saved session profile remains local to the runner at `~/.publish-to-medium-profile`.
- Publication requires user approval before live/public publish.
- For first milestone, unlisted publish is acceptable as a controlled proof-of-concept.

## Immediate Next Actions

1. Create clean Medium-ready Markdown from NKS-PUB-000001.
2. Create adapter mapping note for `publish-to-medium`.
3. Create local-run instructions for the Medium POC.
4. Execute on a local machine with Medium login available.
5. Capture Medium URL and update NKS state.

## Current Decision

For Publication Milestone 1, use `patnaikd/publish-to-medium` as the immediate Medium automation POC path, with TryPost/Postiz remaining broader downstream distribution candidates.