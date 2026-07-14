"""Deterministic policy, packaging, revocation, and bounded model-use dispatch."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from nks.application.governed_transactions import canonical_sha256
from nks.enki.contracts import ConfidenceLevel
from nks.enki.model_use_contracts import (
    DownstreamEffectReceipt,
    DownstreamEffectStatus,
    EnkiModelUseDirective,
    EnkiModelUseItem,
    EnkiModelUsePackage,
    EnkiModelUseRequest,
    ModelUseAudience,
    ModelUseConsentState,
    ModelUseDecisionAction,
    ModelUseDirectiveAction,
    ModelUseItemDecision,
    ModelUseItemKind,
    ModelUseRevocation,
    ModelUseSensitivity,
    ModelUseTemporalState,
)
from nks.governance.approvals import ExecutionContext


class ModelUsePackageConflictError(RuntimeError):
    """Raised when directives or package context are ambiguous or mismatched."""


class ModelUseRevocationRepository(Protocol):
    def get_revocation(self, package_id: str) -> ModelUseRevocation | None: ...

    def append_revocation(self, revocation: ModelUseRevocation) -> None: ...


class ModelUseDispatcher(Protocol):
    dispatcher_id: str

    def dispatch(
        self,
        package: EnkiModelUsePackage,
        *,
        transaction_id: str,
        now: datetime,
    ) -> DownstreamEffectReceipt: ...


class ProductionModelTransport(Protocol):
    def dispatch(
        self,
        package: EnkiModelUsePackage,
        *,
        transaction_id: str,
    ) -> str: ...


def model_use_context_sha256(request: EnkiModelUseRequest) -> str:
    return canonical_sha256(
        {
            "subject": request.subject,
            "domain": request.domain,
            "purpose": request.purpose,
            "audience": request.audience,
            "context": sorted(request.context),
            "execution_context": request.execution_context,
            "requested_at": request.requested_at,
            "package_version": request.package_version,
        }
    )


def _decision(
    item: EnkiModelUseItem,
    action: ModelUseDecisionAction,
    reasons: list[str],
    directive: EnkiModelUseDirective | None,
) -> ModelUseItemDecision:
    return ModelUseItemDecision(
        item_id=item.item_id,
        action=action,
        directive_id=directive.directive_id if directive else None,
        reasons=list(dict.fromkeys(reasons)),
        metadata={
            "item_kind": item.item_kind.value,
            "confidence_level": item.confidence.level.value,
        },
    )


def _base_item_reasons(
    request: EnkiModelUseRequest,
    item: EnkiModelUseItem,
) -> tuple[ModelUseDecisionAction | None, list[str]]:
    reasons: list[str] = []
    if item.subject != request.subject:
        reasons.append("item subject does not match package subject")
    if item.domain != request.domain:
        reasons.append("item domain does not match package domain")
    if request.purpose not in item.allowed_purposes:
        reasons.append("package purpose is not allowed for this item")
    if item.expires_at is not None and item.expires_at <= request.requested_at:
        reasons.append("item is expired")
    if item.revoked_at is not None and item.revoked_at <= request.requested_at:
        reasons.append("item is revoked")
    if item.temporal_state in {
        ModelUseTemporalState.RETRACTED,
        ModelUseTemporalState.EXPIRED,
        ModelUseTemporalState.SUPERSEDED,
        ModelUseTemporalState.INAPPLICABLE,
    }:
        reasons.append(f"item temporal state is {item.temporal_state.value}")
    if item.consent_state in {
        ModelUseConsentState.DENIED,
        ModelUseConsentState.REVOKED,
        ModelUseConsentState.UNKNOWN,
    }:
        reasons.append(f"item consent state is {item.consent_state.value}")
    if request.audience in item.redaction_required_for:
        reasons.append(
            "a separately approved redacted derivative is required for this audience"
        )
    if (
        item.sensitivity == ModelUseSensitivity.INTERNAL
        and request.audience == ModelUseAudience.EXTERNAL_MODEL
    ):
        reasons.append("INTERNAL item cannot be sent to an external model")
    if (
        item.sensitivity == ModelUseSensitivity.PRIVATE
        and request.audience == ModelUseAudience.EXTERNAL_MODEL
    ):
        reasons.append("PRIVATE item cannot be sent to an external model")
    if item.sensitivity == ModelUseSensitivity.RESTRICTED:
        reasons.append("RESTRICTED item cannot enter a model-use package")
    if reasons:
        return ModelUseDecisionAction.WITHHOLD, reasons
    if item.temporal_state == ModelUseTemporalState.DISPUTED:
        return ModelUseDecisionAction.DEFER, [
            "DISPUTED item is preserved but cannot control downstream behavior"
        ]
    if item.confidence.level in {ConfidenceLevel.UNKNOWN, ConfidenceLevel.LOW}:
        return ModelUseDecisionAction.DEFER, [
            f"{item.confidence.level.value} confidence cannot control downstream behavior"
        ]
    return None, []


def _directive_reasons(
    request: EnkiModelUseRequest,
    item: EnkiModelUseItem,
    directive: EnkiModelUseDirective,
) -> tuple[ModelUseDecisionAction | None, list[str]]:
    reasons: list[str] = []
    if directive.item_id != item.item_id or directive.item_kind != item.item_kind:
        reasons.append("directive does not bind the exact item")
    if directive.subject != request.subject or directive.subject != item.subject:
        reasons.append("directive subject does not match package and item")
    if directive.domain != request.domain or directive.domain != item.domain:
        reasons.append("directive domain does not match package and item")
    if directive.purpose != request.purpose:
        reasons.append("directive purpose does not match package purpose")
    if directive.audience != request.audience:
        reasons.append("directive audience does not match package audience")
    if directive.required_context and not directive.required_context <= request.context:
        reasons.append("package context does not satisfy directive context")
    if directive.expires_at is not None and directive.expires_at <= request.requested_at:
        reasons.append("directive is expired")
    if directive.revoked_at is not None and directive.revoked_at <= request.requested_at:
        reasons.append("directive is revoked")
    if directive.action == ModelUseDirectiveAction.EXCLUDE:
        reasons.append("directive explicitly excludes this item")
    if item.item_kind == ModelUseItemKind.TRANSITION:
        if directive.transition_inclusion is not True:
            reasons.append("transition inclusion was not explicitly authorized")
    if reasons:
        return ModelUseDecisionAction.WITHHOLD, reasons
    return None, []


def build_enki_model_use_package(
    request: EnkiModelUseRequest,
) -> EnkiModelUsePackage:
    """Build one deterministic package without widening context or authority."""

    directives_by_item: dict[tuple[str, ModelUseItemKind], EnkiModelUseDirective] = {}
    for directive in request.directives:
        key = (directive.item_id, directive.item_kind)
        if key in directives_by_item:
            raise ModelUsePackageConflictError(
                f"multiple directives bind the same item: {directive.item_id}"
            )
        directives_by_item[key] = directive

    included: list[EnkiModelUseItem] = []
    decisions: list[ModelUseItemDecision] = []
    used_directive_ids: set[str] = set()

    for item in sorted(request.items, key=lambda candidate: candidate.item_id):
        directive = directives_by_item.get((item.item_id, item.item_kind))
        if directive is not None:
            used_directive_ids.add(directive.directive_id)

        action, reasons = _base_item_reasons(request, item)
        if action is not None:
            decisions.append(_decision(item, action, reasons, directive))
            continue
        if directive is None:
            decisions.append(
                _decision(
                    item,
                    ModelUseDecisionAction.DEFER,
                    ["no exact model-use directive exists for this item"],
                    None,
                )
            )
            continue

        action, reasons = _directive_reasons(request, item, directive)
        if action is not None:
            decisions.append(_decision(item, action, reasons, directive))
            continue
        included.append(item)
        decisions.append(
            _decision(
                item,
                ModelUseDecisionAction.INCLUDE,
                ["exact purpose-bound directive and item policy allow inclusion"],
                directive,
            )
        )

    unused = sorted(
        directive.directive_id
        for directive in request.directives
        if directive.directive_id not in used_directive_ids
    )
    if unused:
        raise ModelUsePackageConflictError(
            f"directives reference absent or mismatched items: {unused}"
        )

    context_hash = model_use_context_sha256(request)
    package_payload = {
        "package_id": request.package_id,
        "subject": request.subject,
        "domain": request.domain,
        "purpose": request.purpose,
        "audience": request.audience,
        "context": sorted(request.context),
        "execution_context": request.execution_context,
        "included_items": included,
        "decisions": decisions,
        "directive_ids": sorted(used_directive_ids),
        "context_sha256": context_hash,
        "created_at": request.requested_at,
        "package_version": request.package_version,
        "metadata": request.metadata,
    }
    package_hash = canonical_sha256(package_payload)
    return EnkiModelUsePackage(
        **package_payload,
        package_sha256=package_hash,
    )


def assert_package_context(
    package: EnkiModelUsePackage,
    request: EnkiModelUseRequest,
) -> None:
    expected_context_hash = model_use_context_sha256(request)
    checks = {
        "id": package.package_id == request.package_id,
        "subject": package.subject == request.subject,
        "domain": package.domain == request.domain,
        "purpose": package.purpose == request.purpose,
        "audience": package.audience == request.audience,
        "context": package.context == request.context,
        "execution context": package.execution_context == request.execution_context,
        "context hash": package.context_sha256 == expected_context_hash,
    }
    for name, valid in checks.items():
        if not valid:
            raise ModelUsePackageConflictError(f"package {name} does not match request")


def assert_package_not_revoked(
    package: EnkiModelUsePackage,
    revocation: ModelUseRevocation | None,
) -> None:
    if revocation is None:
        return
    checks = {
        "package id": revocation.package_id == package.package_id,
        "package hash": revocation.package_sha256 == package.package_sha256,
        "subject": revocation.subject == package.subject,
        "purpose": revocation.purpose == package.purpose,
        "audience": revocation.audience == package.audience,
        "context": revocation.execution_context == package.execution_context,
    }
    for name, valid in checks.items():
        if not valid:
            raise ModelUsePackageConflictError(f"revocation {name} does not match")
    raise PermissionError("model-use package is revoked")


class NoEffectTestModelDispatcher:
    """TEST dispatcher with no transport, credentials, endpoint, or callback surface."""

    dispatcher_id = "enki-no-effect-test-dispatcher/v1"

    def dispatch(
        self,
        package: EnkiModelUsePackage,
        *,
        transaction_id: str,
        now: datetime,
    ) -> DownstreamEffectReceipt:
        if package.execution_context != ExecutionContext.TEST:
            raise PermissionError("TEST dispatcher accepts TEST packages only")
        return DownstreamEffectReceipt(
            effect_id=f"EFFECT-{transaction_id}",
            package_id=package.package_id,
            package_sha256=package.package_sha256,
            execution_context=ExecutionContext.TEST,
            status=DownstreamEffectStatus.NO_EFFECT_TEST,
            external_effect=False,
            dispatcher_id=self.dispatcher_id,
            transaction_id=transaction_id,
            recorded_at=now,
            metadata={"included_item_count": len(package.included_items)},
        )


class CapabilityIsolatedProductionModelDispatcher:
    """PRODUCTION dispatcher that cannot exist without an explicit transport."""

    dispatcher_id = "enki-production-model-dispatcher/v1"

    def __init__(self, transport: ProductionModelTransport) -> None:
        self._transport = transport

    def dispatch(
        self,
        package: EnkiModelUsePackage,
        *,
        transaction_id: str,
        now: datetime,
    ) -> DownstreamEffectReceipt:
        if package.execution_context != ExecutionContext.PRODUCTION:
            raise PermissionError("PRODUCTION dispatcher accepts PRODUCTION packages only")
        provider_reference = self._transport.dispatch(
            package,
            transaction_id=transaction_id,
        )
        if not provider_reference:
            raise RuntimeError("production transport returned no provider reference")
        return DownstreamEffectReceipt(
            effect_id=f"EFFECT-{transaction_id}",
            package_id=package.package_id,
            package_sha256=package.package_sha256,
            execution_context=ExecutionContext.PRODUCTION,
            status=DownstreamEffectStatus.DISPATCHED,
            external_effect=True,
            dispatcher_id=self.dispatcher_id,
            transaction_id=transaction_id,
            provider_reference=provider_reference,
            recorded_at=now,
            metadata={"included_item_count": len(package.included_items)},
        )


def dispatch_model_use_package(
    package: EnkiModelUsePackage,
    *,
    request: EnkiModelUseRequest,
    transaction_id: str,
    dispatcher: ModelUseDispatcher,
    revocation_repository: ModelUseRevocationRepository,
    now: datetime,
) -> DownstreamEffectReceipt:
    """Verify exact context and revocation before invoking a bounded dispatcher."""

    assert_package_context(package, request)
    assert_package_not_revoked(
        package,
        revocation_repository.get_revocation(package.package_id),
    )
    return dispatcher.dispatch(
        package,
        transaction_id=transaction_id,
        now=now,
    )
