"""Load canonical NKS records from a portable filesystem store."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from nks.domain.models import CanonicalRecord

RecordT = TypeVar("RecordT", bound=CanonicalRecord)


def load_record(root: Path, collection: str, record_id: str, record_type: type[RecordT]) -> RecordT:
    path = root / collection / f"{record_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"canonical record not found: {path}")
    return record_type.model_validate_json(path.read_text(encoding="utf-8"))
