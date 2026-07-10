"""Port for visual rendering adapters."""

from __future__ import annotations

from typing import Protocol

from nks.domain.visuals import VisualAssetRecord, VisualRenderRequest


class VisualRenderer(Protocol):
    def prepare(self, request: VisualRenderRequest) -> VisualAssetRecord: ...
