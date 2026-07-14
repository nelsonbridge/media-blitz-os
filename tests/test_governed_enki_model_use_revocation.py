from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from nks.adapters.approval_grants import JsonApprovalGrantRepository
from nks.adapters.enki_model_use import JsonEnkiModelUseRepository
from nks.adapters.governed_transactions import JsonGovernedTransactionRepository
from nks.application.enki_model_use_execution import (
    build_model_use_revocation_plan,
    execute_governed_model_use_revocation,
)
from nks.application.enki_model_use_policy import build_enki_model_use_package
from nks.application.governed_transactions import (
    GovernedTransactionExecutor,
    TransactionTerminalState,
    canonical_sha256,
)
from nks.enki.contracts import ConfidenceAssertion, ConfidenceLevel, SubjectRef
from nks.enki.model_use_contracts import (
    DownstreamEffectStatus,
    EnkiModelUseDirective,
    EnkiModelUseItem,
    EnkiModelUseRequest,
    ModelUseAudience,
    ModelUseConsentState,
    ModelUseDirectiveAction,
    ModelUseItemKind,
    ModelUseRevocation,
    ModelUseSensitivity,
    ModelUseTemporalState,
)
from nks.governance.approvals import ApprovalDecision, ApprovalGrant, ExecutionContext


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def _now() -> datetime:
    return datetime(2026, 7, 14, 13, 0, tzinfo=timezone.utc)


def _fixture():
    subject = SubjectRef(subject_id="PERSON-1", subject_type="PERSON")
    item = EnkiModelUseItem(
        item_id="F-1",
        item_kind=ModelUseItemKind.FINDING,
        subject=subject,
        domain="career",
        content_sha256=_hash("finding"),
        context=["current-role"],
        temporal_state=ModelUseTemporalState.CURRENT,
        confidence=ConfidenceAssertion(
            level=ConfidenceLevel.HIGH,
            rationale="Supported by TEST evidence.",
            evidence_ids=["E-1"],
        ),
        sensitivity=ModelUseSensitivity.PRIVATE,
        consent_state=ModelUseConsentState.GRANTED,
        allowed_purposes={"career-assistance"},
        provenance_classification="REAL",
    )
    directive = EnkiModelUseDirective(
        directive_id="D-1",
        action=ModelUseDirectiveAction.INCLUDE,
        item_id=item.item_id,
        item_kind=item.item_kind,
        subject=subject,
        domain=item.domain,
        purpose="career-assistance",
        audience=ModelUseAudience.INTERNAL_MODEL,
        required_context={"current-role"},
        rationale="Explicit internal use.",
        issued_by="PERSON-1",
        authority_class="SUBJECT",
        issued_at=_now() - timedelta(minutes=10),
    )
    request = EnkiModelUseRequest(
        package_id="PKG-1",
        subject=subject,
        domain=item.domain,
        purpose="career-assistance",
        audience=ModelUseAudience.INTERNAL_MODEL,
        context={"current-role"},
        execution_context=ExecutionContext.TEST,
        items=[item],
        directives=[directive],
        requested_at=_now(),
        package_version="enki-model-use/v1",
    )
    package = build_enki_model_use_package(request)
    revocation = ModelUseRevocation(
        revocation_id="REV-1",
        package_id=package.package_id,
        package_sha256=package.package_sha256,
        subject=package.subject,
        purpose=package.purpose,
        audience=package.audience,
        execution_context=package.execution_context,
        reason="The subject revoked downstream influence.",
        revoked_by="PERSON-1",
        authority_class="SUBJECT",
        revoked_at=_now() + timedelta(minutes=5),
        transaction_id="TX-REVOKE-1",
    )
    return package, revocation


def _executor(tmp_path):
    approvals = JsonApprovalGrantRepository(tmp_path)
    transactions = JsonGovernedTransactionRepository(tmp_path)
    executor = GovernedTransactionExecutor(
        approval_repository=approvals,
        journal=transactions,
        receipt_repository=transactions,
    )
    return approvals, transactions, executor


def _grant(package, revocation) -> ApprovalGrant:
    return ApprovalGrant(
        approval_id="APPROVAL-REVOKE-1",
        decision=ApprovalDecision.APPROVED,
        execution_context=ExecutionContext.TEST,
        permitted_actions={"enki:model-use:revoke"},
        subject_id=package.subject.subject_id,
        content_sha256=canonical_sha256(revocation),
        authorized_by="PERSON-1",
        authority_class="SUBJECT",
        issued_at=_now(),
        expires_at=_now() + timedelta(hours=1),
    )


def test_revocation_plan_binds_exact_revocation_payload() -> None:
    package, revocation = _fixture()
    plan = build_model_use_revocation_plan(
        package,
        revocation,
        acceptable_authority_classes={"SUBJECT"},
    )
    assert plan.action == "enki:model-use:revoke"
    assert plan.content_sha256 == canonical_sha256(revocation)
    assert plan.transaction_id == revocation.transaction_id


def test_governed_revocation_consumes_authority_and_records_effect(tmp_path) -> None:
    package, revocation = _fixture()
    approvals, transactions, executor = _executor(tmp_path)
    approvals.save_new(_grant(package, revocation))
    repository = JsonEnkiModelUseRepository(tmp_path)
    repository.append_package(package)

    result = execute_governed_model_use_revocation(
        package,
        revocation,
        approval_id="APPROVAL-REVOKE-1",
        acceptable_authority_classes={"SUBJECT"},
        transaction_executor=executor,
        repository=repository,
        now=revocation.revoked_at,
    )

    assert result.transaction_receipt.terminal_state == TransactionTerminalState.COMMITTED
    assert result.effect.status == DownstreamEffectStatus.REVOKED
    assert result.effect.external_effect is False
    assert repository.get_revocation(package.package_id) == revocation
    assert transactions.get_receipt(revocation.transaction_id) == result.transaction_receipt


def test_revocation_exact_retry_is_idempotent(tmp_path) -> None:
    package, revocation = _fixture()
    approvals, _transactions, executor = _executor(tmp_path)
    approvals.save_new(_grant(package, revocation))
    repository = JsonEnkiModelUseRepository(tmp_path)
    repository.append_package(package)

    first = execute_governed_model_use_revocation(
        package,
        revocation,
        approval_id="APPROVAL-REVOKE-1",
        acceptable_authority_classes={"SUBJECT"},
        transaction_executor=executor,
        repository=repository,
        now=revocation.revoked_at,
    )
    retry = execute_governed_model_use_revocation(
        package,
        revocation,
        approval_id="APPROVAL-REVOKE-1",
        acceptable_authority_classes={"SUBJECT"},
        transaction_executor=executor,
        repository=repository,
        now=revocation.revoked_at,
    )
    assert retry.effect == first.effect
    assert retry.transaction_receipt.exact_retry is True


def test_revocation_with_wrong_package_hash_fails_closed(tmp_path) -> None:
    package, revocation = _fixture()
    approvals, _transactions, executor = _executor(tmp_path)
    approvals.save_new(_grant(package, revocation))
    repository = JsonEnkiModelUseRepository(tmp_path)
    tampered = revocation.model_copy(update={"package_sha256": _hash("wrong")})

    with pytest.raises(Exception, match="package hash"):
        execute_governed_model_use_revocation(
            package,
            tampered,
            approval_id="APPROVAL-REVOKE-1",
            acceptable_authority_classes={"SUBJECT"},
            transaction_executor=executor,
            repository=repository,
            now=tampered.revoked_at,
        )
    assert repository.get_revocation(package.package_id) is None
