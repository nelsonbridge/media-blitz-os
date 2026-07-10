# Visual Package Index

## Authority

Canonical visual-package state is stored in:

- `records/visuals/*.json`
- generated human view: `generated/visual-package-index.md`

This file is now a compatibility view for publication records that have not yet been converted to canonical JSON. Do not use its summary counts as canonical runtime state.

## Canonical Visual Packages

| Publication ID | Visual Package | Signature Diagram | Hero Image | Gate | Canonical Record |
|---|---|---|---|---|---|
| NKS-PUB-000001 | NKS-VIS-000001 | NKS-DGM-000001 | NKS-HRO-000001 | ready | `records/visuals/NKS-VIS-000001.json` |

Canonical package count: **1**

## Legacy Planned Packages Awaiting Canonical Conversion

| Publication ID | Planned Visual Package | Status |
|---|---|---|
| NKS-PUB-000002 | NKS-VIS-000002 | Planned — legacy record only |
| NKS-PUB-000003 | NKS-VIS-000003 | Planned — legacy record only |
| NKS-PUB-000004 | NKS-VIS-000004 | Planned — legacy record only |
| NKS-PUB-000005 | NKS-VIS-000005 | Planned — legacy record only |
| NKS-PUB-000006 | NKS-VIS-000006 | Planned — legacy record only |
| NKS-PUB-000007 | NKS-VIS-000007 | Planned — legacy record only |
| NKS-PUB-000008 | NKS-VIS-000008 | Planned — legacy record only |
| NKS-PUB-000009 | NKS-VIS-000009 | Planned — legacy record only |
| NKS-PUB-000010 | NKS-VIS-000010 | Planned — legacy record only |
| NKS-PUB-000011 | NKS-VIS-000011 | Planned — legacy record only |
| NKS-PUB-000012 | NKS-VIS-000012 | Planned — legacy record only |

## Reconciliation Rule

1. Canonical JSON and generated views win when state conflicts.
2. Legacy rows remain only to prevent loss of unconverted planning data.
3. Each legacy row must be removed when its canonical JSON record is created.
4. Runtime code must read canonical JSON, not this compatibility file.
