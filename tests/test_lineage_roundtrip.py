import json
from pathlib import Path

from nks.application.export_import import export_portable_state, import_portable_state
from nks.application.reconstruction import PersistedKnowledgeHistory, reconstruct_governed_state


def _lineage_snapshot(reconstructed):
    knowledge = reconstructed.knowledge["K-001"]
    return [
        {
            "state_id": state.state_id,
            "authoritative": state.authoritative,
            "parent_state_id": state.lineage.parent_state_id,
            "supersedes_state_id": state.lineage.supersedes_state_id,
            "branch_id": state.lineage.branch_id,
            "evidence_ids": [
                association.evidence_id for association in state.evidence_associations
            ],
        }
        for state in knowledge.historical_states
    ]


def test_lineage_round_trip_preserves_reconstructable_lineage(tmp_path: Path):
    source = tmp_path / "source"
    (source / "records" / "history").mkdir(parents=True)

    history_payload = {
        "sequence_contract": "ordered-only",
        "transitions": [
            {
                "transition_id": "tr-1",
                "transition_index": 10,
                "knowledge_id": "K-001",
                "from_state_id": None,
                "to_state_id": "S-010",
                "authoritative": False,
                "state_payload": {"status": "draft"},
                "provenance": {"source": "records/sources/SRC-001.json"},
                "evidence_associations": [
                    {
                        "evidence_id": "EVD-001",
                        "relationship": "supports",
                        "metadata": {"strength": "moderate"},
                    }
                ],
                "lineage": {
                    "parent_state_id": None,
                    "supersedes_state_id": None,
                    "branch_id": "main",
                },
            },
            {
                "transition_id": "tr-2",
                "transition_index": 12,
                "knowledge_id": "K-001",
                "from_state_id": "S-010",
                "to_state_id": "S-012",
                "authoritative": False,
                "state_payload": {"status": "review"},
                "provenance": {"source": "records/proofs/PRF-001.json"},
                "evidence_associations": [
                    {
                        "evidence_id": "EVD-002",
                        "relationship": "supports",
                        "metadata": {"strength": "high"},
                    }
                ],
                "lineage": {
                    "parent_state_id": "S-010",
                    "supersedes_state_id": None,
                    "branch_id": "main",
                },
            },
            {
                "transition_id": "tr-3",
                "transition_index": 15,
                "knowledge_id": "K-001",
                "from_state_id": "S-012",
                "to_state_id": "S-015",
                "authoritative": True,
                "state_payload": {"status": "approved"},
                "provenance": {"source": "records/proofs/PRF-002.json"},
                "evidence_associations": [
                    {
                        "evidence_id": "EVD-003",
                        "relationship": "bounds",
                        "metadata": {"reason": "superseded risk"},
                    }
                ],
                "lineage": {
                    "parent_state_id": "S-012",
                    "supersedes_state_id": "S-012",
                    "branch_id": "main",
                },
            },
        ],
    }

    history_path = source / "records" / "history" / "transitions.json"
    history_path.write_text(json.dumps(history_payload, indent=2), encoding="utf-8")

    original_history = PersistedKnowledgeHistory.model_validate(history_payload)
    original_reconstructed = reconstruct_governed_state(original_history)

    archive = tmp_path / "roundtrip.zip"
    export_portable_state(source, archive)
    destination = tmp_path / "destination"
    import_portable_state(archive, destination)

    imported_history = PersistedKnowledgeHistory.model_validate_json(
        (destination / "records" / "history" / "transitions.json").read_text(encoding="utf-8")
    )
    imported_reconstructed = reconstruct_governed_state(imported_history)

    assert _lineage_snapshot(original_reconstructed) == _lineage_snapshot(imported_reconstructed)
    assert (
        original_reconstructed.knowledge["K-001"].current_authoritative_state.state_id
        == imported_reconstructed.knowledge["K-001"].current_authoritative_state.state_id
        == "S-015"
    )
