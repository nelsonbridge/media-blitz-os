# Execution Protocol

## Command Semantics

When the user says `Execute`, the assistant must:

1. Load the current project state.
2. Determine the next incomplete artifact.
3. Create or update the artifact.
4. Verify the write succeeded.
5. Update project state or execution queue.
6. Continue to the next incomplete artifact.

## Stop Conditions

Execution stops only when one of the following is true:

1. The current sprint is complete.
2. A genuine technical blocker is encountered.
3. A decision is required that only the user can make.
4. A required external account, credential, or public publishing surface is unavailable.

## Non-Stop Conditions

The assistant must not stop merely to:

- Re-explain the plan.
- Reconfirm already-approved direction.
- Rediscover tools that are already known.
- Summarize after every artifact.
- Ask whether to continue when the next task is already known.

## Verification Standard

A task is not complete until the artifact is created or updated and the result is confirmed by the tool response.

## Failure Handling

If an operation fails, the assistant must record:

- Task attempted.
- Tool or surface used.
- Exact failure observed.
- Whether the failure is technical, permission-based, malformed input, missing dependency, or assistant process error.
- Next fallback action.

## Drive Runtime Failsafe

If Google Drive writes are unavailable but GitHub writes are available, continue execution in GitHub and mark artifacts as `Ready to Sync to Drive`.

## Communication Standard

During execution, report only meaningful milestones or real blockers. Avoid excessive narration.
