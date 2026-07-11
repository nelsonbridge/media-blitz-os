"""Application services for synthetic and replay feedback ingestion."""

from __future__ import annotations

from dataclasses import dataclass

from nks.domain.delivery import FeedbackRecord, FeedbackScenario
from nks.ports.delivery import FeedbackRepository
from nks.ports.repositories import EventRepository
from nks.domain.models import WorkflowEvent


@dataclass
class FeedbackReplayHarness:
    repository: FeedbackRepository
    events: EventRepository

    def replay(self, scenarios: list[FeedbackScenario]) -> list[FeedbackRecord]:
        played_back: list[FeedbackRecord] = []
        for scenario in scenarios:
            feedback = self.repository.save(scenario.feedback)
            self.events.append(
                WorkflowEvent(
                    event_id=f"feedback.replayed:{feedback.feedback_id}",
                    event_type="feedback.replayed",
                    subject_id=feedback.publication_id,
                    payload={
                        "feedback_id": feedback.feedback_id,
                        "scenario_id": scenario.scenario_id,
                        "provenance": feedback.provenance,
                    },
                )
            )
            played_back.append(feedback)
        return played_back
