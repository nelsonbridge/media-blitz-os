"""Integrity-checked execution boundary for Enki-native model-use packages."""

from __future__ import annotations

from datetime import datetime

from nks.application.enki_model_use_policy import (
    ModelUseDispatcher,
    ModelUsePackageConflictError,
    ModelUseRevocationRepository,
    assert_package_context,
    assert_package_not_revoked,
)
from nks.application.governed_transactions import canonical_sha256
from nks.enki.model_use_contracts import (
    DownstreamEffectReceipt,
    EnkiModelUsePackage,
    EnkiModelUseRequest,
)


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
