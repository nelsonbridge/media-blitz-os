from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from nks.adapters.enki_model_use import (
    EnkiModelUseRecordConflictError,
    JsonEnkiModelUseRepository,
)
from nks.application.enki_model_use_execution import (
    assert_model_use_package_integrity,
    execute_model_use_dispatch,
)
from nks.application.enki_model_use_policy import (
    CapabilityIsolatedProductionModelDispatcher,
    ModelUsePackageConflictError,
    NoEffectTestModelDispatcher,
    assert_package_context,
    assert_package_not_revoked,
    build_enki_model_use_package,
)
from nks.enki.contracts import SubjectRef
from nks.enki.model_use_contracts import (
    DownstreamEffectReceipt,
    DownstreamEffectStatus,
    EnkiModelUseDirective,
    EnkiModelUseItem,
    EnkiModelUseRequest,
    ModelUseAudience,
    ModelUseConsentState,
    ModelUseDecisionAction,
    ModelUseDirectiveAction,
    ModelUseItemKind,
    ModelUseRevocation,
    ModelUseSensitivity,
    ModelUseTemporalState,
)
from nks.governance.approvals import ExecutionContext


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime(2026, 7, 14, 11, 0, tzinfo=timezone.utc)


SUBJECT = SubjectRef(subject_id="PERSON-1", subject_type="PERSON")


def _item(
    item_id: str = "ITEM-1",
    *,
    item_kind: ModelUseItemKind = ModelUseItemKind.FINDING,
    subject: SubjectRef = SUBJECT,
    domain: str = "career",
    context: list[str] | None = None,
    temporal_state: ModelUseTemporalState = ModelUseTemporalState.CURRENT,
    sensitivity: ModelUseSensitivity = ModelUseSensitivity.PUBLIC,
    consent_state: ModelUseConsentState = ModelUseConsentState.GRANTED,
    allowed_purposes: set[str] | None = None,
    redaction_required_for: set[ModelUseAudience] | None = None,
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> EnkiModelUseItem:
    return EnkiModelUseItem(
        item_id=item_id,
        item_kind=item_kind,
        subject=subject,
        domain=domain,
        content_sha256=_hash(item_id),
        context=context or ["current-role"],
        temporal_state=temporal_state,
        sensitivity=sensitivity,
        consent_state=consent_state,
        allowed_purposes=allowed_purposes or {"career-assistance"},
        redaction_required_for=redaction_required_for or set(),
        provenance_classification="REAL",
        expires_at=expires_at,
        revoked_at=revoked_at,
    )


def _directive(
    item: EnkiModelUseItem,
    *,
    directive_id: str = "DIR-1",
    action: ModelUseDirectiveAction = ModelUseDirectiveAction.INCLUDE,
    subject: SubjectRef | None = None,
    domain: str | None = None,
    purpose: str = "career-assistance",
    audience: ModelUseAudience = ModelUseAudience.INTERNAL_MODEL,
    required_context: set[str] | None = None,
    transition_inclusion: bool | None = None,
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> EnkiModelUseDirective:
    if item.item_kind == ModelUseItemKind.TRANSITION and transition_inclusion is None:
        transition_inclusion = True
    return EnkiModelUseDirective(
        directive_id=directive_id,
        action=action,
        item_id=item.item_id,
        item_kind=item.item_kind,
        subject=subject or item.subject,
        domain=domain or item.domain,
        purpose=purpose,
        audience=audience,
        required_context=required_context or {"current-role"},
        transition_inclusion=transition_inclusion,
        rationale="Exact governed model-use choice.",
        issued_by="PERSON-1",
        authority_class="SUBJECT",
        issued_at=_now() - timedelta(minutes=5),
        expires_at=expires_at,
        revoked_at=revoked_at,
    )


def _request(
    items: list[EnkiModelUseItem],
    directives: list[EnkiModelUseDirective],
    *,
    package_id: str = "PKG-1",
    subject: SubjectRef = SUBJECT,
    domain: str = "career",
    purpose: str = "career-assistance",
    audience: ModelUseAudience = ModelUseAudience.INTERNAL_MODEL,
    context: set[str] | None = None,
    execution_context: ExecutionContext = ExecutionContext.TEST,
) -> EnkiModelUseRequest:
    return EnkiModelUseRequest(
        package_id=package_id,
        subject=subject,
        domain=domain,
        purpose=purpose,
        audience=audience,
        context=context or {"current-role"},
        execution_context=execution_context,
        items=items,
        directives=directives,
        requested_at=_now(),
        package_version="enki-model-use/v1",
    )


def _revocation(package, **updates) -> ModelUseRevocation:
    values = {
        "revocation_id": "REV-1",
        "package_id": package.package_id,
        "package_sha256": package.package_sha256,
        "subject": package.subject,
        "purpose": package.purpose,
        "audience": package.audience,
        "execution_context": package.execution_context,
        "reason": "The governing subject revoked downstream use.",
        "revoked_by": "PERSON-1",
        "authority_class": "SUBJECT",
        "revoked_at": _now() + timedelta(minutes=1),
        "transaction_id": "TX-REV-1",
    }
    values.update(updates)
    return ModelUseRevocation(**values)


def test_exact_directive_includes_item_and_package_hash_is_deterministic() -> None:
    item = _item()
    request = _request([item], [_directive(item)])

    first = build_enki_model_use_package(request)
    second = build_enki_model_use_package(request)

    assert first == second
    assert first.included_items == [item]
    assert first.decisions[0].action == ModelUseDecisionAction.INCLUDE
    assert first.directive_ids == ["DIR-1"]
    assert_model_use_package_integrity(first)


def test_item_without_directive_is_deferred_not_inferred() -> None:
    item = _item()
    package = build_enki_model_use_package(_request([item], []))

    assert package.included_items == []
    assert package.decisions[0].action == ModelUseDecisionAction.DEFER
    assert "no exact model-use directive" in package.decisions[0].reasons[0]


@pytest.mark.parametrize(
    "temporal_state",
    [
        ModelUseTemporalState.RETRACTED,
        ModelUseTemporalState.EXPIRED,
        ModelUseTemporalState.SUPERSEDED,
        ModelUseTemporalState.INAPPLICABLE,
    ],
)
def test_inapplicable_temporal_state_is_withheld(
    temporal_state: ModelUseTemporalState,
) -> None:
    item = _item(temporal_state=temporal_state)
    package = build_enki_model_use_package(_request([item], [_directive(item)]))

    assert package.decisions[0].action == ModelUseDecisionAction.WITHHOLD
    assert temporal_state.value in package.decisions[0].reasons[0]


def test_disputed_item_is_deferred_even_with_include_directive() -> None:
    item = _item(temporal_state=ModelUseTemporalState.DISPUTED)
    package = build_enki_model_use_package(_request([item], [_directive(item)]))

    assert package.decisions[0].action == ModelUseDecisionAction.DEFER
    assert package.included_items == []


@pytest.mark.parametrize(
    "consent_state",
    [
        ModelUseConsentState.DENIED,
        ModelUseConsentState.REVOKED,
        ModelUseConsentState.UNKNOWN,
    ],
)
def test_nonqualifying_consent_is_withheld(
    consent_state: ModelUseConsentState,
) -> None:
    item = _item(consent_state=consent_state)
    package = build_enki_model_use_package(_request([item], [_directive(item)]))

    assert package.decisions[0].action == ModelUseDecisionAction.WITHHOLD
    assert consent_state.value in package.decisions[0].reasons[0]


def test_item_expiry_and_revocation_are_withheld() -> None:
    expired = _item("EXPIRED", expires_at=_now() - timedelta(seconds=1))
    revoked = _item("REVOKED", revoked_at=_now() - timedelta(seconds=1))
    package = build_enki_model_use_package(
        _request(
            [expired, revoked],
            [_directive(expired, directive_id="DIR-E"), _directive(revoked, directive_id="DIR-R")],
        )
    )

    actions = {decision.item_id: decision for decision in package.decisions}
    assert "item is expired" in actions["EXPIRED"].reasons
    assert "item is revoked" in actions["REVOKED"].reasons


def test_purpose_mismatch_is_withheld() -> None:
    item = _item(allowed_purposes={"research"})
    package = build_enki_model_use_package(_request([item], [_directive(item)]))

    assert package.decisions[0].action == ModelUseDecisionAction.WITHHOLD
    assert "purpose is not allowed" in package.decisions[0].reasons[0]


@pytest.mark.parametrize(
    "sensitivity",
    [
        ModelUseSensitivity.INTERNAL,
        ModelUseSensitivity.PRIVATE,
        ModelUseSensitivity.RESTRICTED,
    ],
)
def test_sensitive_state_is_not_widened_to_external_models(
    sensitivity: ModelUseSensitivity,
) -> None:
    item = _item(sensitivity=sensitivity)
    directive = _directive(item, audience=ModelUseAudience.EXTERNAL_MODEL)
    request = _request(
        [item],
        [directive],
        audience=ModelUseAudience.EXTERNAL_MODEL,
    )
    package = build_enki_model_use_package(request)

    assert package.included_items == []
    assert package.decisions[0].action == ModelUseDecisionAction.WITHHOLD


def test_redaction_requirement_withholds_original_item() -> None:
    item = _item(
        redaction_required_for={ModelUseAudience.EXTERNAL_MODEL},
    )
    directive = _directive(item, audience=ModelUseAudience.EXTERNAL_MODEL)
    package = build_enki_model_use_package(
        _request(
            [item],
            [directive],
            audience=ModelUseAudience.EXTERNAL_MODEL,
        )
    )

    assert package.decisions[0].action == ModelUseDecisionAction.WITHHOLD
    assert "redacted derivative" in package.decisions[0].reasons[0]


def test_transition_requires_explicit_inclusion_choice() -> None:
    item = _item(item_kind=ModelUseItemKind.TRANSITION)
    with pytest.raises(ValidationError, match="explicit inclusion choice"):
        _directive(item, transition_inclusion=None).model_copy(
            update={"transition_inclusion": None}
        ).model_validate(
            _directive(item, transition_inclusion=True).model_dump(
                mode="python",
                exclude={"transition_inclusion"},
            )
        )


def test_transition_explicit_exclusion_is_withheld() -> None:
    item = _item(item_kind=ModelUseItemKind.TRANSITION)
    directive = _directive(item, transition_inclusion=False)
    package = build_enki_model_use_package(_request([item], [directive]))

    assert package.included_items == []
    assert "transition inclusion was not explicitly authorized" in package.decisions[0].reasons


def test_duplicate_directives_for_one_item_fail_closed() -> None:
    item = _item()
    request = _request(
        [item],
        [_directive(item, directive_id="D-1"), _directive(item, directive_id="D-2")],
    )
    with pytest.raises(ModelUsePackageConflictError, match="multiple directives"):
        build_enki_model_use_package(request)


def test_directive_for_absent_item_fails_closed() -> None:
    present = _item("PRESENT")
    absent = _item("ABSENT")
    request = _request([present], [_directive(absent)])

    with pytest.raises(ModelUsePackageConflictError, match="absent or mismatched"):
        build_enki_model_use_package(request)


@pytest.mark.parametrize(
    ("directive_update", "reason"),
    [
        ({"purpose": "other-purpose"}, "directive purpose"),
        ({"audience": ModelUseAudience.EXTERNAL_MODEL}, "directive audience"),
        ({"required_context": {"other-context"}}, "directive context"),
        ({"expires_at": _now() - timedelta(seconds=1)}, "directive is expired"),
        ({"revoked_at": _now() - timedelta(seconds=1)}, "directive is revoked"),
        ({"action": ModelUseDirectiveAction.EXCLUDE}, "explicitly excludes"),
    ],
)
def test_directive_mismatch_or_ineligibility_withholds(
    directive_update: dict,
    reason: str,
) -> None:
    item = _item()
    directive = _directive(item).model_copy(update=directive_update)
    package = build_enki_model_use_package(_request([item], [directive]))

    assert package.decisions[0].action == ModelUseDecisionAction.WITHHOLD
    assert any(reason in item_reason for item_reason in package.decisions[0].reasons)


def test_package_context_substitution_is_rejected() -> None:
    item = _item()
    request = _request([item], [_directive(item)])
    package = build_enki_model_use_package(request)
    mismatched = request.model_copy(update={"purpose": "other-purpose"})

    with pytest.raises(ModelUsePackageConflictError, match="purpose"):
        assert_package_context(package, mismatched)


def test_package_tampering_is_rejected_before_dispatch(tmp_path) -> None:
    item = _item()
    request = _request([item], [_directive(item)])
    package = build_enki_model_use_package(request)
    tampered_item = package.included_items[0].model_copy(
        update={"content_sha256": _hash("tampered")}
    )
    tampered = package.model_copy(update={"included_items": [tampered_item]})

    with pytest.raises(ModelUsePackageConflictError, match="hash is invalid"):
        execute_model_use_dispatch(
            tampered,
            request=request,
            transaction_id="TX-1",
            dispatcher=NoEffectTestModelDispatcher(),
            revocation_repository=JsonEnkiModelUseRepository(tmp_path),
            now=_now(),
        )


def test_exact_revocation_blocks_dispatch(tmp_path) -> None:
    item = _item()
    request = _request([item], [_directive(item)])
    package = build_enki_model_use_package(request)
    repository = JsonEnkiModelUseRepository(tmp_path)
    repository.append_revocation(_revocation(package))

    with pytest.raises(PermissionError, match="package is revoked"):
        execute_model_use_dispatch(
            package,
            request=request,
            transaction_id="TX-1",
            dispatcher=NoEffectTestModelDispatcher(),
            revocation_repository=repository,
            now=_now(),
        )


def test_revocation_hash_mismatch_fails_as_conflict() -> None:
    item = _item()
    request = _request([item], [_directive(item)])
    package = build_enki_model_use_package(request)

    with pytest.raises(ModelUsePackageConflictError, match="hash"):
        assert_package_not_revoked(
            package,
            _revocation(package, package_sha256=_hash("wrong")),
        )


def test_test_dispatcher_has_no_external_effect_or_provider_reference(tmp_path) -> None:
    item = _item()
    request = _request([item], [_directive(item)])
    package = build_enki_model_use_package(request)
    repository = JsonEnkiModelUseRepository(tmp_path)

    receipt = execute_model_use_dispatch(
        package,
        request=request,
        transaction_id="TX-1",
        dispatcher=NoEffectTestModelDispatcher(),
        revocation_repository=repository,
        now=_now(),
    )

    assert receipt.status == DownstreamEffectStatus.NO_EFFECT_TEST
    assert receipt.external_effect is False
    assert receipt.provider_reference is None


def test_test_dispatcher_rejects_production_package() -> None:
    item = _item()
    directive = _directive(item)
    package = build_enki_model_use_package(
        _request(
            [item],
            [directive],
            execution_context=ExecutionContext.PRODUCTION,
        )
    )
    with pytest.raises(PermissionError, match="TEST packages only"):
        NoEffectTestModelDispatcher().dispatch(
            package,
            transaction_id="TX-1",
            now=_now(),
        )


class _FakeTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def dispatch(self, package, *, transaction_id: str) -> str:
        self.calls.append((package.package_id, transaction_id))
        return f"provider:{transaction_id}"


def test_production_dispatcher_requires_production_package_and_explicit_transport() -> None:
    item = _item()
    directive = _directive(item)
    test_package = build_enki_model_use_package(_request([item], [directive]))
    transport = _FakeTransport()
    dispatcher = CapabilityIsolatedProductionModelDispatcher(transport)

    with pytest.raises(PermissionError, match="PRODUCTION packages only"):
        dispatcher.dispatch(test_package, transaction_id="TX-1", now=_now())
    assert transport.calls == []

    production_request = _request(
        [item],
        [directive],
        execution_context=ExecutionContext.PRODUCTION,
    )
    production_package = build_enki_model_use_package(production_request)
    receipt = dispatcher.dispatch(
        production_package,
        transaction_id="TX-2",
        now=_now(),
    )

    assert transport.calls == [("PKG-1", "TX-2")]
    assert receipt.status == DownstreamEffectStatus.DISPATCHED
    assert receipt.external_effect is True
    assert receipt.provider_reference == "provider:TX-2"


def test_test_effect_receipt_cannot_claim_external_effect() -> None:
    with pytest.raises(ValidationError, match="cannot claim an external effect"):
        DownstreamEffectReceipt(
            effect_id="E-1",
            package_id="PKG-1",
            package_sha256=_hash("package"),
            execution_context=ExecutionContext.TEST,
            status=DownstreamEffectStatus.NO_EFFECT_TEST,
            external_effect=True,
            dispatcher_id="bad-test-dispatcher",
            transaction_id="TX-1",
            recorded_at=_now(),
        )


def test_append_only_repository_preserves_packages_effects_and_revocations(tmp_path) -> None:
    item = _item()
    request = _request([item], [_directive(item)])
    package = build_enki_model_use_package(request)
    repository = JsonEnkiModelUseRepository(tmp_path)
    repository.append_package(package)
    repository.append_package(package)

    receipt = NoEffectTestModelDispatcher().dispatch(
        package,
        transaction_id="TX-1",
        now=_now(),
    )
    repository.append_effect(receipt)
    repository.append_effect(receipt)

    revocation = _revocation(package)
    repository.append_revocation(revocation)
    repository.append_revocation(revocation)

    assert repository.get_package(package.package_id) == package
    assert repository.get_effect(receipt.effect_id) == receipt
    assert repository.get_revocation(package.package_id) == revocation

    with pytest.raises(EnkiModelUseRecordConflictError):
        repository.append_package(package.model_copy(update={"purpose": "tampered"}))
    with pytest.raises(EnkiModelUseRecordConflictError):
        repository.append_revocation(
            revocation.model_copy(update={"reason": "different revocation"})
        )
