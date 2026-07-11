"""Application services for synthetic and replay feedback ingestion."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from pydantic import ValidationError

from nks.domain.delivery import (
    FeedbackProvenance,
    FeedbackRecord,
    FeedbackScenario,
)
from nks.domain.models import WorkflowEvent
from nks.ports.delivery import FeedbackRepository
from nks.ports.repositories import EventRepository


@dataclass
class FeedbackReplayHarness:
    repository: FeedbackRepository
    events: EventRepository

    def replay_json(self, raw_scenario: str) -> list[FeedbackRecord]:
        """Validate and replay one scenario while retaining validation failures."""
        try:
            scenario = FeedbackScenario.model_validate_json(raw_scenario)
        except ValidationError as exc:
            digest = hashlib.sha256(raw_scenario.encode("utf-8")).hexdigest()
            subject_id = "feedback-replay"
            try:
                payload = json.loads(raw_scenario)
                if isinstance(payload, dict):
                    subject_id = str(payload.get("scenario_id") or subject_id)
            except json.JSONDecodeError:
                pass

            self.events.append(
                WorkflowEvent(
                    event_id=f"feedback.replay_validation_failed:{digest[:16]}",
                    event_type="feedback.replay_validation_failed",
                    subject_id=subject_id,
                    payload={
                        "reason_code": "SCENARIO_VALIDATION_FAILED",
                        "content_sha256": digest,
                        "error_count": len(exc.errors()),
                    },
                )
            )
            raise

        return self.replay([scenario])

    def replay(self, scenarios: list[FeedbackScenario]) -> list[FeedbackRecord]:
        played_back: list[FeedbackRecord] = []
        for scenario in scenarios:
            original = scenario.feedback
            lineage_ids = list(
                dict.fromkeys([*original.lineage_ids, scenario.scenario_id])
            )
            metadata = {
                **original.metadata,
                "replay_source_provenance": original.provenance,
                "replay_scenario_id": scenario.scenario_id,
            }
            feedback = FeedbackRecord.model_validate(
                {
                    **original.model_dump(),
                    "provenance": FeedbackProvenance.REPLAY,
                    "scenario_id": scenario.scenario_id,
                    "lineage_ids": lineage_ids,
                    "metadata": metadata,
                }
            )
            saved = self.repository.save(feedback)
            self.events.append(
                WorkflowEvent(
                    event_id=f"feedback.replayed:{saved.feedback_id}",
                    event_type="feedback.replayed",
                    subject_id=saved.publication_id,
                    payload={
                        "feedback_id": saved.feedback_id,
                        "scenario_id": scenario.scenario_id,
                        "provenance": saved.provenance,
                        "source_provenance": original.provenance,
                        "lineage_ids": saved.lineage_ids,
                    },
                )
            )
            played_back.append(saved)
        return played_back
