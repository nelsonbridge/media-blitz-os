"""Application service governing social publication dispatch."""

from __future__ import annotations

from datetime import datetime, timezone

from nks.ports.social_publication import (
    DispatchLedger,
    SocialPublicationRequest,
    SocialPublicationResult,
    SocialPublisher,
)


class DispatchRejected(ValueError):
    """Raised when an NKS policy prevents adapter dispatch."""


class DispatchSocialPublication:
    def __init__(self, publisher: SocialPublisher, ledger: DispatchLedger) -> None:
        self._publisher = publisher
        self._ledger = ledger

    def execute(
        self,
        request: SocialPublicationRequest,
        *,
        dry_run: bool = True,
    ) -> SocialPublicationResult:
        prior = self._ledger.get(request.idempotency_key)
        if prior is not None:
            return prior

        if request.approval_required and not request.approved:
            raise DispatchRejected("explicit user approval is required before dispatch")

        self._validate_secret_boundary(request)

        try:
            result = self._publisher.publish(request, dry_run=dry_run)
        except TimeoutError as exc:
            result = self._failure(
                request,
                code="adapter_timeout",
                message=str(exc) or "adapter timed out",
                retryable=True,
            )
        except PermissionError as exc:
            result = self._failure(
                request,
                code="adapter_permission_denied",
                message=str(exc) or "adapter permission denied",
                retryable=False,
            )
        except Exception as exc:  # adapter boundary: convert unknown vendor errors
            result = self._failure(
                request,
                code="adapter_failure",
                message=str(exc) or exc.__class__.__name__,
                retryable=False,
            )

        if result.idempotency_key != request.idempotency_key:
            raise DispatchRejected("adapter returned a mismatched idempotency key")

        self._ledger.save(result)
        return result

    @staticmethod
    def _validate_secret_boundary(request: SocialPublicationRequest) -> None:
        forbidden = ("token", "secret", "password", "cookie", "authorization")
        serialized = request.model_dump_json().lower()
        for marker in forbidden:
            if marker in serialized and marker not in request.credential_reference.lower():
                raise DispatchRejected(f"possible secret material found in request: {marker}")

    @staticmethod
    def _failure(
        request: SocialPublicationRequest,
        *,
        code: str,
        message: str,
        retryable: bool,
    ) -> SocialPublicationResult:
        return SocialPublicationResult(
            success=False,
            status="failed",
            error_code=code,
            error_message=message,
            retryable=retryable,
            manual_fallback_required=True,
            idempotency_key=request.idempotency_key,
            created_at=datetime.now(timezone.utc),
            audit_log=("external dispatch failed", "manual fallback queued"),
        )
