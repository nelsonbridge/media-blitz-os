"""Transport adapters for the stable Enki consumer contract.

Both adapters intentionally delegate to the same :class:`ConsumerGateway`. Neither
adapter receives a repository object, repository path, or approval-consumption
primitive, preventing transport-specific governance bypasses.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import ValidationError

from nks.application.consumer_contracts import (
    ConsumerContractFailure,
    ConsumerErrorCode,
    ConsumerRequest,
    build_error_response,
)
from nks.application.consumer_service import ConsumerGateway


class ConsumerApiAdapter:
    def __init__(self, gateway: ConsumerGateway) -> None:
        self._gateway = gateway

    def invoke(self, payload: dict[str, Any], *, now: datetime) -> dict[str, Any]:
        request_id = payload.get("request_id") if isinstance(payload, dict) else None
        version = payload.get("contract_version") if isinstance(payload, dict) else None
        try:
            request = ConsumerRequest.model_validate(payload)
            response = self._gateway.execute(request, now=now)
            return response.model_dump(mode="json")
        except ConsumerContractFailure as exc:
            return build_error_response(
                code=exc.code,
                message=exc.message,
                request_id=request_id if isinstance(request_id, str) else None,
                contract_version=version if isinstance(version, str) else None,
            ).model_dump(mode="json")
        except ValidationError as exc:
            return build_error_response(
                code=ConsumerErrorCode.INVALID_REQUEST,
                message=exc.errors()[0]["msg"] if exc.errors() else "invalid request",
                request_id=request_id if isinstance(request_id, str) else None,
                contract_version=version if isinstance(version, str) else None,
            ).model_dump(mode="json")


class ConsumerCliAdapter:
    """JSON-in/JSON-out CLI adapter over the exact same governed gateway."""

    def __init__(self, gateway: ConsumerGateway) -> None:
        self._api = ConsumerApiAdapter(gateway)

    def invoke_json(self, request_json: str, *, now: datetime) -> str:
        try:
            payload = json.loads(request_json)
        except json.JSONDecodeError as exc:
            error = build_error_response(
                code=ConsumerErrorCode.INVALID_REQUEST,
                message=f"invalid JSON: {exc.msg}",
            )
            return json.dumps(error.model_dump(mode="json"), sort_keys=True)
        if not isinstance(payload, dict):
            error = build_error_response(
                code=ConsumerErrorCode.INVALID_REQUEST,
                message="request must be a JSON object",
            )
            return json.dumps(error.model_dump(mode="json"), sort_keys=True)
        result = self._api.invoke(payload, now=now)
        return json.dumps(result, sort_keys=True)
