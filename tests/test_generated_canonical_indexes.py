from pathlib import Path

from nks.views.markdown import render_proof_index, render_publication_index, render_visual_index

ROOT = Path(__file__).resolve().parents[1] / "records"


def test_generated_indexes_cover_all_twelve_canonical_publications():
    publication_index = render_publication_index(ROOT)
    proof_index = render_proof_index(ROOT)
    visual_index = render_visual_index(ROOT)

    assert "Total publications: 12" in publication_index
    assert "Total proof records: 12" in proof_index
    assert "Total visual packages: 12" in visual_index

    for index in range(1, 13):
        suffix = f"{index:06d}"
        assert f"NKS-PUB-{suffix}" in publication_index
        assert f"NKS-PRF-{suffix}" in proof_index
        assert f"NKS-VIS-{suffix}" in visual_index
