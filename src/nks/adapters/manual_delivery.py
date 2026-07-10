"""Manual publication fallback and local feedback persistence adapters."""

from __future__ import annotations

import json
from pathlib import Path

from nks.domain.delivery import (
    DeliveryStatus,
    FeedbackRecord,
    PublicationPayload,
    PublicationReceipt,
)


class ManualPublicationAdapter:
    """Creates a deterministic human-executable publication package."""

    def __init__(self, output_root: Path) -> None:
        self._output_root = output_root

    def prepare(self, payload: PublicationPayload) -> PublicationReceipt:
        package_dir = self._output_root / payload.platform / payload.publication_id
        package_dir.mkdir(parents=True, exist_ok=True)

        (package_dir / "payload.json").write_text(
            payload.model_dump_json(indent=2), encoding="utf-8"
        )
        checklist = "\n".join(
            [
                f"# Manual Publication Checklist — {payload.publication_id}",
                "",
                f"Platform: {payload.platform}",
                "",
                "- [ ] Confirm editorial readiness.",
                "- [ ] Confirm user approval is recorded.",
                "- [ ] Confirm required assets are available.",
                "- [ ] Publish the prepared payload.",
                "- [ ] Record the public URL and external platform ID.",
                "- [ ] Persist a publication receipt and workflow event.",
                "",
            ]
        )
        (package_dir / "checklist.md").write_text(checklist, encoding="utf-8")

        return PublicationReceipt(
            receipt_id=f"manual:{payload.platform}:{payload.publication_id}",
            publication_id=payload.publication_id,
            platform=payload.platform,
            status=DeliveryStatus.PREPARED,
            metadata={"package_path": str(package_dir)},
        )


class JsonFeedbackRepository:
    def __init__(self, root: Path) -> None:
        self._root = root / "feedback"
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, feedback_id: str) -> Path:
        return self._root / f"{feedback_id.replace('/', '_')}.json"

    def save(self, feedback: FeedbackRecord) -> FeedbackRecord:
        path = self._path(feedback.feedback_id)
        serialized = feedback.model_dump_json(indent=2)
        if path.exists() and path.read_text(encoding="utf-8") == serialized:
            return feedback
        path.write_text(serialized, encoding="utf-8")
        return feedback

    def get(self, feedback_id: str) -> FeedbackRecord | None:
        path = self._path(feedback_id)
        if not path.exists():
            return None
        return FeedbackRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def list_for_publication(self, publication_id: str) -> list[FeedbackRecord]:
        records: list[FeedbackRecord] = []
        for path in sorted(self._root.glob("*.json")):
            record = FeedbackRecord.model_validate_json(path.read_text(encoding="utf-8"))
            if record.publication_id == publication_id:
                records.append(record)
        return records
