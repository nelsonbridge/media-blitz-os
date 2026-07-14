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
    assert build_authority_manifest()["schema_version"] == "1.2"
    assert build_authority_manifest()["generated_output_families"][0]["directory_glob"] == (
        "generated/model-feedback/*"
    )


def test_verification_detects_missing_and_stale_manifest(tmp_path: Path) -> None:
    violations = verify_authority_manifest(tmp_path)
    assert f"missing generated authority manifest: {MANIFEST_PATH}" in violations

    output = write_authority_manifest(tmp_path)
    output.write_text("{}\n", encoding="utf-8")

    violations = verify_authority_manifest(tmp_path)
    assert f"stale generated authority manifest: {MANIFEST_PATH}" in violations


def _write_required_projection_paths(tmp_path: Path) -> None:
    manifest = build_authority_manifest()
    for projection in manifest["generated_authoritative_projections"]:
        path = tmp_path / projection["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("generated\n", encoding="utf-8")


def test_written_manifest_verifies_when_projection_paths_exist(tmp_path: Path) -> None:
    _write_required_projection_paths(tmp_path)
    write_authority_manifest(tmp_path)

    assert verify_authority_manifest(tmp_path) == []


def test_optional_output_family_may_be_absent(tmp_path: Path) -> None:
    _write_required_projection_paths(tmp_path)
    write_authority_manifest(tmp_path)

    assert verify_authority_manifest(tmp_path) == []


def test_partial_output_family_fails_closed(tmp_path: Path) -> None:
    _write_required_projection_paths(tmp_path)
    output = tmp_path / "generated" / "model-feedback" / "MFR-1"
    output.mkdir(parents=True)
    (output / "payload.json").write_text("{}\n", encoding="utf-8")
    write_authority_manifest(tmp_path)

    violations = verify_authority_manifest(tmp_path)

    assert (
        "incomplete Class 2 output family member: "
        "generated/model-feedback/MFR-1/receipt.json"
    ) in violations


def test_complete_output_family_verifies(tmp_path: Path) -> None:
    _write_required_projection_paths(tmp_path)
    output = tmp_path / "generated" / "model-feedback" / "MFR-1"
    output.mkdir(parents=True)
    (output / "payload.json").write_text("{}\n", encoding="utf-8")
    (output / "receipt.json").write_text("{}\n", encoding="utf-8")
    write_authority_manifest(tmp_path)

    assert verify_authority_manifest(tmp_path) == []
