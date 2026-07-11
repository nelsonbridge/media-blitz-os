"""Deterministic social adapter implementations for contract verification."""

from __future__ import annotations

from datetime import datetime, timezone

from nks.ports.social_publication import (
    SocialPublicationRequest,
    SocialPublicationResult,
)


class InMemoryDispatchLedger:
    def __init__(self) -> None:
        self._results: dict[str, SocialPublicationResult] = {}

    def get(self, idempotency_key: str) -> SocialPublicationResult | None:
        return self._results.get(idempotency_key)

    def save(self, result: SocialPublicationResult) -> None:
        existing = self._results.get(result.idempotency_key)
        if existing is not None and existing != result:
            raise ValueError("conflicting receipt for existing idempotency key")
        self._results[result.idempotency_key] = result

    def list(self) -> list[SocialPublicationResult]:
        return [self._results[key] for key in sorted(self._results)]


class InMemorySocialPublisher:
    def __init__(self) -> None:
        self.calls: list[tuple[SocialPublicationRequest, bool]] = []

    def publish(
        self,
        request: SocialPublicationRequest,
        *,
        dry_run: bool,
    ) -> SocialPublicationResult:
        self.calls.append((request, dry_run))
        status = "validated" if dry_run else "published"
        suffix = request.idempotency_key.replace(":", "-")
        return SocialPublicationResult(
            success=True,
            status=status,
            external_id=f"test-{suffix}",
            external_url=None if dry_run else f"https://example.invalid/posts/{suffix}",
            idempotency_key=request.idempotency_key,
            created_at=datetime.now(timezone.utc),
            audit_log=(
                f"channel={request.channel}",
                f"account_reference={request.account_reference}",
                f"dry_run={str(dry_run).lower()}",
            ),
        )


class TimeoutSocialPublisher:
    def publish(
        self,
        request: SocialPublicationRequest,
        *,
        dry_run: bool,
    ) -> SocialPublicationResult:
        raise TimeoutError("vendor request timed out")


class PermissionDeniedSocialPublisher:
    def publish(
        self,
        request: SocialPublicationRequest,
        *,
        dry_run: bool,
    ) -> SocialPublicationResult:
        raise PermissionError("missing required platform scope")
