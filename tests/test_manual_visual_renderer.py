from pathlib import Path

from nks.adapters.manual_visuals import ManualVisualRenderer
from nks.domain.visuals import VisualAssetStatus, VisualRenderRequest


def test_manual_visual_renderer_creates_deterministic_prompt_package(tmp_path: Path):
    renderer = ManualVisualRenderer(tmp_path)
    request = VisualRenderRequest(
        request_id="NKS-VRQ-000001",
        visual_id="NKS-DGM-000001",
        publication_id="NKS-PUB-000001",
        asset_type="signature-diagram",
        prompt="Render the knowledge manufacturing pipeline as a clean systems diagram.",
        proof_boundaries=[
            "Do not claim measured public outcomes.",
            "Represent GitHub as current persistence, not permanent architecture.",
        ],
        dimensions="1600x900",
    )

    first = renderer.prepare(request)
    second = renderer.prepare(request)
    package = tmp_path / "NKS-PUB-000001" / "NKS-DGM-000001"

    assert first == second
    assert first.status == VisualAssetStatus.BRIEFED
    assert first.renderer == "manual"
    assert (package / "request.json").exists()
    assert (package / "checklist.md").exists()
