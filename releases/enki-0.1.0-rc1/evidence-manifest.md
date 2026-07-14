# Enki 0.1.0-rc1 Evidence Manifest

## Candidate identity

- Candidate ID: `ENKI-0.1.0-RC1`
- Version: `0.1.0-rc1`
- Source commit: `cb84fbc8eef6096e8a707e1b922dfa2eddb23e51`
- Execution context: `TEST`
- External effects: `false`

## Implementation evidence

- Implementation PR: https://github.com/nelsonbridge/media-blitz-os/pull/41
- CI: https://github.com/nelsonbridge/media-blitz-os/actions/runs/29336687498
- Runtime Coverage: https://github.com/nelsonbridge/media-blitz-os/actions/runs/29336687640
- Work Control Authority: https://github.com/nelsonbridge/media-blitz-os/actions/runs/29336687647

## Adaptive-loop evidence

- Publication loop receipt hash: `sha256:743c0b5444719a6dbe4757a90a42c21fd1111f47dcd8d786e370f8a9e02c7cfc`
- Nonpublication loop receipt hash: `sha256:f3e82654d0919d71eed399fa387be58def6d67be207a0ffb7cc01e3dbb4b6e35`
- Both loop receipts record `TEST`, `external_effect=false`, `COMMITTED`, and `COMPLETE` reconstruction.

## Required release artifacts

This directory contains the calibration report, threat model, internal TEST runbook, known limitations, rollback package, release notes, human decision request, adaptive-loop receipts, candidate manifest, and this evidence manifest.

All artifact hashes are carried in `release-candidate.json`. The package must be regenerated or rejected if any file changes.

## Authority

This manifest is evidence for an internal release-candidate decision. It is not a release decision and cannot authorize production effects.
