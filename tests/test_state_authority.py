from pathlib import Path

from nks.views.authority import (
    MANIFEST_PATH,
    build_authority_manifest,
    render_authority_manifest,
    verify_authority_manifest,
    write_authority_manifest,
)


def test_authority_manifest_is_deterministic() -> None:
    first = render_authority_manifest()
    second = render_authority_manifest()

    assert first == second
    assert build_authority_manifest()["authority_precedence"][0] == "canonical_machine_state"
    assert '"manually_editable": false' in first


def test_verification_detects_missing_and_stale_manifest(tmp_path: Path) -> None:
    violations = verify_authority_manifest(tmp_path)
    assert f"missing generated authority manifest: {MANIFEST_PATH}" in violations

    output = write_authority_manifest(tmp_path)
    output.write_text("{}\n", encoding="utf-8")

    violations = verify_authority_manifest(tmp_path)
    assert f"stale generated authority manifest: {MANIFEST_PATH}" in violations


def test_written_manifest_verifies_when_projection_paths_exist(tmp_path: Path) -> None:
    manifest = build_authority_manifest()
    for projection in manifest["generated_authoritative_projections"]:
        path = tmp_path / projection["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("generated\n", encoding="utf-8")

    write_authority_manifest(tmp_path)

    assert verify_authority_manifest(tmp_path) == []
