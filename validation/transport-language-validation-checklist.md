# Transport Language Validation Checklist

## Purpose

Validate whether a planned connector write preserves canonical meaning while using the correct surface language.

## Checklist

| Check | Question | Pass Condition |
|---|---|---|
| Canonical Meaning | Is the original NKS concept preserved? | Meaning is unchanged. |
| Source Lineage | Does the representation preserve source identity? | Source IDs and paths remain intact. |
| Proof Boundary | Are evidence limits still visible? | Boundaries remain explicit. |
| Graph Identity | Are graph IDs and relationships preserved? | IDs remain stable. |
| Surface Fit | Does wording fit the destination? | Uses the relevant language profile. |
| Friction Reduction | Does wording reduce unnecessary connector friction? | Avoids risky clusters of wording. |
| No Semantic Drift | Did the rewrite weaken or redirect the idea? | No drift detected. |
| Split Needed | Is the payload too dense for the surface? | Split if needed. |
| Review State | Is manual review required? | Mark if unclear. |

## Validation States

| State | Meaning |
|---|---|
| Pass | Safe to write through target surface. |
| Pass with Boundary | Safe if boundary wording is retained. |
| Split | Break into smaller records. |
| Rewrite Transport Only | Change surface wording, not canonical meaning. |
| Manual Review | Connector friction likely; review before write. |
| Do Not Send | Meaning would be distorted or boundary lost. |

## Application Order

1. Identify canonical concept.
2. Identify target surface.
3. Apply target language profile.
4. Validate meaning preservation.
5. Validate proof and graph identity.
6. Write only if the representation passes.

## Status

Implemented as validation checklist v1.