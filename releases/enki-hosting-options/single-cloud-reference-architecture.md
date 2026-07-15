# Single-Cloud Reference Architecture

Reference finalist: `CF-NATIVE` with `GCP-NATIVE` retained as the container-native alternative.

## CF-NATIVE

```text
Consumer suites
    |
    v
Cloudflare edge / Workers
    |-- governed Enki consumer boundary
    |-- approval and policy enforcement
    |-- no direct repository shortcut
    |
    +--> D1 canonical operational store
    |      - namespace / tenant / subject / domain / audience boundaries
    |      - logical isolation contract
    |      - production database isolation remains unvalidated
    |
    +--> R2 evidence / export / portability plane
           - immutable evidence packages
           - recovery exports
           - provider-exit artifacts
```

### Trust boundaries

1. Consumer-to-Workers identity and authorization boundary.
2. Workers-to-D1 canonical data boundary.
3. Workers-to-R2 evidence boundary.
4. Administrative Cloudflare account boundary.

### Failure domains

A Cloudflare account, control-plane, identity, or regional/platform failure can affect runtime, canonical data, and evidence access simultaneously. R2 provides logical service separation but not independent-provider failure isolation.

### Data flow

Canonical writes remain governed through Enki application services. D1 stores only authorized canonical effects. Evidence and export artifacts are written separately to R2. Downstream products consume through the stable Enki consumer contract and never write predictions or recommendations directly into canonical state.

### Production prerequisites

Cloudflare's available IAM, secrets, networking, and storage capabilities are architecture candidates only. Production IAM, federation, database isolation, network segmentation, tenant-key custody, secrets lifecycle, and penetration testing remain unresolved until deployed and validated.

## GCP-NATIVE alternative

```text
Consumer suites
    |
    v
Cloud Run (Python Enki runtime)
    |
    +--> Firestore candidate canonical store
    |
    +--> Cloud Storage evidence / export plane
    |
    +--> IAM / workload identity / secret / network candidates
```

Cloud Run minimizes runtime adaptation, but Firestore changes the canonical persistence model. A managed relational database could preserve relational semantics but is not assumed to remain inside the absolute-zero budget. Firestore free usage also does not include all production backup and PITR capabilities.

## Single-cloud selection criteria

Prefer a single-cloud design when reduced operational complexity, one incident owner, and low cross-provider latency are more valuable than provider-failure isolation. Reject it when independent data custody, stronger provider-exit posture, or independent evidence-plane survivability is a governing requirement.
