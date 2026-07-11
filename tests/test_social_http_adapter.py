from datetime import datetime, timezone

import pytest

from nks.adapters.social_http import JsonHttpSocialPublisher
from nks.ports.social_publication import SocialPublicationRequest


class Response:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class Transport:
    def __init__(self, response: Response):
        self.response = response
        self.calls: list[dict] = []

    def post(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class Credentials:
    def __init__(self, value: str = "credential-value"):
        self.value = value
        self.references: list[str] = []

    def resolve(self, credential_reference: str) -> str:
        self.references.append(credential_reference)
        return self.value


class Mapper:
    vendor_name = "candidate"

    def endpoint(self, request):
        return "https://candidate.invalid/api/posts"

    def map_request(self, request):
        return {
            "channel": request.channel,
            "account": request.account_reference,
            "content": request.body,
            "media": request.asset_ids,
            "scheduled_at": request.publish_at.isoformat() if request.publish_at else None,
            "metadata": {
                "package_id": request.package_id,
                "publication_id": request.publication_id,
            },
        }

    def normalize_result(self, response_payload):
        return (
            response_payload.get("id"),
            response_payload.get("url"),
            response_payload.get("status", "accepted"),
        )


def request():
    return SocialPublicationRequest(
        request_id="NKS-SOC-REQ-000001",
        package_id="NKS-DER-000001",
        publication_id="NKS-PUB-000001",
        channel="linkedin",
        account_reference="executive-profile",
        body="Publishing is downstream of knowledge manufacturing.",
        asset_ids=["NKS-QTC-000001"],
        approved=True,
        approved_by="user",
        approved_at=datetime.now(timezone.utc),
        idempotency_key="NKS-DER-000001:linkedin:executive-profile",
        credential_reference="SOCIAL_LINKEDIN_PRIMARY",
    )


def publisher(response: Response, credential: str = "credential-value"):
    transport = Transport(response)
    credentials = Credentials(credential)
    adapter = JsonHttpSocialPublisher(
        transport=transport,
        credentials=credentials,
        mapper=Mapper(),
    )
    return adapter, transport, credentials


def test_dry_run_maps_without_resolving_credentials_or_calling_transport():
    adapter, transport, credentials = publisher(Response(201, {}))

    result = adapter.publish(request(), dry_run=True)

    assert result.success
    assert result.status == "validated"
    assert transport.calls == []
    assert credentials.references == []
    assert "mapped_fields=account,channel,content,media,metadata,scheduled_at" in result.audit_log


def test_live_publish_uses_idempotency_header_and_normalizes_receipt():
    adapter, transport, credentials = publisher(
        Response(201, {"id": "external-1", "url": "https://social.example/post/1", "status": "scheduled"})
    )
    payload = request()

    result = adapter.publish(payload, dry_run=False)

    assert result.success
    assert result.external_id == "external-1"
    assert result.external_url == "https://social.example/post/1"
    assert result.status == "scheduled"
    assert credentials.references == [payload.credential_reference]
    call = transport.calls[0]
    assert call["headers"]["Idempotency-Key"] == payload.idempotency_key
    assert call["headers"]["Authorization"] == "Bearer credential-value"
    assert "credential-value" not in " ".join(result.audit_log)


@pytest.mark.parametrize("status", [401, 403])
def test_authentication_and_scope_failures_are_permission_errors(status):
    adapter, _, _ = publisher(Response(status, {"error": "denied"}))
    with pytest.raises(PermissionError):
        adapter.publish(request(), dry_run=False)


@pytest.mark.parametrize("status", [429, 500, 503])
def test_rate_limit_and_server_errors_are_retryable(status):
    adapter, _, _ = publisher(Response(status, {"error": "retry"}))
    with pytest.raises(TimeoutError):
        adapter.publish(request(), dry_run=False)


def test_other_non_success_response_is_terminal():
    adapter, _, _ = publisher(Response(422, {"error": "invalid payload"}))
    with pytest.raises(RuntimeError):
        adapter.publish(request(), dry_run=False)


def test_empty_credential_is_rejected():
    adapter, _, _ = publisher(Response(201, {}), credential="")
    with pytest.raises(PermissionError):
        adapter.publish(request(), dry_run=False)
