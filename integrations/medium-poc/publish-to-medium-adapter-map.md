# Medium POC Adapter Map — publish-to-medium

## Purpose

Map the NKS Publication Contract for NKS-PUB-000001 to the `patnaikd/publish-to-medium` Playwright automation path.

## Selected POC Tool

Repository: `patnaikd/publish-to-medium`

Why selected:

- Direct Medium publishing automation.
- No Medium API token required.
- Uses browser automation through Playwright.
- First run authenticates through Medium in Chromium.
- Session is saved locally for future runs.
- Accepts local Markdown file path.
- Returns Medium post URL.

## NKS Input

Publication Contract:

`contracts/payloads/NKS-PUB-000001-publication-contract.yaml`

Medium-ready Markdown:

`publishing/medium-ready/NKS-PUB-000001-medium-ready.md`

## Field Mapping

| NKS Field | publish-to-medium Handling |
|---|---|
| `publication.title` | First H1 in Markdown. |
| `publication.body_markdown_path` | CLI file argument. |
| `publication.tags` | Not currently handled by inspected script. Manual/additional adapter extension required. |
| `publication.canonical_url` | Not currently handled by inspected script. Adapter extension required if canonical URL is needed. |
| `approval.approved` | Must be checked by NKS before running script. |
| `visuals.*` | Not handled by inspected script. Visuals are separate Medium editor insertion work unless adapter is extended. |
| `distribution.adapter_target` | `publish-to-medium-playwright`. |

## Execution Mode

Initial POC should publish as **unlisted**.

The inspected script explicitly publishes Medium posts as unlisted.

## Local Runner Requirements

- Python 3.
- `venv`.
- Playwright.
- Chromium installed by Playwright.
- Medium login completed in first browser session.

## POC Command Pattern

```bash
git clone https://github.com/patnaikd/publish-to-medium
cd publish-to-medium
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python3 scripts/publish_to_medium.py /path/to/NKS-PUB-000001-medium-ready.md
```

## Output Capture

The script prints the Medium URL after publishing. That URL must be copied into:

- `publishing/readiness/NKS-PUB-000001-publication-readiness.md`
- `contracts/payloads/NKS-PUB-000001-publication-contract.yaml`
- `publishing/publication-index.md`
- Master State / execution snapshot

## Security Boundary

- Medium credentials are never stored in GitHub.
- Saved session profile remains local at `~/.publish-to-medium-profile`.
- Do not commit browser profile data.
- Do not run publish unless user approval is recorded.

## Known Gaps

1. No license file found in inspected repository.
2. Script does not appear to set tags.
3. Script does not appear to set canonical URL.
4. Script does not appear to insert images or SVGs.
5. Script publishes unlisted by design.

## Recommendation

Use this tool for the first automated Medium POC because it tests the true missing endpoint: Medium publication without copy/paste or API tokens.

After POC succeeds, either:

1. Extend a local adapter around the script, or
2. Build a clean NKS-owned Playwright adapter using the same pattern.