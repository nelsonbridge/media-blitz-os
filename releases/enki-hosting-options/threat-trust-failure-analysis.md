# Threat, Trust-Boundary, and Failure-Domain Analysis

## Shared threats

- Stolen workload or administrator credentials.
- Cross-tenant or cross-subject authorization confusion.
- Secret leakage through configuration, logs, CI, or telemetry.
- Canonical/evidence role confusion in which a backup or export is treated as authoritative state.
- Replay of stale approvals or receipts across environments or providers.
- Network partition after a durable effect but before terminal receipt persistence.
- Provider outage, account suspension, quota exhaustion, or control-plane failure.
- Supply-chain compromise in application dependencies or deployment workflows.
- Misconfigured public database or object-store access.
- Unsupported promotion of TEST evidence into production-control claims.

## Single-cloud trust posture

Single-cloud reduces credential edges and incident ownership but concentrates runtime, identity, data, keys, secrets, and evidence behind one provider/account governance domain. A sufficiently broad account or provider failure can affect multiple Enki planes at once.

Required mitigations before production include separate administrative roles, least-privilege workload identities, isolated service credentials, immutable evidence controls, tested backup export, and independent recovery copies where justified.

## Split-cloud trust posture

Split-cloud reduces one-provider custody concentration but creates more trust links:

- runtime provider to canonical data provider;
- runtime provider to evidence provider;
- human identity across multiple provider accounts;
- cross-provider secret distribution and rotation;
- cross-provider observability and incident correlation.

A split design is safer only when those additional links are narrower and better governed than the concentration risk they replace.

## Failure behavior required of every finalist

1. Runtime unavailable: reject or queue according to explicit operation semantics; never mutate canonical state through a side channel.
2. Canonical database unavailable: fail closed; evidence or caches cannot become substitute authority.
3. Evidence plane unavailable: operations requiring terminal evidence must pause, roll back, or enter reconstructable recovery state.
4. Network partition: exact retry and idempotency rules remain authoritative.
5. Duplicate delivery: at most one conflicting effect.
6. Credential mismatch or expiry: fail closed without audience or context widening.
7. Provider quota exhaustion: surface explicit operational failure; never silently downgrade governance.
8. Recovery: reconstruct from immutable receipts, hashes, and governed exports; do not rewrite historical truth.

## Privacy and compliance boundary

Provider geography, contractual terms, and certifications may inform a later hosting decision, but provider certifications do not certify Enki's deployment. Data residency, deletion, retention, disclosure, backup, and key-custody requirements must be mapped to the actual selected environment and data classes.

## Independent penetration testing

No architecture option resolves this prerequisite. Repository adversarial tests and provider security claims remain distinct from an independent penetration test against the deployed system.
