"""Governed application gateway shared by API and CLI consumer adapters."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from nks.application.consumer_contracts import (
    ConsumerContractFailure,
    ConsumerErrorCode,
    ConsumerOperation,
    ConsumerReceipt,
    ConsumerRequest,
    ConsumerResponse,
    ConsumerStatus,
    PaginationResponse,
    resolve_contract_version,
)
from nks.application.governed_transactions import canonical_sha256
from nks.governance.boundaries import (
    BoundaryAction,
    BoundaryAuthorization,
    BoundaryOutcome,
    evaluate_boundary_authorization,
)


_REPOSITORY_SHORTCUT_KEYS = {
    "repository_path",
    "record_path",
    "records_path",
    "canonical_record_path",
    "canonical_collection",
    "direct_canonical_write",
    "approval_record_path",
    "consume_approval",
    "approval_consumption",
}


class ConsumerServiceResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    data: dict[str, Any] = Field(default_factory=dict)
    items: list[dict[str, Any]] = Field(default_factory=list)
    next_cursor: str | None = None


class ConsumerApplicationService(Protocol):
    def execute(
        self,
        payload: dict[str, Any],
        *,
        page_size: int,
        cursor: str | None,
    ) -> ConsumerServiceResult: ...


class DeterministicConsumerApplicationService:
    """Safe product-neutral reference service used by the local CLI and tests.

    The service does not read or write canonical repositories. It proves that both
    transports reach the same application boundary without manufacturing an
    alternate repository access path.
    """

    def execute(
        self,
        payload: dict[str, Any],
        *,
        page_size: int,
        cursor: str | None,
    ) -> ConsumerServiceResult:
        raw_items = payload.get("items", [])
        items = [dict(item) for item in raw_items if isinstance(item, dict)]
        start = int(cursor or "0") if (cursor or "0").isdigit() else 0
        selected = items[start : start + page_size]
        next_offset = start + len(selected)
        next_cursor = str(next_offset) if next_offset < len(items) else None
        return ConsumerServiceResult(
            data={
                "accepted": True,
                "payload_sha256": canonical_sha256(payload),
            },
            items=selected,
            next_cursor=next_cursor,
        )


class _IdempotencyEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_sha256: str
    response: ConsumerResponse


class ConsumerGateway:
    """Single governed application boundary used by every consumer transport."""

    def __init__(
        self,
        *,
        authorizations: dict[str, BoundaryAuthorization],
        services: dict[ConsumerOperation, ConsumerApplicationService],
    ) -> None:
        self._authorizations = dict(authorizations)
        self._services = dict(services)
        self._idempotency: dict[tuple[str, str, str], _IdempotencyEntry] = {}

    def execute(self, request: ConsumerRequest, *, now: datetime) -> ConsumerResponse:
        version = resolve_contract_version(request.contract_version)
        self._reject_repository_shortcuts(request.payload)

        authorization = self._authorizations.get(request.authorization_id)
        if authorization is None:
            raise ConsumerContractFailure(
                ConsumerErrorCode.AUTHORITY_DENIED,
                "authorization does not exist",
            )

        action = (
            BoundaryAction.READ
            if request.operation == ConsumerOperation.QUERY
            else BoundaryAction.WRITE
        )
        decision = evaluate_boundary_authorization(
            authorization,
            action=action,
            requested_boundary=request.boundary,
            evaluated_at=now,
        )
        if decision.outcome != BoundaryOutcome.ALLOWED:
            raise ConsumerContractFailure(
                ConsumerErrorCode.AUTHORITY_DENIED,
                f"authority denied: {decision.reason_code}",
            )

        service = self._services.get(request.operation)
        if service is None:
            raise ConsumerContractFailure(
                ConsumerErrorCode.OPERATION_UNAVAILABLE,
                f"operation is not available: {request.operation.value}",
            )

        ledger_key = (
            request.boundary.boundary_sha256,
            request.operation.value,
            request.idempotency_key,
        )
        request_sha = request.idempotency_fingerprint
        existing = self._idempotency.get(ledger_key)
        if existing is not None:
            if existing.request_sha256 != request_sha:
                raise ConsumerContractFailure(
                    ConsumerErrorCode.IDEMPOTENCY_CONFLICT,
                    "idempotency key was reused with divergent request content",
                )
            return existing.response

        result = service.execute(
            request.payload,
            page_size=request.pagination.page_size,
            cursor=request.pagination.cursor,
        )
        response_payload = {
            "request_id": request.request_id,
            "contract_version": version,
            "operation": request.operation,
            "status": ConsumerStatus.OK,
            "data": result.data,
            "items": result.items,
            "pagination": PaginationResponse(
                returned=len(result.items),
                next_cursor=result.next_cursor,
            ),
        }
        response_sha = canonical_sha256(response_payload)
        receipt_payload = {
            "receipt_id": f"CONSUMER-RCPT-{response_sha.removeprefix('sha256:')[:24]}",
            "request_id": request.request_id,
            "operation": request.operation,
            "contract_version": version,
            "idempotency_key": request.idempotency_key,
            "request_sha256": request_sha,
            "response_sha256": response_sha,
            "recorded_at": now,
        }
        receipt = ConsumerReceipt(
            **receipt_payload,
            receipt_sha256=canonical_sha256(receipt_payload),
        )
        response = ConsumerResponse(**response_payload, receipt=receipt)
        self._idempotency[ledger_key] = _IdempotencyEntry(
            request_sha256=request_sha,
            response=response,
        )
        return response

    @classmethod
    def _reject_repository_shortcuts(cls, payload: dict[str, Any]) -> None:
        def walk(value: Any) -> None:
            if isinstance(value, dict):
                for key, nested in value.items():
                    normalized = str(key).strip().lower()
                    if normalized in _REPOSITORY_SHORTCUT_KEYS or normalized.startswith(
                        "repository_"
                    ):
                        raise ConsumerContractFailure(
                            ConsumerErrorCode.REPOSITORY_SHORTCUT_DENIED,
                            f"repository shortcut is prohibited: {key}",
                        )
                    walk(nested)
            elif isinstance(value, list):
                for nested in value:
                    walk(nested)

        walk(payload)
