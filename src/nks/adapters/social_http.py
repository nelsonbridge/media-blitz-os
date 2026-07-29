"""Generic JSON/HTTP implementation for vendor-specific social mappings."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Protocol

from nks.ports.social_publication import (
    SocialPublicationRequest,
    SocialPublicationResult,
)


class HttpResponse(Protocol):
    status_code: int

    def json(self) -> dict[str, Any]: ...


class JsonHttpTransport(Protocol):
    def post(
        self,
        *,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout_seconds: float,
    ) -> HttpResponse: ...


class CredentialProvider(Protocol):
    def resolve(self, credential_reference: str) -> str: ...


class SocialVendorMapper(Protocol):
    vendor_name: str

    def endpoint(self, request: SocialPublicationRequest) -> str: ...

    def map_request(self, request: SocialPublicationRequest) -> dict[str, Any]: ...

    def normalize_result(
        self,
        response_payload: dict[str, Any],
    ) -> tuple[str | None, str | None, str]: ...


class JsonHttpSocialPublisher:
    """Transport adapter that keeps vendor mapping and credentials replaceable."""

    _SENSITIVE_KEYS = {
        "access_token",
        "authorization",
        "api_key",
        "apikey",
        "credential",
        "token",
        "password",
        "secret",
        "cookie",
    }

    def __init__(
        self,
        *,
        transport: JsonHttpTransport,
        credentials: CredentialProvider,
        mapper: SocialVendorMapper,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._transport = transport
        self._credentials = credentials
        self._mapper = mapper
        self._timeout_seconds = timeout_seconds

    @classmethod
    def _redact_sensitive_fields(cls, value: object) -> object:
        if isinstance(value, dict):
            return {
                key: ("[REDACTED]" if cls._is_sensitive_key(key) else cls._redact_sensitive_fields(item))
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [cls._redact_sensitive_fields(item) for item in value]
        return value

    @classmethod
    def _is_sensitive_key(cls, key: str) -> bool:
        normalized = key.lower().replace("-", "_").replace(" ", "_")
        return any(marker in normalized for marker in cls._SENSITIVE_KEYS)

    def publish(
        self,
        request: SocialPublicationRequest,
        *,
        dry_run: bool,
    ) -> SocialPublicationResult:
        vendor_payload = self._mapper.map_request(request)
        redacted_payload = self._redact_sensitive_fields(deepcopy(vendor_payload))
        if dry_run:
            return SocialPublicationResult(
                success=True,
                status="validated",
                external_id=None,
                external_url=None,
                idempotency_key=request.idempotency_key,
                created_at=datetime.now(timezone.utc),
                audit_log=(
                    f"vendor={self._mapper.vendor_name}",
                    f"channel={request.channel}",
                    "dry_run=true",
                    f"mapped_fields={','.join(sorted(vendor_payload))}",
                ),
            )

        credential = self._credentials.resolve(request.credential_reference)
        if not credential:
            raise PermissionError("credential reference resolved to an empty value")

        response = self._transport.post(
            url=self._mapper.endpoint(request),
            headers={
                "Authorization": f"Bearer {credential}",
                "Content-Type": "application/json",
                "Idempotency-Key": request.idempotency_key,
            },
            payload=redacted_payload,
            timeout_seconds=self._timeout_seconds,
        )

        payload = response.json()
        if response.status_code in {401, 403}:
            raise PermissionError("vendor rejected the configured credential or scope")
        if response.status_code == 429 or response.status_code >= 500:
            raise TimeoutError(f"retryable vendor response: HTTP {response.status_code}")
        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError(f"terminal vendor response: HTTP {response.status_code}")

        external_id, external_url, status = self._mapper.normalize_result(payload)
        return SocialPublicationResult(
            success=True,
            status=status,
            external_id=external_id,
            external_url=external_url,
            idempotency_key=request.idempotency_key,
            created_at=datetime.now(timezone.utc),
            audit_log=(
                f"vendor={self._mapper.vendor_name}",
                f"channel={request.channel}",
                "dry_run=false",
                f"http_status={response.status_code}",
            ),
        )
