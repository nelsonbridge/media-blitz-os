# Enki 0.1.0-rc1 Threat Model

## Protected assets

- canonical observations, relationships, findings, transitions, and interpretations;
- approval grants and their reservation or consumption state;
- governed transaction journals and terminal receipts;
- feedback provenance, content hashes, and disposition records;
- release evidence, candidate hashes, and human release authority;
- the boundary separating TEST from PRODUCTION effects.

## Principal threats and controls

| Threat | Primary controls |
|---|---|
| TEST authority used for production | Context-bound approval evaluation, TEST-only plans, no-effect adapters, production capability absence |
| External publication or model dispatch during tests | No transport, credentials, endpoints, callbacks, or provider references in TEST adapters |
| Replay with changed content | Exact plan, subject, content, context, approval, and transaction hashes |
| Duplicate effects after interruption | Idempotent adapters, approval consumption lineage, exact-retry recovery, immutable terminal receipts |
| Feedback provenance laundering | Explicit provenance enums, content hashing, replay origin, deduplication, immutable disposition |
| Audience widening | Purpose, subject, channel, and context binding; no audience capability in TEST |
| Self-issued release approval | Human decision request contract prohibits a system-supplied decision |
| Evidence or candidate tampering | Hash-bound artifacts, candidate manifest, deterministic reconstruction, generated-view drift checks |
| Partial authority or state | Journaled operation boundaries, rollback before consumption, recovery after consumption |
| Conflicting immutable records | Append-only persistence and conflict rejection |

## Trust boundaries

1. Human governing authority.
2. Enki canonical and transaction core.
3. TEST-only adapters.
4. Separately constructed PRODUCTION adapters.
5. Downstream products and external systems.

Crossing from one boundary to another requires explicit, exact authority. The Sprint 13 candidate crosses none of the external-effect boundaries.

## Residual risk

- The internal proof cannot demonstrate third-party platform behavior, provider outages, or real audience response.
- A future production adapter can introduce implementation-specific risk and requires its own threat model and authorization.
- Human review remains necessary for release, public identity, consent, privacy, and external publication decisions.
- Repository and CI compromise remain supply-chain risks outside the application contracts.

## Security decision

The candidate is suitable for a human release decision as an internal TEST release candidate. It is not evidence of production authorization.
