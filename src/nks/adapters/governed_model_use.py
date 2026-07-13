"""Recoverable filesystem persistence for governed human-state model use."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel

from nks.application.human_state_model_use import (
    GovernedHumanStateModelUseReceipt,
)
from nks.domain.human_state import ModelFeedbackPackage


class ModelUseOutputConflictError(RuntimeError):
    """Raised when immutable model-use output differs under an existing id."""


class PartialModelUseOutputError(RuntimeError):
    """Raised when a model-use output directory is incomplete."""


class JsonGovernedHumanStateModelUseWriter:
    """Write complete output first, then its canonical receipt.

    If execution stops after the generated payload/receipt pair is committed but
    before the canonical receipt is written, an exact retry validates the pair
    and completes the canonical record. This direction is recoverable because
    the generated receipt contains the complete canonical receipt payload.
    """

    def __init__(self, repository_root: Path) -> None:
        self._root = repository_root
        self._output_root = repository_root / "generated" / "model-feedback"
        self._receipt_root = repository_root / "records" / "model-feedback-receipts"
        self._output_root.mkdir(parents=True, exist_ok=True)
        self._receipt_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_identifier(value: str) -> str:
        return value.replace("/", "_").replace("\\", "_")

    @staticmethod
    def _serialize(record: BaseModel) -> str:
        payload = record.model_dump(mode="json", exclude_none=False)
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"

    @staticmethod
    def _write_durable(path: Path, content: str) -> None:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

    def _output_directory(self, receipt_id: str) -> Path:
        return self._output_root / self._safe_identifier(receipt_id)

    def _receipt_path(self, receipt_id: str) -> Path:
        return self._receipt_root / f"{self._safe_identifier(receipt_id)}.json"

    def _validate_existing_output(
        self,
        output: Path,
        package_content: str,
        receipt_content: str,
    ) -> None:
        payload_path = output / "payload.json"
        receipt_path = output / "receipt.json"
        if not payload_path.exists() or not receipt_path.exists():
            raise PartialModelUseOutputError(
                f"incomplete generated model-use output: {output.relative_to(self._root)}"
            )
        if payload_path.read_text(encoding="utf-8") != package_content:
            raise ModelUseOutputConflictError("existing model-use payload differs")
        if receipt_path.read_text(encoding="utf-8") != receipt_content:
            raise ModelUseOutputConflictError("existing model-use receipt differs")

    def _commit_output(
        self,
        package: ModelFeedbackPackage,
        receipt: GovernedHumanStateModelUseReceipt,
    ) -> None:
        output = self._output_directory(receipt.receipt_id)
        package_content = self._serialize(package)
        receipt_content = self._serialize(receipt)
        if output.exists():
            self._validate_existing_output(output, package_content, receipt_content)
            return

        temp = self._output_root / (
            f".{self._safe_identifier(receipt.receipt_id)}.{uuid4().hex}.tmp"
        )
        try:
            temp.mkdir()
            self._write_durable(temp / "payload.json", package_content)
            self._write_durable(temp / "receipt.json", receipt_content)
            os.replace(temp, output)
        finally:
            if temp.exists():
                shutil.rmtree(temp)

    def _commit_canonical_receipt(
        self,
        receipt: GovernedHumanStateModelUseReceipt,
    ) -> None:
        path = self._receipt_path(receipt.receipt_id)
        content = self._serialize(receipt)
        if path.exists():
            if path.read_text(encoding="utf-8") == content:
                return
            raise ModelUseOutputConflictError(
                f"canonical model-use receipt differs: {receipt.receipt_id}"
            )
        self._write_durable(path, content)

    def save_model_use(
        self,
        package: ModelFeedbackPackage,
        receipt: GovernedHumanStateModelUseReceipt,
    ) -> None:
        self._commit_output(package, receipt)
        self._commit_canonical_receipt(receipt)
