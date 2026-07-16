"""Deterministic reconstruction of governed knowledge state from persisted history."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Literal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvidenceAssociation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=1)
    relationship: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LineageMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parent_state_id: str | None = None
    supersedes_state_id: str | None = None
    branch_id: str | None = None


class TransitionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transition_id: str = Field(min_length=1)
    transition_index: int = Field(ge=0)
    knowledge_id: str = Field(min_length=1)
    from_state_id: str | None = None
    to_state_id: str = Field(min_length=1)
    authoritative: bool = False
    state_payload: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any]
    evidence_associations: list[EvidenceAssociation] = Field(default_factory=list)
    lineage: LineageMetadata


class PersistedKnowledgeHistory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence_contract: Literal["ordered-only", "contiguous-index"] = "ordered-only"
    transitions: list[TransitionRecord] = Field(min_length=1)


class ReconstructedState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state_id: str
    authoritative: bool
    state_payload: dict[str, Any]
    provenance: dict[str, Any]
    evidence_associations: list[EvidenceAssociation]
    lineage: LineageMetadata


class ReconstructedKnowledge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_id: str
    transitions: list[TransitionRecord]
    historical_states: list[ReconstructedState]
    current_authoritative_state: ReconstructedState | None = None


class ReconstructedGovernedState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge: dict[str, ReconstructedKnowledge]

    def canonical_fingerprint(self) -> str:
        payload = self.model_dump(mode="json")
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return sha256(encoded).hexdigest()

    def semantic_fingerprint(self) -> str:
        payload = self.model_dump(mode="json")
        for knowledge in payload["knowledge"].values():
            for transition in knowledge["transitions"]:
                transition.pop("transition_id", None)
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return sha256(encoded).hexdigest()


def reconstruct_governed_state(
    history: PersistedKnowledgeHistory,
) -> ReconstructedGovernedState:
    by_knowledge: dict[str, list[TransitionRecord]] = {}
    for transition in history.transitions:
        by_knowledge.setdefault(transition.knowledge_id, []).append(transition)

    reconstructed: dict[str, ReconstructedKnowledge] = {}

    for knowledge_id, transitions in by_knowledge.items():
        ordered = sorted(
            transitions,
            key=lambda item: (item.transition_index, item.transition_id),
        )

        expected_index = 0

        seen_indices: set[int] = set()
        seen_transition_ids: set[str] = set()
        current_state_id: str | None = None
        states: list[ReconstructedState] = []

        for transition in ordered:
            if transition.transition_index in seen_indices:
                raise ValueError(
                    f"duplicate transition_index for {knowledge_id}: {transition.transition_index}"
                )
            seen_indices.add(transition.transition_index)

            if (
                history.sequence_contract == "contiguous-index"
                and transition.transition_index != expected_index
            ):
                raise ValueError(
                    f"non-contiguous transition_index for {knowledge_id}: "
                    f"expected {expected_index}, received {transition.transition_index}"
                )
            expected_index += 1

            if transition.transition_id in seen_transition_ids:
                raise ValueError(
                    f"duplicate transition_id for {knowledge_id}: {transition.transition_id}"
                )
            seen_transition_ids.add(transition.transition_id)

            if transition.from_state_id != current_state_id:
                raise ValueError(
                    "transition sequence mismatch for "
                    f"{knowledge_id}: expected from_state_id={current_state_id}, "
                    f"received {transition.from_state_id}"
                )

            state = ReconstructedState(
                state_id=transition.to_state_id,
                authoritative=transition.authoritative,
                state_payload=transition.state_payload,
                provenance=transition.provenance,
                evidence_associations=transition.evidence_associations,
                lineage=transition.lineage,
            )
            states.append(state)
            current_state_id = transition.to_state_id

        authoritative_states = [state for state in states if state.authoritative]
        if len(authoritative_states) > 1:
            raise ValueError(
                f"multiple authoritative states for {knowledge_id}: "
                f"{[state.state_id for state in authoritative_states]}"
            )

        reconstructed[knowledge_id] = ReconstructedKnowledge(
            knowledge_id=knowledge_id,
            transitions=ordered,
            historical_states=states,
            current_authoritative_state=authoritative_states[0] if authoritative_states else None,
        )

    return ReconstructedGovernedState(knowledge=reconstructed)
