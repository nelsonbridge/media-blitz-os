from datetime import datetime, timezone

import pytest

from nks.adapters.social_memory import (
    InMemoryDispatchLedger,
    InMemorySocialPublisher,
    PermissionDeniedSocialPublisher,
    TimeoutSocialPublisher,
)
from nks.application.social_dispatch import DispatchRejected, DispatchSocialPublication
from nks.ports.social_publication import SocialPublicationRequest


def request(*, approved: bool = True, metadata: dict[str, str] | None = None):
    return SocialPublicationRequest(
        request_id="NKS-SOC-REQ-000001",
        package_id="NKS-DER-000001",
        publication_id="NKS-PUB-000001",
        channel="linkedin",
        account_reference="executive-profile",
        body="Publishing is downstream of knowledge manufacturing.",
        asset_ids=["NKS-QTC-000001"],
        approved=approved,
        approved_by="user" if approved else None,
        approved_at=datetime.now(timezone.utc) if approved else None,
        idempotency_key="NKS-DER-000001:linkedin:executive-profile",
        credential_reference="TRYPPOST_LINKEDIN_CREDENTIAL",
        metadata=metadata or {},
    )


def test_unapproved_dispatch_is_rejected_before_adapter_call():
    publisher = InMemorySocialPublisher()
    service = DispatchSocialPublication(publisher, InMemoryDispatchLedger())

    with pytest.raises(DispatchRejected, match="explicit user approval"):
        service.execute(request(approved=False), dry_run=False)

    assert publisher.calls == []


def test_dry_run_returns_structured_receipt_and_is_idempotent():
    publisher = InMemorySocialPublisher()
    ledger = InMemoryDispatchLedger()
    service = DispatchSocialPublication(publisher, ledger)
    payload = request()

    first = service.execute(payload, dry_run=True)
    second = service.execute(payload, dry_run=True)

    assert first == second
    assert first.success
    assert first.status == "validated"
    assert first.external_id
    assert first.external_url is None
    assert first.idempotency_key == payload.idempotency_key
    assert len(publisher.calls) == 1
    assert ledger.list() == [first]


def test_publish_receipt_contains_external_url():
    service = DispatchSocialPublication(
        InMemorySocialPublisher(),
        InMemoryDispatchLedger(),
    )

    result = service.execute(request(), dry_run=False)

    assert result.success
    assert result.status == "published"
    assert result.external_url is not None
    assert result.manual_fallback_required is False


def test_timeout_is_retryable_and_queues_manual_fallback():
    service = DispatchSocialPublication(
        TimeoutSocialPublisher(),
        InMemoryDispatchLedger(),
    )

    result = service.execute(request(), dry_run=False)

    assert not result.success
    assert result.error_code == "adapter_timeout"
    assert result.retryable
    assert result.manual_fallback_required


def test_permission_failure_is_terminal_and_queues_manual_fallback():
    service = DispatchSocialPublication(
        PermissionDeniedSocialPublisher(),
        InMemoryDispatchLedger(),
    )

    result = service.execute(request(), dry_run=False)

    assert not result.success
    assert result.error_code == "adapter_permission_denied"
    assert not result.retryable
    assert result.manual_fallback_required


def test_possible_secret_material_is_rejected():
    service = DispatchSocialPublication(
        InMemorySocialPublisher(),
        InMemoryDispatchLedger(),
    )

    with pytest.raises(DispatchRejected, match="possible secret material"):
        service.execute(
            request(metadata={"access_token": "must-not-enter-canonical-payload"}),
            dry_run=True,
        )
