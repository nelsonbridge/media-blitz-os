"""Manual visual renderer fallback that materializes a deterministic prompt package."""

from __future__ import annotations

from pathlib import Path

from nks.domain.visuals import VisualAssetRecord, VisualAssetStatus, VisualRenderRequest


class ManualVisualRenderer:
    def __init__(self, output_root: Path) -> None:
        self._output_root = output_root

    def prepare(self, request: VisualRenderRequest) -> VisualAssetRecord:
        package_dir = self._output_root / request.publication_id / request.visual_id
        package_dir.mkdir(parents=True, exist_ok=True)

        (package_dir / "request.json").write_text(
            request.model_dump_json(indent=2), encoding="utf-8"
        )
        checklist = "\n".join(
            [
                f"# Visual Render Checklist — {request.visual_id}",
                "",
                f"Publication: {request.publication_id}",
                f"Asset type: {request.asset_type}",
                "",
                "- [ ] Confirm the brief and proof boundaries.",
                "- [ ] Render the asset using the selected visual renderer.",
                "- [ ] Record renderer and output location.",
                "- [ ] Review against the visual brief.",
                "- [ ] Record approval or rejection.",
                "",
            ]
        )
        (package_dir / "checklist.md").write_text(checklist, encoding="utf-8")

        return VisualAssetRecord(
            asset_id=request.visual_id,
            visual_id=request.visual_id,
            publication_id=request.publication_id,
            asset_type=request.asset_type,
            status=VisualAssetStatus.BRIEFED,
            renderer="manual",
            request_id=request.request_id,
            metadata={"package_path": str(package_dir)},
        )
