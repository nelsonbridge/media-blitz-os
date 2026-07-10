# Local Run Instructions — Medium Automation POC

## Objective

Publish `NKS-PUB-000001` to Medium without copy/paste using a browser automation path.

## Selected Tool

`patnaikd/publish-to-medium`

This tool uses Playwright to open a Chromium browser, authenticate to Medium, publish a Markdown file as an unlisted Medium post, and print the Medium URL.

## NKS Source File

`publishing/ready/NKS-PUB-000001-published.md`

## Step 1 — Clone POC Tool

```bash
git clone https://github.com/patnaikd/publish-to-medium
cd publish-to-medium
```

## Step 2 — Set Up Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Step 3 — Run First Publish

From inside the cloned `publish-to-medium` repo:

```bash
python3 scripts/publish_to_medium.py /absolute/path/to/media-blitz-os/publishing/ready/NKS-PUB-000001-published.md
```

## Step 4 — Authenticate

On first run, Chromium opens Medium.

Log in with the authorized Medium account.

After login, the browser session is saved locally to:

```bash
~/.publish-to-medium-profile
```

Future runs should reuse this session.

## Step 5 — Capture Output

The script prints the Medium URL after publishing.

Capture the URL and update:

1. `contracts/payloads/NKS-PUB-000001-publication-contract.yaml`
2. `publishing/readiness/NKS-PUB-000001-publication-readiness.md`
3. `publishing/publication-index.md`
4. A new execution snapshot

## Expected Result

An unlisted Medium URL for Publication #1.

## Do Not Commit

Never commit:

- Medium credentials
- browser profile folder
- cookies
- local session files
- `.venv`

## Known Limitations

- The inspected script publishes as unlisted.
- It does not currently set tags.
- It does not currently set canonical URL.
- It does not currently insert generated visual assets.
- It has no license file visible during inspection, so treat it as a POC tool/reference unless license status is resolved.

## Success Criteria

- Medium URL exists.
- NKS publication record is updated with external URL.
- Publication Milestone 1 is marked externally published/unlisted.
- Manual review confirms content formatting is acceptable.