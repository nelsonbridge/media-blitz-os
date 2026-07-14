"""Run temporal human-state records through the domain-neutral Enki core."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Protocol

from nks.adapters.human_state_enki import project_human_observation, project_human_transition
from nks.domain.human_state import HumanStateObservation, HumanStateTransition
from nks.enki.contracts import ExpressionOrigin, ReconciliationRequest, ReconciliationResult
from nks.enki.reconciliation import ReconciliationEngine


class HumanStateReader(Protocol):
    def list_observations(self, subject_id: str, domain: str) -> Sequence[HumanStateObservation]: ...

    def list_transitions(self, subject_id: str, domain: str) -> Sequence[HumanStateTransition]: ...


class ReconcileHumanState:
    """Compatibility use case for the current human-state bounded context.

    Expression origin is caller-supplied because the legacy contract records
    expression strength, not whether the subject personally declared the state.
    The use case therefore fails closed rather than inventing authorship.
    """

    def __init__(
        self,
        repository: HumanStateReader,
        engine: ReconciliationEngine,
    ) -> None:
        self._repository = repository
        self._engine = engine

    def execute(
        self,
        *,
        subject_id: str,
        domain: str,
        expression_origins: Mapping[str, ExpressionOrigin],
        objective_refs: Sequence[str] = (),
        priority_refs: Sequence[str] = (),
        as_of: datetime,
    ) -> ReconciliationResult:
        human_observations = list(self._repository.list_observations(subject_id, domain))
        missing_origins = sorted(
            item.observation_id
            for item in human_observations
            if item.observation_id not in expression_origins
        )
        if missing_origins:
            raise ValueError(
                "expression origin is required for human observations: "
                + ", ".join(missing_origins)
            )

        observations = [
            project_human_observation(
                item,
                expression_origin=expression_origins[item.observation_id],
            )
            for item in human_observations
        ]
        relationships = [
            project_human_transition(item)
            for item in self._repository.list_transitions(subject_id, domain)
        ]
        subject = observations[0].subject if observations else None
        if subject is None:
            raise ValueError("no human-state observations exist for the requested scope")

        request = ReconciliationRequest(
            subject=subject,
            domain=domain,
            observations=observations,
            relationships=relationships,
            objective_refs=list(objective_refs),
            priority_refs=list(priority_refs),
            as_of=as_of,
        )
        return self._engine.execute(request)
