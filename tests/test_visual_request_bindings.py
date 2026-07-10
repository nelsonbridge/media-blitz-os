import json
from pathlib import Path

from nks.application.load_records import load_record
from nks.domain.models import GateStatus, VisualPackageRecord

ROOT = Path(__file__).resolve().parents[1] / "records"


def read_request(request_id: str) -> dict:
    path = ROOT / "visual-requests" / f"{request_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_signature_and_hero_requests_are_bound_to_visual_packages_2_through_12():
    for publication_number in range(2, 13):
        suffix = f"{publication_number:06d}"
        signature_request_id = f"NKS-VRQ-{publication_number + 4:06d}"
        hero_request_id = f"NKS-VRQ-{publication_number + 15:06d}"
        visual_id = f"NKS-VIS-{suffix}"
        diagram_id = f"NKS-DGM-{suffix}"
        hero_id = f"NKS-HRO-{suffix}"

        visual = load_record(ROOT, "visuals", visual_id, VisualPackageRecord)
        signature_request = read_request(signature_request_id)
        hero_request = read_request(hero_request_id)

        assert signature_request["publication_id"] == f"NKS-PUB-{suffix}"
        assert signature_request["visual_id"] == diagram_id
        assert signature_request["asset_type"] == "signature-diagram"
        assert signature_request["metadata"]["visual_package_id"] == visual.id
        assert signature_request["metadata"]["review_required"] is True

        assert hero_request["publication_id"] == f"NKS-PUB-{suffix}"
        assert hero_request["visual_id"] == hero_id
        assert hero_request["asset_type"] == "hero-image"
        assert hero_request["metadata"]["visual_package_id"] == visual.id
        assert hero_request["metadata"]["review_required"] is True

        assert visual.signature_diagram_id == diagram_id
        assert visual.hero_image_id == hero_id
        assert diagram_id in visual.asset_ids
        assert hero_id in visual.asset_ids
        assert visual.gate_status == GateStatus.NEEDED


def test_all_signature_and_hero_requests_have_explicit_proof_boundaries():
    for request_number in range(6, 28):
        request = read_request(f"NKS-VRQ-{request_number:06d}")
        assert len(request["proof_boundaries"]) >= 3
        assert request["prompt"].strip()
        assert request["dimensions"] == "1600x900"
