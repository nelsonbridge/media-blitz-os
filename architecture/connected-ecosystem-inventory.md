# Connected Ecosystem Capability Inventory

## Purpose

This document records the currently available execution ecosystem around the Nelson Knowledge System and defines how each capability may be used without becoming a domain dependency.

The inventory must be reassessed periodically because connector and plugin capabilities are not static.

## Governing Rule

Capabilities are classified by role, not by vendor.

The domain core owns models, policies, state machines, and contracts. Connected systems provide execution, storage, communication, synchronization, research, rendering, or publication through adapters.

## Capability Inventory

| Capability Surface | Current Role | Reliability Posture | Canonical Authority | Portable Boundary |
|---|---|---|---|---|
| ChatGPT reasoning/orchestration | Planning, synthesis, workflow execution, policy application | High, session-scoped | No | Application service / orchestration client |
| Local Python execution | Offline runtime verification, data transformation, test execution, export/import validation | High within session | No | CLI and test runner |
| GitHub repository | Current control plane, source control, canonical JSON persistence, contracts, code, audit history | High | Temporary canonical store | Repository adapter |
| GitHub Actions | Optional CI orchestration and hosted execution | Partially observable; not on critical path | No | CI adapter invoking CLI/tests |
| Google Drive | Editorial workspace, document synchronization, human navigation | Intermittent connector availability | No | Document/sync adapter |
| Google Docs | Human-readable editorial views and review surfaces | Intermittent connector availability | No | Document renderer/editor adapter |
| Google Sheets | Dashboards, queues, ledgers, operational views | Intermittent connector availability | No | Tabular view/sync adapter |
| Gmail | Notifications, approval communication, distribution coordination | High when explicitly invoked | No | Notification/messaging adapter |
| Google Calendar | Scheduling, review windows, publication planning | High when explicitly invoked | No | Scheduling adapter |
| Google Contacts | Identity and recipient resolution | High, read-only | No | Directory adapter |
| Automations | Scheduled checks, reminders, recurring summaries, condition watches | High for supported cadence | No | Scheduler/trigger adapter |
| Image generation | Hero images, concept visuals, visual derivatives | Available per explicit generation workflow | No | Visual renderer adapter |
| Web research | Current public verification, citations, standards, external proof | High with source-quality controls | No | Research/evidence adapter |
| Consensus | Academic literature search and synthesis | Available connector | No | Academic evidence adapter |
| Outlook Email | Optional email retrieval/communication surface | Available connector | No | Messaging adapter |
| Outlook Calendar | Optional scheduling surface | Available connector | No | Scheduling adapter |
| OpenAI Platform | API-key and platform setup capability | Available for explicit platform requests | No | Model/provider configuration adapter |
| Medium | Canonical public long-form publication target | External/manual or future adapter | Public canonical URL after release only | Publishing adapter |
| LinkedIn | Executive distribution and professional discovery | External/manual or future adapter | No | Publishing adapter |
| X | Short-form distribution and argument threads | External/manual or future adapter | No | Publishing adapter |
| Facebook | General audience distribution | External/manual or future adapter | No | Publishing adapter |
| Instagram | Carousel and visual distribution | External/manual or future adapter | No | Publishing adapter |
| Pinterest | Evergreen visual discovery | External/manual or future adapter | No | Publishing adapter |

## Capability Classes

### Core Execution

- ChatGPT orchestration
- Local Python runtime
- NKS domain/application code

These capabilities execute the system but do not own canonical domain truth.

### Canonical Persistence

- GitHub repository, temporarily
- Future filesystem/database/object-store adapters

Canonical persistence must remain exportable and replaceable.

### Human Workspace

- Google Drive
- Google Docs
- Google Sheets

These surfaces improve review and usability. They must never become the only location of canonical state.

### Communication and Scheduling

- Gmail
- Outlook Email
- Google Calendar
- Outlook Calendar
- Google Contacts
- Automations

These surfaces notify, coordinate, and schedule. They do not advance publication gates without recorded domain events.

### Evidence and Research

- Web research
- Consensus
- uploaded source files

Evidence adapters may enrich proof records but may not silently overwrite source lineage or proof posture.

### Rendering and Distribution

- Image generation
- Medium
- LinkedIn
- X
- Facebook
- Instagram
- Pinterest

Rendered and published assets are derivatives of canonical packages. External platform metadata must map back to platform-neutral publication and visual IDs.

## Failure Posture

### Connector Unavailable

- Record the integration failure.
- Queue the adapter action.
- Continue domain execution through available adapters.

### Local Execution Available but Network Isolated

- Reconstruct or export canonical state through connector reads.
- Execute tests and transformations offline.
- Persist verified results through the repository adapter.

### CI Unobservable

- Do not infer pass or failure from an incomplete run-list surface.
- Execute the same test suite locally.
- Treat CI as a secondary integration check.

### Publishing Adapter Unavailable

- Complete all internal gates.
- Produce a manual-publication package.
- Preserve platform payload and expected response contract.

## Reassessment Rule

At the start of each major execution wave, and whenever a blocker is declared:

1. Reassess installed plugins and direct tools.
2. Read exact tool limitations rather than inferring from empty results.
3. Check for alternate execution surfaces.
4. Narrow the blocker to the smallest unavailable capability.
5. Update this inventory when the effective capability boundary changes.
