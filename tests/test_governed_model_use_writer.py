from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from nks.adapters.governed_model_use import (
    JsonGovernedHumanStateModelUseWriter,
    ModelUseOutputConflictError,
    PartialModelUseOutputError,
)
from nks.application.human_state_model_use import (
    GovernedHumanStateModelUseReceipt,
)
from nks.domain.human_state import (
    ExpressionStrength,
    HumanStateObservation,
    IngestionScope,
    ModelFeedbackPackage,
    TemporalStatus,
)
from nks.governance.approvals import ExecutionContext


def _hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime(2026, 7, 14, 6, 0, tzinfo=timezone.utc)


def _package() -> ModelFeedbackPackage:
    observation = HumanStateObservation(
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
    return ModelFeedbackPackage(
        subject_id="SUBJECT-1",
        domain="career",
        current_observation=observation,
        historical_observations=[],
        transitions=[],
        permitted_scope=IngestionScope.PERSONALIZATION,
        behavioral_instructions={"preserve_uncertainty": True},
    )


def _receipt(*, payload_hash: str = "sha256:" + "1" * 64):
    return GovernedHumanStateModelUseReceipt(
        receipt_id="NKS-GMUR-000001",
        subject_id="SUBJECT-1",
        domain="career",
        observation_ids=["OBS-1"],
        transition_ids=[],
        policy_id="POL-1",
        approval_id="APR-1",
        execution_context=ExecutionContext.TEST,
        transaction_id="TX-1",
        destination_scope=IngestionScope.PERSONALIZATION,
        payload_hash=payload_hash,
        authorized_at=_now(),
        recorded_at=_now(),
        publisher_version="test/v1",
    )


def test_writer_commits_complete_output_and_canonical_receipt(tmp_path: Path) -> None:
    writer = JsonGovernedHumanStateModelUseWriter(tmp_path)
    package = _package()
    receipt = _receipt()

    writer.save_model_use(package, receipt)
    writer.save_model_use(package, receipt)

    output = tmp_path / "generated" / "model-feedback" / receipt.receipt_id
    canonical = tmp_path / "records" / "model-feedback-receipts" / (
        receipt.receipt_id + ".json"
    )
    assert (output / "payload.json").exists()
    assert (output / "receipt.json").exists()
    assert canonical.exists()


def test_existing_output_with_different_receipt_fails(tmp_path: Path) -> None:
    writer = JsonGovernedHumanStateModelUseWriter(tmp_path)
    package = _package()
    writer.save_model_use(package, _receipt())

    with pytest.raises(ModelUseOutputConflictError, match="receipt differs"):
        writer.save_model_use(package, _receipt(payload_hash="sha256:" + "2" * 64))


def test_partial_output_fails_closed(tmp_path: Path) -> None:
    writer = JsonGovernedHumanStateModelUseWriter(tmp_path)
    output = tmp_path / "generated" / "model-feedback" / "NKS-GMUR-000001"
    output.mkdir(parents=True)
    (output / "payload.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(PartialModelUseOutputError, match="incomplete"):
        writer.save_model_use(_package(), _receipt())


class FailCanonicalOnceWriter(JsonGovernedHumanStateModelUseWriter):
    def __init__(self, repository_root: Path) -> None:
        super().__init__(repository_root)
        self.fail_once = True

    def _commit_canonical_receipt(self, receipt) -> None:
        if self.fail_once:
            self.fail_once = False
            raise OSError("simulated canonical receipt failure")
        super()._commit_canonical_receipt(receipt)


def test_retry_recovers_canonical_receipt_from_complete_output(tmp_path: Path) -> None:
    writer = FailCanonicalOnceWriter(tmp_path)
    package = _package()
    receipt = _receipt()

    with pytest.raises(OSError, match="canonical receipt failure"):
        writer.save_model_use(package, receipt)

    output = tmp_path / "generated" / "model-feedback" / receipt.receipt_id
    canonical = tmp_path / "records" / "model-feedback-receipts" / (
        receipt.receipt_id + ".json"
    )
    assert (output / "payload.json").exists()
    assert (output / "receipt.json").exists()
    assert not canonical.exists()

    writer.save_model_use(package, receipt)

    assert canonical.exists()
