from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from nks.adapters.approval_grants import JsonApprovalGrantRepository
from nks.adapters.governed_model_use import JsonGovernedHumanStateModelUseWriter
from nks.adapters.workflow_events import JsonWorkflowEventRecordRepository
from nks.application.execute_human_state_model_use import (
    ExecuteGovernedHumanStateModelUse,
)
from nks.application.human_state_model_use import (
    BuildHumanStateModelUsePackage,
    ResolveHumanStateInterpretation,
)
from nks.application.model_use_journal import ModelUseEventStage, model_use_event_id
from nks.audit.model_use import ForensicStatus, reconstruct_model_use
from nks.domain.human_state import (
    ExpressionStrength,
    HumanStateObservation,
    IngestionScope,
    ModelIngestionPolicy,
    TemporalStatus,
)
from nks.governance.approvals import (
    ApprovalDecision,
    ApprovalGrant,
    ApprovalRequest,
    ExecutionContext,
)


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime(2026, 7, 14, 8, 0, tzinfo=timezone.utc)


class HumanStateReader:
    def __init__(self) -> None:
        self.observation = HumanStateObservation(
            observation_id="OBS-1",
            subject_id="SUBJECT-1",
            content="Prioritize stable income.",
            content_hash=_hash("Prioritize stable income."),
            domain="career",
            state_type="DECLARED_PRIORITY",
            provenance="REAL",
            source_id="SOURCE-1",
            observed_at=_now(),
            effective_from=date(2026, 7, 1),
            expression_strength=ExpressionStrength.EXPLICIT,
            confidence="HIGH",
            temporal_status=TemporalStatus.CURRENT,
        )
        self.policy = ModelIngestionPolicy(
            policy_id="POL-1",
            subject_id="SUBJECT-1",
            domain="career",
            observation_id=self.observation.observation_id,
            observation_hash=self.observation.content_hash,
            approved_scopes={IngestionScope.PERSONALIZATION},
            approved_by="SUBJECT-1",
            approved_at=_now() - timedelta(minutes=5),
            expires_at=_now() + timedelta(hours=1),
        )

    def list_observations(self, subject_id: str, domain: str):
        return [self.observation]

    def list_transitions(self, subject_id: str, domain: str):
        return []

    def get_policy(self, policy_id: str):
        return self.policy if policy_id == self.policy.policy_id else None


def _execute_complete_transaction(root: Path):
    reader = HumanStateReader()
    interpretation = ResolveHumanStateInterpretation(reader).execute(
        subject_id="SUBJECT-1",
        domain="career",
        now=_now(),
    )
    envelope = BuildHumanStateModelUsePackage().execute(
        interpretation,
        scope=IngestionScope.PERSONALIZATION,
    )
    approvals = JsonApprovalGrantRepository(root)
    action = "model-use:personalization"
    approvals.save_new(
        ApprovalGrant(
            approval_id="APR-1",
            decision=ApprovalDecision.APPROVED,
            execution_context=ExecutionContext.TEST,
            permitted_actions={action},
            subject_id="SUBJECT-1",
            content_sha256=envelope.payload_hash,
            authorized_by="SUBJECT-1",
            authority_class="SUBJECT",
            issued_at=_now() - timedelta(minutes=1),
            expires_at=_now() + timedelta(hours=1),
        )
    )
    request = ApprovalRequest(
        execution_context=ExecutionContext.TEST,
        action=action,
        subject_id="SUBJECT-1",
        content_sha256=envelope.payload_hash,
        acceptable_authority_classes={"SUBJECT"},
        transaction_id="TX-1",
        requested_at=_now(),
    )
    receipt = ExecuteGovernedHumanStateModelUse(
        model_use_reader=reader,
        model_use_writer=JsonGovernedHumanStateModelUseWriter(root),
        approval_repository=approvals,
        event_writer=JsonWorkflowEventRecordRepository(root),
        publisher_version="test/v1",
    ).execute(
        interpretation,
        envelope,
        policy_id="POL-1",
        approval_id="APR-1",
        request=request,
        now=_now(),
    )
    return receipt


def test_complete_transaction_reconstructs_without_issues(tmp_path: Path) -> None:
    receipt = _execute_complete_transaction(tmp_path)

    report = reconstruct_model_use(tmp_path, "TX-1")

    assert report.status == ForensicStatus.COMPLETE
    assert report.reconstructable is True
    assert report.approval_consumed is True
    assert report.canonical_receipt_present is True
    assert report.generated_receipt_present is True
    assert report.output_pair_present is True
    assert report.receipt_id == receipt.receipt_id
    assert report.issues == []


def test_missing_canonical_receipt_is_incomplete_but_reconstructable(
    tmp_path: Path,
) -> None:
    receipt = _execute_complete_transaction(tmp_path)
    canonical = (
        tmp_path
        / "records"
        / "model-feedback-receipts"
        / f"{receipt.receipt_id}.json"
    )
    canonical.unlink()

    report = reconstruct_model_use(tmp_path, "TX-1")

    assert report.status == ForensicStatus.INCOMPLETE
    assert report.reconstructable is True
    assert report.canonical_receipt_present is False
    assert report.generated_receipt_present is True
    assert "canonical model-use receipt is missing" in report.issues


def test_missing_persisted_stage_is_incomplete_but_artifacts_remain_repairable(
    tmp_path: Path,
) -> None:
    _execute_complete_transaction(tmp_path)
    event_id = model_use_event_id("TX-1", ModelUseEventStage.PERSISTED)
    (tmp_path / "records" / "events" / f"{event_id}.json").unlink()

    report = reconstruct_model_use(tmp_path, "TX-1")

    assert report.status == ForensicStatus.INCOMPLETE
    assert report.reconstructable is True
    assert any("required journal stages are missing" in issue for issue in report.issues)


def test_tampered_payload_is_a_forensic_conflict(tmp_path: Path) -> None:
    receipt = _execute_complete_transaction(tmp_path)
    payload_path = (
        tmp_path
        / "generated"
        / "model-feedback"
        / receipt.receipt_id
        / "payload.json"
    )
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    payload["behavioral_instructions"]["preserve_uncertainty"] = False
    payload_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = reconstruct_model_use(tmp_path, "TX-1")

    assert report.status == ForensicStatus.CONFLICT
    assert report.reconstructable is False
    assert "generated payload hash does not match selected receipt" in report.issues


def test_generated_and_canonical_receipt_difference_is_conflict(tmp_path: Path) -> None:
    receipt = _execute_complete_transaction(tmp_path)
    generated_path = (
        tmp_path
        / "generated"
        / "model-feedback"
        / receipt.receipt_id
        / "receipt.json"
    )
    generated = json.loads(generated_path.read_text(encoding="utf-8"))
    generated["publisher_version"] = "tampered/v2"
    generated_path.write_text(
        json.dumps(generated, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = reconstruct_model_use(tmp_path, "TX-1")

    assert report.status == ForensicStatus.CONFLICT
    assert report.reconstructable is False
    assert "generated and canonical receipts differ" in report.issues
