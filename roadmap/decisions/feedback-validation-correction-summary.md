# Feedback Validation Correction Summary

The roadmap now distinguishes feedback provenance from execution context:

- provenance: `REAL | SYNTHETIC | REPLAY`;
- context: `TEST | PRODUCTION`.

Before production, Sprint 13 must prove the feedback subsystem using:

- `SYNTHETIC/TEST` scenarios;
- `REPLAY/TEST` regression where historical cases exist;
- controlled `REAL/TEST` human evaluation;
- end-to-end ingestion, classification, routing, deduplication, disposition, promotion control, audit, zero-feedback, and calibration evidence.

Sprint 3 no longer requires that an audience member responds. It requires a defined observation window and either:

- attributable `REAL/PRODUCTION` feedback; or
- an immutable zero-feedback receipt.

Actual production feedback becomes post-release calibration evidence. It is not the first test of whether the feedback system works and cannot be fabricated, assumed, or substituted with TEST evidence.
