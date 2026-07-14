# Sprint 3 Dependency Decomposition

## Purpose

Prevent the first live publication cycle from being treated as a single indivisible approval dependency.

## Governing principle

A missing downstream artifact does not invalidate or block independent upstream work. Approval gates apply only to the exact effect they authorize. They do not create authority over unrelated preparation work.

## Independent workstreams

### A. Visual review

The rendered visual package may be reviewed immediately against its manifest and proof boundaries.

A visual decision authorizes or rejects only the reviewed visual package. It does not authorize publication.

### B. Publication-body manufacture

The final article body may be manufactured from the canonical artifact, proof record, narrative arc, editorial state, and governing publication record.

Drafting and revision are preparation activities. They do not require publication approval and do not cause an external effect.

### C. Publication configuration

Channel, account identity, byline, brand treatment, channel copy, and asset selection may be resolved in parallel with visual review and body manufacture.

### D. Final publication authorization

Final authorization is a convergence gate. It becomes available only when the exact body, body hash, approved visual manifest, selected channels, identity, byline, and channel copy are presented together.

Approval authorizes only that exact package and those stated effects.

### E. Live execution and evidence

Publication, receipt capture, social distribution, real-feedback ingestion, governed disposition, and cycle reporting occur after final publication authorization.

## Dependency graph

```text
Visual review ───────────────┐
                             │
Body manufacture ────────────┼──> Final publication authorization
                             │
Publication configuration ───┘
                                      │
                                      v
                            Live execution and evidence
```

No circular dependency exists. Visual review, body manufacture, and publication configuration proceed independently and converge only at the final authorization boundary.

## Workaround rule

If a publication adapter is unavailable, use the documented manual-publication fallback and preserve equivalent receipts, hashes, identity, timestamp, channel, and live URL evidence.
