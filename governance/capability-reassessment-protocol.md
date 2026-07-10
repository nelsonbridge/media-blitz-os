# Capability Reassessment Protocol

## Purpose

Prevents the Nelson Knowledge System from treating a temporary, misunderstood, or newly resolved tool limitation as a system blocker.

Connected capabilities can change between sessions. Tool names, function scope, permissions, observability, and execution surfaces must be verified at the point of use.

## Trigger Conditions

Run a capability reassessment when:

1. A task appears blocked by a connector or tool limitation.
2. An empty result is being used to infer nonexistence or failure.
3. A prior session reported that a capability was unavailable.
4. A new plugin or connector may have been added.
5. A major execution wave begins.
6. The runtime needs a capability outside the current critical path.

## Required Sequence

### Step 1 — Define the Exact Required Capability

Describe the smallest required action, such as:

- execute Python tests;
- list workflow runs;
- retrieve job logs;
- write a Drive document;
- generate an image;
- schedule a condition watch;
- publish a platform payload.

Do not use broad labels such as “GitHub unavailable” when only workflow dispatch is missing.

### Step 2 — Inventory Direct Tools

Check direct tools already exposed in the session.

### Step 3 — Reassess Installed Plugins

Search installed plugins and inspect exact function descriptions and limitations.

### Step 4 — Search for Alternate Surfaces

Examples:

- local execution instead of CI;
- filesystem adapter instead of GitHub persistence;
- manual publication package instead of direct API publication;
- queued Drive synchronization instead of stopping corpus work;
- web research instead of relying on stale internal knowledge.

### Step 5 — Test the Narrow Capability

Perform the smallest safe probe that can distinguish:

- available;
- unavailable;
- partially available;
- available but unobservable;
- permission denied;
- network isolated;
- unsupported by the connector contract.

### Step 6 — Reclassify the Blocker

Use one of these classifications:

- No blocker — alternate execution path exists.
- Adapter degradation — queue and continue.
- Observability limitation — execute elsewhere and record result.
- Permission limitation — request only the specific missing permission.
- User decision gate — stop only the gated action.
- True data absence — stop the dependent workflow only.
- Safety/integrity blocker — stop affected work.

### Step 7 — Update State

Update:

- connected ecosystem inventory;
- runtime status;
- technical backlog;
- adapter capability notes;
- Master State if the critical path changed.

## Empty Result Rule

An empty connector response does not establish that no external object exists unless the tool contract states that the query is complete for the requested scope.

Examples:

- A PR-only workflow lookup cannot prove that no push workflow ran.
- A search limited to one page cannot prove complete absence.
- A missing file at an assumed path does not prove the record is absent elsewhere.

## Stop Rule

The system may declare a genuine blocker only after:

1. the exact capability is defined;
2. direct and installed tools are reassessed;
3. alternate surfaces are considered;
4. a narrow probe is performed where safe;
5. the blocker is reduced to the smallest affected action.

## Audit Requirement

When reassessment changes a prior conclusion, correct the authoritative state and state exactly what inference was wrong.