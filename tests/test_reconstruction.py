import pytest

from nks.application.reconstruction import PersistedKnowledgeHistory, reconstruct_governed_state


def _history() -> PersistedKnowledgeHistory:
    return PersistedKnowledgeHistory.model_validate(
        {
            "transitions": [
                {
                    "transition_id": "tr-1",
                    "transition_index": 0,
                    "knowledge_id": "K-001",
                    "from_state_id": None,
                    "to_state_id": "S-001",
                    "authoritative": False,
                    "state_payload": {"status": "draft"},
                    "provenance": {
                        "source": "records/sources/SRC-001.json",
                        "captured_by": "test-fixture",
                    },
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
                    "transition_index": 1,
                    "knowledge_id": "K-001",
                    "from_state_id": "S-001",
                    "to_state_id": "S-002",
                    "authoritative": True,
                    "state_payload": {"status": "approved"},
                    "provenance": {
                        "source": "records/proofs/PRF-001.json",
                        "captured_by": "test-fixture",
                    },
                    "evidence_associations": [
                        {
                            "evidence_id": "EVD-001",
                            "relationship": "supports",
                            "metadata": {"strength": "high"},
                        },
                        {
                            "evidence_id": "EVD-002",
                            "relationship": "bounds",
                            "metadata": {"reason": "uncertainty"},
                        },
                    ],
                    "lineage": {
                        "parent_state_id": "S-001",
                        "supersedes_state_id": None,
                        "branch_id": "main",
                    },
                },
            ]
        }
    )


def test_reconstruction_is_deterministic_for_identical_valid_histories():
    left = reconstruct_governed_state(_history())
    right = reconstruct_governed_state(_history())

    assert left.model_dump(mode="json") == right.model_dump(mode="json")
    assert left.canonical_fingerprint() == right.canonical_fingerprint()

    reconstructed = left.knowledge["K-001"]
    assert [state.state_id for state in reconstructed.historical_states] == ["S-001", "S-002"]
    assert reconstructed.current_authoritative_state is not None
    assert reconstructed.current_authoritative_state.state_id == "S-002"


def test_reconstruction_is_order_deterministic_for_equivalent_history_sets():
    history = _history().model_dump(mode="json")
    reversed_history = PersistedKnowledgeHistory.model_validate(
        {"transitions": list(reversed(history["transitions"]))}
    )

    left = reconstruct_governed_state(_history())
    right = reconstruct_governed_state(reversed_history)

    assert left.canonical_fingerprint() == right.canonical_fingerprint()
    assert left.semantic_fingerprint() == right.semantic_fingerprint()


def test_reconstruction_repeated_execution_is_idempotent():
    fingerprints: set[str] = set()
    semantic_fingerprints: set[str] = set()

    for _ in range(5):
        reconstructed = reconstruct_governed_state(_history())
        fingerprints.add(reconstructed.canonical_fingerprint())
        semantic_fingerprints.add(reconstructed.semantic_fingerprint())

    assert len(fingerprints) == 1
    assert len(semantic_fingerprints) == 1


def test_reconstruction_preserves_historical_truth_and_current_authority_distinction():
    reconstructed = reconstruct_governed_state(_history()).knowledge["K-001"]

    assert [state.state_id for state in reconstructed.historical_states] == ["S-001", "S-002"]
    assert reconstructed.historical_states[0].authoritative is False
    assert reconstructed.historical_states[1].authoritative is True
    assert reconstructed.current_authoritative_state is not None
    assert reconstructed.current_authoritative_state.state_id == "S-002"
    assert reconstructed.current_authoritative_state.state_payload == {"status": "approved"}


def test_reconstruction_rejects_sequence_mismatch_without_inference():
    bad_history = PersistedKnowledgeHistory.model_validate(
        {
            "transitions": [
                {
                    "transition_id": "tr-1",
                    "transition_index": 0,
                    "knowledge_id": "K-001",
                    "from_state_id": None,
                    "to_state_id": "S-001",
                    "authoritative": False,
                    "state_payload": {"status": "draft"},
                    "provenance": {"source": "records/sources/SRC-001.json"},
                    "evidence_associations": [],
                    "lineage": {
                        "parent_state_id": None,
                        "supersedes_state_id": None,
                        "branch_id": "main",
                    },
                },
                {
                    "transition_id": "tr-2",
                    "transition_index": 1,
                    "knowledge_id": "K-001",
                    "from_state_id": "UNKNOWN-STATE",
                    "to_state_id": "S-002",
                    "authoritative": True,
                    "state_payload": {"status": "approved"},
                    "provenance": {"source": "records/proofs/PRF-001.json"},
                    "evidence_associations": [],
                    "lineage": {
                        "parent_state_id": "S-001",
                        "supersedes_state_id": None,
                        "branch_id": "main",
                    },
                },
            ]
        }
    )

    with pytest.raises(ValueError, match="transition sequence mismatch"):
        reconstruct_governed_state(bad_history)


def test_reconstruction_rejects_non_contiguous_transition_index():
    bad_history = PersistedKnowledgeHistory.model_validate(
        {
            "sequence_contract": "contiguous-index",
            "transitions": [
                {
                    "transition_id": "tr-1",
                    "transition_index": 0,
                    "knowledge_id": "K-001",
                    "from_state_id": None,
                    "to_state_id": "S-001",
                    "authoritative": False,
                    "state_payload": {"status": "draft"},
                    "provenance": {"source": "records/sources/SRC-001.json"},
                    "evidence_associations": [],
                    "lineage": {
                        "parent_state_id": None,
                        "supersedes_state_id": None,
                        "branch_id": "main",
                    },
                },
                {
                    "transition_id": "tr-2",
                    "transition_index": 2,
                    "knowledge_id": "K-001",
                    "from_state_id": "S-001",
                    "to_state_id": "S-002",
                    "authoritative": True,
                    "state_payload": {"status": "approved"},
                    "provenance": {"source": "records/proofs/PRF-001.json"},
                    "evidence_associations": [],
                    "lineage": {
                        "parent_state_id": "S-001",
                        "supersedes_state_id": None,
                        "branch_id": "main",
                    },
                },
            ]
        }
    )

    with pytest.raises(ValueError, match="non-contiguous transition_index"):
        reconstruct_governed_state(bad_history)


def test_reconstruction_allows_non_contiguous_index_when_contract_is_ordered_only():
    bounded_scope = PersistedKnowledgeHistory.model_validate(
        {
            "sequence_contract": "ordered-only",
            "transitions": [
                {
                    "transition_id": "tr-10",
                    "transition_index": 10,
                    "knowledge_id": "K-001",
                    "from_state_id": None,
                    "to_state_id": "S-010",
                    "authoritative": False,
                    "state_payload": {"status": "historical"},
                    "provenance": {"source": "records/sources/SRC-001.json"},
                    "evidence_associations": [],
                    "lineage": {
                        "parent_state_id": None,
                        "supersedes_state_id": None,
                        "branch_id": "main",
                    },
                },
                {
                    "transition_id": "tr-12",
                    "transition_index": 12,
                    "knowledge_id": "K-001",
                    "from_state_id": "S-010",
                    "to_state_id": "S-012",
                    "authoritative": True,
                    "state_payload": {"status": "authoritative"},
                    "provenance": {"source": "records/proofs/PRF-001.json"},
                    "evidence_associations": [],
                    "lineage": {
                        "parent_state_id": "S-010",
                        "supersedes_state_id": None,
                        "branch_id": "main",
                    },
                },
            ]
        }
    )

    reconstructed = reconstruct_governed_state(bounded_scope)
    knowledge = reconstructed.knowledge["K-001"]
    assert [state.state_id for state in knowledge.historical_states] == ["S-010", "S-012"]
    assert knowledge.current_authoritative_state is not None
    assert knowledge.current_authoritative_state.state_id == "S-012"


def test_reconstruction_rejects_multiple_authoritative_states():
    bad_history = PersistedKnowledgeHistory.model_validate(
        {
            "transitions": [
                {
                    "transition_id": "tr-1",
                    "transition_index": 0,
                    "knowledge_id": "K-001",
                    "from_state_id": None,
                    "to_state_id": "S-001",
                    "authoritative": True,
                    "state_payload": {"status": "approved"},
                    "provenance": {"source": "records/sources/SRC-001.json"},
                    "evidence_associations": [],
                    "lineage": {
                        "parent_state_id": None,
                        "supersedes_state_id": None,
                        "branch_id": "main",
                    },
                },
                {
                    "transition_id": "tr-2",
                    "transition_index": 1,
                    "knowledge_id": "K-001",
                    "from_state_id": "S-001",
                    "to_state_id": "S-002",
                    "authoritative": True,
                    "state_payload": {"status": "approved-v2"},
                    "provenance": {"source": "records/proofs/PRF-001.json"},
                    "evidence_associations": [],
                    "lineage": {
                        "parent_state_id": "S-001",
                        "supersedes_state_id": "S-001",
                        "branch_id": "main",
                    },
                },
            ]
        }
    )

    with pytest.raises(ValueError, match="multiple authoritative states"):
        reconstruct_governed_state(bad_history)
