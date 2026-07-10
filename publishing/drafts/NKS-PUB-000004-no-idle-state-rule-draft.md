# The No Idle State Rule

## Subtitle

If useful work remains, the system should not wait to be told to continue.

## Draft

Most execution failures do not begin as technical failures.

They begin as state failures.

The system forgets what was approved. It loses track of what has already been completed. It waits for confirmation even when the next task is obvious. It summarizes progress instead of continuing progress. It treats every step like a new conversation rather than part of an ongoing operating process.

That behavior is tolerable in casual assistance.

It is unacceptable in execution systems.

That is why the No Idle State Rule exists.

## The Rule

If executable work remains anywhere in the approved backlog, the system must not become idle.

It must continuously select the highest-priority unblocked task, execute it, verify the result, update project state, and continue until the current sprint is complete or a genuine blocker exists.

That rule changes the operating mode.

The assistant is no longer waiting for the next instruction after every small action.

It is executing against an approved state model.

## The Conversational Trap

Most assistants are optimized for interaction.

They answer, explain, ask, clarify, summarize, and wait.

That works when the goal is understanding.

It fails when the goal is execution.

Once execution has been authorized, the assistant should not repeatedly return to conversational posture unless something truly requires the user's judgment.

If the next work item is known, the next move is not to explain the plan again.

The next move is to perform the work.

## Execution Requires State

The No Idle State Rule only works if the system has state.

It must know:

- what sprint is active,
- what artifacts already exist,
- what has been verified,
- what remains pending,
- what is blocked,
- what can be worked around,
- and what requires user approval.

Without that, continuous execution becomes reckless.

With state, continuous execution becomes disciplined.

## Stop Conditions

The rule does not mean the system never stops.

It means the system stops only for valid reasons.

Valid stop conditions include:

- the sprint is complete,
- a genuine technical blocker exists,
- a required external dependency is unavailable,
- a decision is required that only the user can make,
- or public release requires approval.

Everything else should be worked around.

If Drive is unavailable, write to GitHub.

If a full source cannot be accessed, process available sources.

If public release is blocked, create the publication package.

If a draft is not final, create the review checklist.

The system should keep moving until movement would become dishonest, unsafe, destructive, or dependent on a user-owned decision.

## Why This Matters

The No Idle State Rule prevents a common pattern: artificial stoppage.

Artificial stoppage happens when work stops even though nothing real is blocking it.

It shows up as over-explaining, repeated planning, unnecessary confirmation, tool rediscovery, and premature summaries.

Those behaviors feel helpful in a chat interface.

They are waste inside an operating system.

## The Operating Principle

If the next task is known, execute it.

If execution succeeds, verify it.

If verification succeeds, update state.

If state is updated, select the next unblocked task.

Then continue.

That loop is simple, but it is powerful.

It converts approval into momentum.

It converts conversation into production.

It converts an assistant into an operating partner.

## Draft Status

Internal draft. Requires editorial review before public publication.
