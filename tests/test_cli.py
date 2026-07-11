import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from nks.cli.main import app
from nks.domain.models import GateStatus
from nks.domain.delivery import FeedbackClassification, FeedbackProvenance, FeedbackRecord


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_prepare_publication_requires_approval(tmp_path: Path):
    repository_root = tmp_path / "repo"
    publications = repository_root / "records" / "publications"
    write_json(
        publications / "NKS-PUB-000001.json",
        {
            "id": "NKS-PUB-000001",
            "title": "The Corpus Is Manufactured, Not Found",
            "status": "review",
            "artifact_id": "NKS-ART-000001",
            "proof_id": "NKS-PRF-000001",
            "narrative_id": "NKS-NAR-000001",
            "visual_package_id": "NKS-VIS-000001",
            "draft_path": "publishing/drafts/NKS-PUB-000001.md",
            "editorial_status": "ready",
            "user_approval": "needed",
        },
    )

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["prepare-publication", str(repository_root), "NKS-PUB-000001", "--platform", "medium"],
    )

    assert result.exit_code != 0
    assert "requires explicit user approval" in result.output


def test_prepare_publication_creates_package_and_events(tmp_path: Path):
    repository_root = tmp_path / "repo"
    publications = repository_root / "records" / "publications"
    visuals = repository_root / "records" / "visuals"
    drafts = repository_root / "publishing" / "drafts"

    write_json(
        publications / "NKS-PUB-000001.json",
        {
            "id": "NKS-PUB-000001",
            "title": "The Corpus Is Manufactured, Not Found",
            "status": "review",
            "artifact_id": "NKS-ART-000001",
            "proof_id": "NKS-PRF-000001",
            "narrative_id": "NKS-NAR-000001",
            "visual_package_id": "NKS-VIS-000001",
            "draft_path": "publishing/drafts/NKS-PUB-000001.md",
            "editorial_status": "ready",
            "user_approval": "approved",
        },
    )
    write_json(
        visuals / "NKS-VIS-000001.json",
        {
            "id": "NKS-VIS-000001",
            "title": "Visual Package",
            "status": "planned",
            "artifact_id": "NKS-ART-000001",
            "publication_id": "NKS-PUB-000001",
            "signature_diagram_id": "NKS-DGM-000001",
            "hero_image_id": "NKS-HRO-000001",
            "asset_ids": ["NKS-DGM-000001", "NKS-HRO-000001"],
            "gate_status": "needed",
        },
    )
    drafts.mkdir(parents=True, exist_ok=True)
    (drafts / "NKS-PUB-000001.md").write_text("publication draft body", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["prepare-publication", str(repository_root), "NKS-PUB-000001", "--platform", "medium"],
    )

    assert result.exit_code == 0
    assert "receipt_id:" in result.output
    assert "package_path:" in result.output

    output_path = repository_root / "medium" / "NKS-PUB-000001"
    assert (output_path / "payload.json").exists()
    assert (output_path / "checklist.md").exists()
    assert (output_path / "receipt.json").exists()
    assert (repository_root / "events" / "events.jsonl").exists()

    events = [json.loads(line) for line in (repository_root / "events" / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(event["event_type"] == "publication.prepared" for event in events)


def test_ingest_feedback_creates_record_and_event(tmp_path: Path):
    repository_root = tmp_path / "repo"
    repository_root.mkdir(parents=True, exist_ok=True)

    feedback_payload = {
        "feedback_id": "NKS-FDB-000010",
        "publication_id": "NKS-PUB-000001",
        "platform": "twitter",
        "classification": "comment",
        "content": "This is a customer comment.",
        "provenance": "real",
    }
    feedback_file = tmp_path / "feedback.json"
    feedback_file.write_text(json.dumps(feedback_payload, indent=2), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["ingest-feedback", str(repository_root), str(feedback_file)],
    )

    assert result.exit_code == 0
    assert "NKS-FDB-000010" in result.output
    assert (repository_root / "feedback" / "NKS-FDB-000010.json").exists()
    events = [json.loads(line) for line in (repository_root / "events" / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(event["event_type"] == "feedback.recorded" for event in events)


def test_replay_feedback_synthetic_scenario(tmp_path: Path):
    repository_root = tmp_path / "repo"
    repository_root.mkdir(parents=True, exist_ok=True)

    scenario_payload = {
        "scenario_id": "SYNTH-000010",
        "description": "Replay synthetic feedback.",
        "feedback": {
            "feedback_id": "NKS-FDB-000011",
            "publication_id": "NKS-PUB-000002",
            "platform": "simulation",
            "classification": "signal",
            "content": "Synthetic replayed signal.",
            "provenance": "synthetic",
            "scenario_id": "SYNTH-000010",
        },
    }
    scenario_file = tmp_path / "scenario.json"
    scenario_file.write_text(json.dumps(scenario_payload, indent=2), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["replay-feedback", str(repository_root), str(scenario_file)],
    )

    assert result.exit_code == 0
    assert "NKS-FDB-000011" in result.output
    assert (repository_root / "feedback" / "NKS-FDB-000011.json").exists()
    events = [json.loads(line) for line in (repository_root / "events" / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(event["event_type"] == "feedback.replayed" for event in events)
