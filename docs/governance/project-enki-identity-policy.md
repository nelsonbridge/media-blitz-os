# Project Enki Identity Policy

## Authoritative Identity

The parent system implemented by this repository is **Project Enki**.

Media Blitz is a governed downstream publishing and career-opportunity product. It is not the repository's parent-system identity.

## Current-Authority Rule

Current authoritative documentation, package metadata, runtime help text, module descriptions, navigation, and governance records must identify the parent system as Project Enki.

The following legacy parent-system forms are prohibited in current-authority surfaces:

- `Media Blitz OS`
- `Nelson Knowledge System`
- `nelson-knowledge-system`

The legacy repository slug `nelsonbridge/media-blitz-os` may appear only where required to reference the repository before its administrative rename, or inside explicitly historical and audit evidence.

## Administrative Rename Dependency

Content, governance, package, runtime, and navigation identity can be reconciled within the repository. Renaming the GitHub repository itself is a separate administrative action. Until that rename is completed, immutable evidence URLs, schema identifiers, and exact URL fixtures may retain the live legacy slug under explicit test exceptions.

After the administrative rename, rerun the identity audit and remove exceptions that are no longer required. Historical receipts and provenance-bearing evidence must remain reconstructable rather than being rewritten solely to erase the former URL.

## Retention Rule

Historical records must not be rewritten merely to erase an earlier name. Legacy terms may remain when all of the following are true:

1. the artifact records historical truth, source language, provenance, or an earlier working title;
2. the artifact is clearly classified as historical, audit, source, or product-scoped evidence;
3. the artifact does not claim that the legacy name is current parent-system authority.

## Media Blitz Rule

References to **Media Blitz** remain valid when they describe the downstream product, publishing subsystem, publication package, derivative, audience, platform strategy, or product-specific evidence.

A valid Media Blitz reference must not imply that Media Blitz owns Project Enki canonical knowledge or core mutation authority.

## Link Rule

Use repository-relative links whenever possible. Absolute GitHub links should not hard-code the legacy repository slug unless the target is intentionally historical or cannot be represented as a relative link.

## Enforcement

Automated identity checks scan current-authority text surfaces for prohibited legacy parent-system forms. New exceptions require an explicit path-level justification and must preserve the distinction between historical truth and current authority.
