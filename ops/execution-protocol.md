# Execution Protocol

## Command Semantics

When the user says `execute`, the assistant should:

1. Load current project state.
2. Identify the next incomplete artifact.
3. Create or update the artifact.
4. Verify the write.
5. Update state.
6. Continue to the next incomplete artifact.

The assistant should not stop for summaries, re-explanations, or redundant confirmations.

## Stop Conditions

Execution stops only when:

- the sprint is complete
- a genuine technical blocker occurs
- a decision is required that only the user can make
- external account setup is required
- a safety, legal, or identity-sensitive boundary is reached

## Reporting Cadence

Report only:

- stage completion
- real blockers
- meaningful state changes

Do not report every low-level operation.

## No Silent Failure Rule

If a write, sync, or verification fails, state exactly what failed and why, then continue with non-blocked work where possible.

## Source of Truth Rule

Google Drive is the live working system.
GitHub is the durable architecture repository.
Chat is working memory only.

## Fallback Rule

If Drive or GitHub writes are unavailable, complete the artifacts in chat and queue them for later synchronization.
