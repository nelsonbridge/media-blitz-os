import json
from pathlib import Path

from nks.application.load_records import load_record
from nks.domain.models import GateStatus, VisualPackageRecord

ROOT = Path(__file__).resolve().parents[1] / "records"


ASSET_TYPES = (
    ("DGM", "signature-diagram", 4, "1600x900"),
    ("HRO", "hero-image", 15, "1600x900"),
    ("CAR", "carousel", 26, "1080x1350 per panel"),
    ("QTC", "quote-card", 37, "1200x1200"),
    ("PIN", "pinterest-pin", 48, "1000x1500"),
)


def read_request(request_id: str) -> dict:
    path = ROOT / "visual-requests" / f"{request_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_all_five_requests_are_bound_to_visual_packages_2_through_12():
    for publication_number in range(2, 13):
        suffix = f"{publication_number:06d}"
        visual = load_record(
            ROOT,
            "visuals",
            f"NKS-VIS-{suffix}",
            VisualPackageRecord,
        )

        expected_assets: list[str] = []
        for prefix, asset_type, offset, dimensions in ASSET_TYPES:
            request_id = f"NKS-VRQ-{publication_number + offset:06d}"
            asset_id = f"NKS-{prefix}-{suffix}"
            request = read_request(request_id)
            expected_assets.append(asset_id)

            assert request["publication_id"] == f"NKS-PUB-{suffix}"
            assert request["visual_id"] == asset_id
            assert request["asset_type"] == asset_type
            assert request["dimensions"] == dimensions
            assert request["metadata"]["visual_package_id"] == visual.id
            assert request["metadata"]["review_required"] is True
            assert len(request["proof_boundaries"]) >= 3
            assert request["prompt"].strip()

        assert visual.signature_diagram_id == f"NKS-DGM-{suffix}"
        assert visual.hero_image_id == f"NKS-HRO-{suffix}"
        assert visual.asset_ids == expected_assets
        assert visual.gate_status == GateStatus.NEEDED


def test_visual_request_registry_is_complete_and_contiguous():
    request_ids = {
        path.stem
        for path in (ROOT / "visual-requests").glob("NKS-VRQ-*.json")
    }
    assert request_ids == {
        f"NKS-VRQ-{request_number:06d}"
        for request_number in range(1, 61)
    }
