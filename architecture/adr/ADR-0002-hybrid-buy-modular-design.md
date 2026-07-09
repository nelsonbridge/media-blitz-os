# ADR-0002 — Hybrid Buy, Modular Design

## Status

Accepted.

## Context

The NKS publication and distribution layer can use existing free/open-source solutions. These remain buy decisions even when there is no direct capital or operational subscription cost.

Two strategies exist:

1. Select the broadest integrated platform and minimize procurement iterations.
2. Use smaller modular components and maximize replaceability.

The selected architecture is hybrid: deploy one or more integrated solutions where efficient, but preserve modular design through NKS-owned contracts and adapters.

## Decision

The NKS will pursue a hybrid buy strategy:

- Prefer existing free/open-source packages for infrastructure functions.
- Keep all packages replaceable through adapter contracts.
- Avoid embedding external workflow assumptions inside the NKS core.
- Use vendor/platform solutions only below the NKS contract layer.

## Consequences

### Positive

- Faster initial delivery than building everything from scratch.
- Lower vendor lock-in than direct platform coupling.
- Supports future replacement, fork, or direct API fallback.
- Keeps cost negotiability high.

### Negative

- Requires more design discipline.
- Adds adapter and validation work.
- Can feel slower initially than simply adopting one tool.

## Rule

The NKS may buy execution surfaces, but it must own the operating model.