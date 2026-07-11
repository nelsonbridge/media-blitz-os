"""Resilience wrappers for publication and event adapters."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable

from nks.domain.delivery import PublicationPayload, PublicationReceipt
from nks.ports.delivery import PublicationAdapter
from nks.ports.repositories import EventRepository


class RetryingPublicationAdapter(PublicationAdapter):
    def __init__(
        self,
        delegate: PublicationAdapter,
        max_attempts: int = 3,
        backoff_seconds: float = 0.0,
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    ) -> None:
        self._delegate = delegate
        self._max_attempts = max_attempts
        self._backoff_seconds = backoff_seconds
        self._retryable_exceptions = retryable_exceptions

    def prepare(self, payload: PublicationPayload) -> PublicationReceipt:
        last_error: Exception | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                return self._delegate.prepare(payload)
            except Exception as exc:
                last_error = exc
                if not isinstance(exc, self._retryable_exceptions) or attempt == self._max_attempts:
                    raise
                if self._backoff_seconds > 0:
                    time.sleep(self._backoff_seconds)
        assert last_error is not None
        raise last_error


class RetryingEventRepository(EventRepository):
    def __init__(
        self,
        delegate: EventRepository,
        max_attempts: int = 3,
        backoff_seconds: float = 0.0,
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    ) -> None:
        self._delegate = delegate
        self._max_attempts = max_attempts
        self._backoff_seconds = backoff_seconds
        self._retryable_exceptions = retryable_exceptions

    def append(self, event: "nks.domain.models.WorkflowEvent") -> None:
        last_error: Exception | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                self._delegate.append(event)
                return
            except Exception as exc:
                last_error = exc
                if not isinstance(exc, self._retryable_exceptions) or attempt == self._max_attempts:
                    raise
                if self._backoff_seconds > 0:
                    time.sleep(self._backoff_seconds)
        assert last_error is not None
        raise last_error

    def list(self) -> list["nks.domain.models.WorkflowEvent"]:
        return self._delegate.list()
