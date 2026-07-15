"""Stable product-neutral consumer contracts for Enki service boundaries.

The contracts are deliberately transport-neutral. HTTP-style API adapters and CLI
adapters both parse the same request model, call the same governed application
service gateway, and emit the same response, error, pagination, idempotency, and
receipt structures.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.governance.boundaries import BoundaryContext


SUPPORTED_CONTRACT_VERSIONS = ("1.0",)


class ConsumerOperation(StrEnum):
    QUERY = "QUERY"
    COMMAND = "COMMAND"


class ConsumerStatus(StrEnum):
    OK = "OK"
    ERROR = "ERROR"


class ConsumerErrorCode(StrEnum):
    UNSUPPORTED_VERSION = "UNSUPPORTED_VERSION"
    AMBIGUOUS_VERSION = "AMBIGUOUS_VERSION"
    INVALID_REQUEST = "INVALID_REQUEST"
    AUTHORITY_DENIED = "AUTHORITY_DENIED"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    REPOSITORY_SHORTCUT_DENIED = "REPOSITORY_SHORTCUT_DENIED"
    OPERATION_UNAVAILABLE = "OPERATION_UNAVAILABLE"


class PaginationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    page_size: int = Field(default=50, ge=1, le=100)
    cursor: str | None = None


class PaginationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    returned: int = Field(ge=0)
    next_cursor: str | None = None


class ConsumerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(min_length=1)
    contract_version: str = Field(min_length=1)
    operation: ConsumerOperation
    boundary: BoundaryContext
    authorization_id: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=256)
    payload: dict[str, Any] = Field(default_factory=dict)
    pagination: PaginationRequest = Field(default_factory=PaginationRequest)

    @property
    def idempotency_fingerprint(self) -> str:
        return canonical_sha256(
            self.model_dump(mode="python", exclude={"request_id"})
        )


class ConsumerReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    operation: ConsumerOperation
    contract_version: str
    idempotency_key: str
    request_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    response_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    recorded_at: datetime
    receipt_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_receipt_hash(self) -> "ConsumerReceipt":
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"receipt_sha256"})
        )
        if self.receipt_sha256 != expected:
            raise ValueError("consumer receipt hash is invalid")
        return self


class ConsumerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str
    contract_version: str
    operation: ConsumerOperation
    status: ConsumerStatus = ConsumerStatus.OK
    data: dict[str, Any]
    items: list[dict[str, Any]] = Field(default_factory=list)
    pagination: PaginationResponse
    receipt: ConsumerReceipt


class ConsumerErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str | None = None
    contract_version: str | None = None
    status: ConsumerStatus = ConsumerStatus.ERROR
    error_code: ConsumerErrorCode
    message: str
    supported_versions: tuple[str, ...] = SUPPORTED_CONTRACT_VERSIONS
    error_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_error_hash(self) -> "ConsumerErrorResponse":
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"error_sha256"})
        )
        if self.error_sha256 != expected:
            raise ValueError("consumer error hash is invalid")
        return self


class ConsumerContractFailure(RuntimeError):
    def __init__(self, code: ConsumerErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def resolve_contract_version(value: str) -> str:
    normalized = value.strip()
    if not normalized or any(token in normalized for token in (",", "*", "|", ";")):
        raise ConsumerContractFailure(
            ConsumerErrorCode.AMBIGUOUS_VERSION,
            "contract version must identify exactly one supported version",
        )
    if normalized not in SUPPORTED_CONTRACT_VERSIONS:
        raise ConsumerContractFailure(
            ConsumerErrorCode.UNSUPPORTED_VERSION,
            f"unsupported contract version: {normalized}",
        )
    return normalized


def build_error_response(
    *,
    code: ConsumerErrorCode,
    message: str,
    request_id: str | None = None,
    contract_version: str | None = None,
) -> ConsumerErrorResponse:
    payload = {
        "request_id": request_id,
        "contract_version": contract_version,
        "status": ConsumerStatus.ERROR,
        "error_code": code,
        "message": message,
        "supported_versions": SUPPORTED_CONTRACT_VERSIONS,
    }
    return ConsumerErrorResponse(**payload, error_sha256=canonical_sha256(payload))


def render_contract_markdown() -> str:
    """Return deterministic human-readable documentation for contract v1.0."""

    return """# Enki Consumer Contract v1.0

> Generated deterministically from the Sprint 21 stable consumer boundary.

## Supported version

- `1.0`

## Request

Required fields: `request_id`, `contract_version`, `operation`, `boundary`,
`authorization_id`, `idempotency_key`, `payload`, and `pagination`.

Operations are `QUERY` and `COMMAND`. Both are executed through the same governed
application gateway. Repository paths, canonical-record shortcuts, and direct
approval-consumption fields are prohibited.

## Response

Successful responses contain `status=OK`, `data`, `items`, `pagination`, and an
immutable hash-bound `receipt`.

## Errors

Errors use stable codes: `UNSUPPORTED_VERSION`, `AMBIGUOUS_VERSION`,
`INVALID_REQUEST`, `AUTHORITY_DENIED`, `IDEMPOTENCY_CONFLICT`,
`REPOSITORY_SHORTCUT_DENIED`, and `OPERATION_UNAVAILABLE`.

## Pagination

`page_size` is bounded to 1..100. `cursor` is opaque to consumers. Responses expose
`returned` and `next_cursor`.

## Idempotency

An exact retry with the same boundary, operation, idempotency key, and request
fingerprint returns the original response and receipt. Reuse with divergent content
fails closed with `IDEMPOTENCY_CONFLICT`.

## Compatibility

Consumers must send exactly one supported version. Wildcards, version ranges,
comma-separated alternatives, and unknown versions fail closed.
"""


def compatibility_fixture() -> dict[str, Any]:
    return {
        "contract": "enki-consumer",
        "supported_versions": list(SUPPORTED_CONTRACT_VERSIONS),
        "request_fields": [
            "request_id",
            "contract_version",
            "operation",
            "boundary",
            "authorization_id",
            "idempotency_key",
            "payload",
            "pagination",
        ],
        "operations": [item.value for item in ConsumerOperation],
        "error_codes": [item.value for item in ConsumerErrorCode],
        "page_size": {"minimum": 1, "maximum": 100, "default": 50},
        "idempotency": "exact-retry-reuses-original-receipt",
        "repository_shortcuts": "denied",
    }
