"""Integrity-checked, approval-bound execution for Enki-native model use."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict

from nks.application.enki_model_use_policy import (
    ModelUseDispatcher,
    ModelUsePackageConflictError,
    ModelUseRevocationRepository,
    assert_package_context,
    assert_package_not_revoked,
)
from nks.application.governed_transactions import (
    FailureHook,
    GovernedOperationAdapter,
    GovernedOperationPlan,
    GovernedOperationResult,
    GovernedTransactionExecutor,
    GovernedTransactionReceipt,
    canonical_sha256,
)
from nks.enki.model_use_contracts import (
    DownstreamEffectReceipt,
    EnkiModelUsePackage,
    EnkiModelUseRequest,
)


class EnkiModelUsePersistence(Protocol):
    def append_package(self, package: EnkiModelUsePackage) -> None: ...

    def append_effect(self, effect: DownstreamEffectReceipt) -> None: ...

    def get_effect(self, effect_id: str) -> DownstreamEffectReceipt | None: ...


class GovernedEnkiModelUseExecution(BaseModel):
    """Deterministic result of an approval-bound model-use transaction."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    package: EnkiModelUsePackage
    effect: DownstreamEffectReceipt
    transaction_receipt: GovernedTransactionReceipt


def model_use_package_sha256(package: EnkiModelUsePackage) -> str:
    payload = package.model_dump(mode="python", exclude={"package_sha256"})
    return canonical_sha256(payload)


def assert_model_use_package_integrity(package: EnkiModelUsePackage) -> None:
    expected = model_use_package_sha256(package)
    if package.package_sha256 != expected:
        raise ModelUsePackageConflictError("model-use package hash is invalid")


def execute_model_use_dispatch(
    package: EnkiModelUsePackage,
    *,
    request: EnkiModelUseRequest,
    transaction_id: str,
    dispatcher: ModelUseDispatcher,
    revocation_repository: ModelUseRevocationRepository,
    now: datetime,
) -> DownstreamEffectReceipt:
    """Fail closed before a bounded dispatcher sees a package."""

    assert_model_use_package_integrity(package)
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


def build_model_use_operation_plan(
    package: EnkiModelUsePackage,
    *,
    transaction_id: str,
    acceptable_authority_classes: set[str],
) -> GovernedOperationPlan:
    """Bind generic transaction authority to one exact model-use package."""

    return GovernedOperationPlan(
        operation_id=f"enki-model-use:{package.package_id}",
        transaction_id=transaction_id,
        action="enki:model-use",
        subject_id=package.subject.subject_id,
        content_sha256=package.package_sha256,
        execution_context=package.execution_context,
        acceptable_authority_classes=acceptable_authority_classes,
        requested_at=package.created_at,
        metadata={
            "package_id": package.package_id,
            "purpose": package.purpose,
            "audience": package.audience.value,
            "context_sha256": package.context_sha256,
            "package_version": package.package_version,
        },
    )


class EnkiModelUseOperationAdapter(GovernedOperationAdapter):
    """Idempotently persist and dispatch one exact package after authority consumption."""

    def __init__(
        self,
        *,
        package: EnkiModelUsePackage,
        request: EnkiModelUseRequest,
        dispatcher: ModelUseDispatcher,
        repository: EnkiModelUsePersistence,
        revocation_repository: ModelUseRevocationRepository,
        now: datetime,
    ) -> None:
        self._package = package
        self._request = request
        self._dispatcher = dispatcher
        self._repository = repository
        self._revocations = revocation_repository
        self._now = now

    def apply(self, plan: GovernedOperationPlan) -> GovernedOperationResult:
        if plan.action != "enki:model-use":
            raise ModelUsePackageConflictError("operation action is not enki:model-use")
        if plan.subject_id != self._package.subject.subject_id:
            raise ModelUsePackageConflictError("operation subject does not match package")
        if plan.content_sha256 != self._package.package_sha256:
            raise ModelUsePackageConflictError("operation content hash does not match package")
        if plan.execution_context != self._package.execution_context:
            raise ModelUsePackageConflictError("operation context does not match package")

        assert_model_use_package_integrity(self._package)
        assert_package_context(self._package, self._request)
        self._repository.append_package(self._package)
        effect = execute_model_use_dispatch(
            self._package,
            request=self._request,
            transaction_id=plan.transaction_id,
            dispatcher=self._dispatcher,
            revocation_repository=self._revocations,
            now=self._now,
        )
        self._repository.append_effect(effect)
        return GovernedOperationResult(
            output_sha256=canonical_sha256(
                {
                    "package_sha256": self._package.package_sha256,
                    "effect": effect,
                }
            ),
            metadata={
                "package_id": self._package.package_id,
                "effect_id": effect.effect_id,
                "effect_status": effect.status.value,
                "external_effect": effect.external_effect,
            },
        )


def execute_governed_enki_model_use(
    package: EnkiModelUsePackage,
    *,
    request: EnkiModelUseRequest,
    transaction_id: str,
    approval_id: str,
    acceptable_authority_classes: set[str],
    transaction_executor: GovernedTransactionExecutor,
    dispatcher: ModelUseDispatcher,
    repository: EnkiModelUsePersistence,
    revocation_repository: ModelUseRevocationRepository,
    now: datetime,
    failure_hook: FailureHook | None = None,
) -> GovernedEnkiModelUseExecution:
    """Reserve, consume, persist, dispatch, receipt, and exactly recover one package."""

    assert_model_use_package_integrity(package)
    assert_package_context(package, request)
    plan = build_model_use_operation_plan(
        package,
        transaction_id=transaction_id,
        acceptable_authority_classes=acceptable_authority_classes,
    )
    adapter = EnkiModelUseOperationAdapter(
        package=package,
        request=request,
        dispatcher=dispatcher,
        repository=repository,
        revocation_repository=revocation_repository,
        now=now,
    )
    receipt = transaction_executor.execute(
        plan,
        approval_id=approval_id,
        adapter=adapter,
        now=now,
        failure_hook=failure_hook,
    )
    effect = repository.get_effect(f"EFFECT-{transaction_id}")
    if effect is None:
        raise RuntimeError("committed model-use transaction has no effect receipt")
    return GovernedEnkiModelUseExecution(
        package=package,
        effect=effect,
        transaction_receipt=receipt,
    )
