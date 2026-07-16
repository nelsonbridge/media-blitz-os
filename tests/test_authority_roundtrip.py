import json
from pathlib import Path

from nks.application.export_import import export_portable_state, import_portable_state
from nks.application.reconstruction import PersistedKnowledgeHistory, reconstruct_governed_state


def test_authority_round_trip_preserves_historical_truth_without_promotion(tmp_path: Path):
    source = tmp_path / "source"
    (source / "records" / "history").mkdir(parents=True)

    history_payload = {
        "sequence_contract": "ordered-only",
        "transitions": [
            {
                "transition_id": "tr-1",
                "transition_index": 1,
                "knowledge_id": "K-001",
                "from_state_id": None,
                "to_state_id": "S-001",
                "authoritative": False,
                "state_payload": {"status": "historically-valid", "context": "global"},
                "provenance": {"source": "records/sources/SRC-001.json"},
                "evidence_associations": [],
                "lineage": {
                    "parent_state_id": None,
                    "supersedes_state_id": None,
                    "branch_id": "global",
                },
            },
            {
                "transition_id": "tr-2",
                "transition_index": 2,
                "knowledge_id": "K-001",
                "from_state_id": "S-001",
                "to_state_id": "S-002",
                "authoritative": True,
                "state_payload": {"status": "current-authority", "context": "global"},
                "provenance": {"source": "records/proofs/PRF-001.json"},
                "evidence_associations": [],
                "lineage": {
                    "parent_state_id": "S-001",
                    "supersedes_state_id": "S-001",
                    "branch_id": "global",
                },
            },
        ],
    }

    (source / "records" / "history" / "transitions.json").write_text(
        json.dumps(history_payload, indent=2),
        encoding="utf-8",
    )

    archive = tmp_path / "authority.zip"
    export_portable_state(source, archive)
    destination = tmp_path / "destination"
    import_portable_state(archive, destination)

    imported_history = PersistedKnowledgeHistory.model_validate_json(
        (destination / "records" / "history" / "transitions.json").read_text(encoding="utf-8")
    )
    reconstructed = reconstruct_governed_state(imported_history).knowledge["K-001"]

    assert [state.state_id for state in reconstructed.historical_states] == ["S-001", "S-002"]
    assert reconstructed.historical_states[0].authoritative is False
    assert reconstructed.historical_states[1].authoritative is True
    assert reconstructed.current_authoritative_state is not None
    assert reconstructed.current_authoritative_state.state_id == "S-002"
    assert reconstructed.current_authoritative_state.state_payload["status"] == "current-authority"
