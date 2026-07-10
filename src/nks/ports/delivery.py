"""Ports for publication delivery and feedback ingestion."""

from __future__ import annotations

from typing import Protocol

from nks.domain.delivery import FeedbackRecord, PublicationPayload, PublicationReceipt


class PublicationAdapter(Protocol):
    def prepare(self, payload: PublicationPayload) -> PublicationReceipt: ...


class FeedbackRepository(Protocol):
    def save(self, feedback: FeedbackRecord) -> FeedbackRecord: ...

    def get(self, feedback_id: str) -> FeedbackRecord | None: ...

    def list_for_publication(self, publication_id: str) -> list[FeedbackRecord]: ...
