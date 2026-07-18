import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from nks.application.hosted_identity import (
    HostedBoundaryContext,
    HostedCredential,
    HostedIdentityError,
    HostedIdentityOutcome,
    HostedIdentityPolicy,
    HostedIdentityService,
    TestHostedIdentityAuthority,
)
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryAction, HumanBoundaryPolicy


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "security/enki-hosted-1.0-rc2/hosted-identity-policy.json"
NOW = datetime(2026, 7, 18, 1, 0, tzinfo=timezone.utc)


def authority() -> TestHostedIdentityAuthority:
    return TestHostedIdentityAuthority(key_id="TEST-KEY-1", key=b"test-only-signing-key-1")


def request(**changes: object) -> HostedBoundaryContext:
    payload: dict[str, object] = {
        "namespace_id": "NKS-HOSTED-TEST",
        "tenant_id": "TENANT-A",
        "subject_id": "SUBJECT-1",
        "domain": "operations",
        "audience": "internal",
        "purpose": "reconciliation",
        "principal_id": "PRINCIPAL-A",
        "execution_context": ExecutionContext.TEST,
    }
    payload.update(changes)
    return HostedBoundaryContext(**payload)


def credential(
    signing_authority: TestHostedIdentityAuthority,
    **changes: object,
) -> HostedCredential:
    payload: dict[str, object] = {
        "credential_id": "CRED-1",
        "principal_id": "PRINCIPAL-A",
        "tenant_id": "TENANT-A",
        "permitted_subjects": ("SUBJECT-1",),
        "permitted_domains": ("operations",),
        "permitted_audiences": ("internal",),
        "permitted_purposes": ("reconciliation",),
        "permitted_actions": (BoundaryAction.READ, BoundaryAction.WRITE),
        "issued_at": NOW - timedelta(minutes=5),
        "expires_at": NOW + timedelta(hours=1),
    }
    payload.update(changes)
    return signing_authority.issue(**payload)


def test_persisted_policy_binds_every_required_context_dimension():
    policy = HostedIdentityPolicy(**json.loads(POLICY_PATH.read_text(encoding="utf-8")))

    assert policy.required_dimensions == (
        "principal",
        "tenant",
        "subject",
        "domain",
        "audience",
        "purpose",
        "execution_context",
    )
    assert policy.test_signing_key_reference == (
        "github-actions://ENKI_TEST_IDENTITY_SIGNING_KEY"
    )
    assert policy.production_identity_provider_authorized is False
    assert policy.production_execution_authorized is False
    assert policy.policy_sha256 == (
        "sha256:dfc4ee4dec182b790746981aa2b8e7a305efd4708ba24ee41319725d9bd97924"
    )


def test_exact_test_identity_resolves_to_exact_boundary_authorization():
    signer = authority()
    service = HostedIdentityService(signer)
    requested = request()

    resolution = service.resolve(
        credential(signer),
        requested,
        action=BoundaryAction.READ,
        now=NOW,
    )

    assert resolution.decision.outcome == HostedIdentityOutcome.ALLOWED
    assert resolution.decision.reason_code == "AUTHORIZED"
    assert resolution.authorization is not None
    assert resolution.authorization.boundary == requested.boundary
    assert resolution.authorization.permitted_actions == {BoundaryAction.READ}
    assert resolution.authorization.authority_class == "HOSTED-TEST-IDENTITY"


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"principal_id": "PRINCIPAL-B"}, "PRINCIPAL_MISMATCH"),
        ({"tenant_id": "TENANT-B"}, "TENANT_MISMATCH"),
        ({"subject_id": "SUBJECT-2"}, "SUBJECT_NOT_PERMITTED"),
        ({"domain": "finance"}, "DOMAIN_NOT_PERMITTED"),
        ({"audience": "public"}, "AUDIENCE_NOT_PERMITTED"),
        ({"purpose": "marketing"}, "PURPOSE_NOT_PERMITTED"),
    ],
)
def test_cross_boundary_or_purpose_escalation_fails_closed(changes, reason):
    signer = authority()
    service = HostedIdentityService(signer)

    resolution = service.resolve(
        credential(signer),
        request(**changes),
        action=BoundaryAction.READ,
        now=NOW,
    )

    assert resolution.authorization is None
    assert resolution.decision.outcome == HostedIdentityOutcome.DENIED
    assert resolution.decision.reason_code == reason


def test_test_credential_cannot_satisfy_production_identity_gate():
    signer = authority()
    service = HostedIdentityService(signer)

    resolution = service.resolve(
        credential(signer),
        request(execution_context=ExecutionContext.PRODUCTION),
        action=BoundaryAction.READ,
        now=NOW,
    )

    assert resolution.authorization is None
    assert resolution.decision.reason_code == "TEST_CREDENTIAL_CANNOT_AUTHORIZE_PRODUCTION"


def test_expired_credential_is_denied():
    signer = authority()
    service = HostedIdentityService(signer)
    expired = credential(
        signer,
        issued_at=NOW - timedelta(hours=2),
        expires_at=NOW - timedelta(hours=1),
    )

    resolution = service.resolve(expired, request(), action=BoundaryAction.READ, now=NOW)

    assert resolution.authorization is None
    assert resolution.decision.reason_code == "CREDENTIAL_EXPIRED"


def test_revoked_credential_is_denied():
    signer = authority()
    service = HostedIdentityService(signer)
    revoked = credential(
        signer,
        revoked_at=NOW - timedelta(minutes=1),
    )

    resolution = service.resolve(revoked, request(), action=BoundaryAction.READ, now=NOW)

    assert resolution.authorization is None
    assert resolution.decision.reason_code == "CREDENTIAL_REVOKED"


def test_key_rotation_retires_old_credential_and_new_credential_succeeds():
    signer = authority()
    old = credential(signer)
    signer.rotate(key_id="TEST-KEY-2", key=b"test-only-signing-key-2", retire_prior=True)
    service = HostedIdentityService(signer)

    old_resolution = service.resolve(old, request(), action=BoundaryAction.READ, now=NOW)
    new = credential(signer, credential_id="CRED-2")
    new_resolution = service.resolve(new, request(), action=BoundaryAction.READ, now=NOW)

    assert old_resolution.authorization is None
    assert old_resolution.decision.reason_code == "CREDENTIAL_KEY_RETIRED"
    assert new_resolution.authorization is not None
    assert new_resolution.decision.reason_code == "AUTHORIZED"


def test_forged_credential_signature_is_denied():
    signer = authority()
    service = HostedIdentityService(signer)
    valid = credential(signer)
    forged = valid.model_copy(update={"signature": "hmac-sha256:" + "0" * 64})

    resolution = service.resolve(forged, request(), action=BoundaryAction.READ, now=NOW)

    assert resolution.authorization is None
    assert resolution.decision.reason_code == "FORGED_CREDENTIAL"


def test_unscoped_action_is_denied():
    signer = authority()
    service = HostedIdentityService(signer)
    read_only = credential(signer, permitted_actions=(BoundaryAction.READ,))

    resolution = service.resolve(
        read_only,
        request(),
        action=BoundaryAction.EXPORT,
        now=NOW,
    )

    assert resolution.authorization is None
    assert resolution.decision.reason_code == "ACTION_NOT_PERMITTED"


def test_human_state_policy_remains_stricter_than_valid_tenant_identity():
    signer = authority()
    service = HostedIdentityService(signer)
    valid_credential = credential(signer)

    denied = service.resolve(
        valid_credential,
        request(),
        action=BoundaryAction.READ,
        now=NOW,
        subject_type="PERSON",
    )
    allowed = service.resolve(
        valid_credential,
        request(),
        action=BoundaryAction.READ,
        now=NOW,
        subject_type="PERSON",
        human_policy=HumanBoundaryPolicy(consent_granted=True, purpose_allowed=True),
    )

    assert denied.authorization is None
    assert denied.decision.reason_code == "HUMAN_POLICY_DENIED"
    assert allowed.authorization is not None


def test_denial_evidence_is_privacy_preserving_and_reconstructable():
    signer = authority()
    service = HostedIdentityService(signer)
    requested = request(tenant_id="TENANT-SECRET", purpose="private-purpose")

    resolution = service.resolve(
        credential(signer),
        requested,
        action=BoundaryAction.READ,
        now=NOW,
    )
    serialized = resolution.decision.model_dump_json()

    assert resolution.decision.outcome == HostedIdentityOutcome.DENIED
    assert resolution.decision.event_sha256.startswith("sha256:")
    assert resolution.decision.requested_context_sha256 == requested.context_sha256
    assert "TENANT-SECRET" not in serialized
    assert "private-purpose" not in serialized
    assert "PRINCIPAL-A" not in serialized


def test_require_raises_generic_error_without_boundary_identifiers():
    signer = authority()
    service = HostedIdentityService(signer)

    with pytest.raises(HostedIdentityError) as caught:
        service.require(
            credential(signer),
            request(tenant_id="TENANT-B"),
            action=BoundaryAction.READ,
            now=NOW,
        )

    assert str(caught.value) == "hosted identity operation denied"
    assert caught.value.reason_code == "TENANT_MISMATCH"
    assert "TENANT-B" not in str(caught.value)


def test_policy_rejects_raw_protected_fields_in_denial_evidence():
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    policy["denial_evidence_fields"].append("tenant_id")
    policy["policy_sha256"] = "sha256:" + "0" * 64

    with pytest.raises(ValidationError, match="denial evidence cannot expose"):
        HostedIdentityPolicy(**policy)


def test_credential_model_rejects_production_execution_context():
    signer = authority()
    valid = credential(signer)
    payload = valid.model_dump(mode="python")
    payload["execution_context"] = ExecutionContext.PRODUCTION

    with pytest.raises(ValidationError, match="TEST-only"):
        HostedCredential(**payload)
