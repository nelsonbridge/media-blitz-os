"""Deterministic workflow-event journaling for governed model use."""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from nks.domain.models import WorkflowEvent


class WorkflowEventWriter(Protocol):
    def append(self, event: WorkflowEvent) -> None: ...


class ModelUseEventStage(StrEnum):
    APPROVAL_RESERVED = "APPROVAL_RESERVED"
    AUTHORIZED = "AUTHORIZED"
    APPROVAL_CONSUMED = "APPROVAL_CONSUMED"
    PERSISTED = "PERSISTED"
    RESERVATION_RELEASED = "RESERVATION_RELEASED"
    FAILED = "FAILED"
    RECOVERED = "RECOVERED"


def model_use_event_id(
    transaction_id: str,
    stage: ModelUseEventStage,
    *,
    discriminator: str | None = None,
) -> str:
    identity = f"{transaction_id}|{stage.value}"
    if discriminator:
        identity += f"|{discriminator}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return "NKS-EVT-" + digest[:16].upper()


class ModelUseJournal:
    """Record idempotent, non-prescriptive facts about one transaction."""

    def __init__(self, writer: WorkflowEventWriter | None) -> None:
        self._writer = writer

    def record(
        self,
        stage: ModelUseEventStage,
        *,
        occurred_at: datetime,
        transaction_id: str,
        subject_id: str,
        approval_id: str,
        policy_id: str,
        payload_hash: str,
        execution_context: str,
        failure_type: str | None = None,
    ) -> None:
        if self._writer is None:
            return
        payload = {
            "transaction_id": transaction_id,
            "approval_id": approval_id,
            "policy_id": policy_id,
            "payload_hash": payload_hash,
            "execution_context": execution_context,
            "stage": stage.value,
        }
        if failure_type is not None:
            payload["failure_type"] = failure_type
        self._writer.append(
            WorkflowEvent(
                event_id=model_use_event_id(
                    transaction_id,
                    stage,
                    discriminator=failure_type if stage == ModelUseEventStage.FAILED else None,
                ),
                event_type=f"MODEL_USE_{stage.value}",
                occurred_at=occurred_at,
                subject_id=subject_id,
                actor_capability="governed-model-use",
                actor_implementation="nks.application.execute_human_state_model_use",
                authority_source=approval_id,
                payload=payload,
            )
        )
