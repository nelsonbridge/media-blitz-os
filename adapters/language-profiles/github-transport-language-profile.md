# GitHub Transport Language Profile

## Profile ID

NKS-TLP-GITHUB-000001

## Target Surface

GitHub repository writes, commit messages, file names, summaries, and execution notes.

## Purpose

Reduce connector friction while preserving canonical NKS meaning.

## Canonical Policy

- Preserve meaning: yes.
- Preserve source lineage: yes.
- Preserve proof boundary: yes.
- Preserve graph identity: yes.
- Preserve capability intent: yes.

## Preferred Transport Terms

| Canonical Intent | Preferred GitHub Transport Label | Applies To |
|---|---|---|
| Systems with decision participation | AI-assisted workflow | Filenames, headings, summaries |
| Operational execution support | operational workflow | Filenames, summaries |
| External tool interface | interface layer | Filenames, summaries, commit messages |
| Boundary and approval model | governance boundary | Headings, summaries |
| Controlled outside-facing trial | bounded test | Summaries, readiness records |
| Learning return path | feedback capture | Summaries, registers |
| Execution module | connector profile | Filenames, headings |
| Vendor-neutral interface | contract surface | Architecture records |
| Capability-first ranking | adaptive prioritization | Metrics and operations records |

## Avoid in GitHub Transport Payloads

The following patterns should be avoided in GitHub-facing payloads when they appear together or near operational wording:

| Pattern Type | Safer Replacement |
|---|---|
| High-agency system wording | AI-assisted workflow |
| Sensitive operational wording | operational governance |
| Tool-permission wording | interface boundary |
| Production-change wording | change review boundary |
| Incident-response wording | exception handling |
| External-publishing urgency wording | bounded test |
| Broad connector-control wording | connector profile |

## Review Rules

1. Use canonical terms in internal semantic records only when necessary.
2. Use transport labels in filenames, commit messages, and summaries.
3. Split large payloads if several sensitive patterns appear together.
4. Prefer governance, interface, review, boundary, and profile language for GitHub writes.
5. Preserve canonical IDs even if the visible label changes.
6. If a write is blocked, create a narrower record rather than weakening the canonical model.

## Example

```yaml
canonical_concept: external execution module
transport_label: connector profile
preserved_meaning: replaceable surface-specific implementation path
applies_to:
  - filename
  - commit_message
  - summary
```

## Status

Active profile v1.