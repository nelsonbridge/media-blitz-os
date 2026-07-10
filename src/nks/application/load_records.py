"""Load canonical NKS records from a portable filesystem store."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from nks.domain.models import CanonicalRecord

RecordT = TypeVar("RecordT", bound=CanonicalRecord)


def canonical_record_path(root: Path, collection: str, record_id: str) -> Path:
    primary = root / collection / f"{record_id}.json"
    if primary.exists():
        return primary
    alternate = root / "canonical" / collection / f"{record_id}.json"
    return alternate


def load_record(root: Path, collection: str, record_id: str, record_type: type[RecordT]) -> RecordT:
    path = canonical_record_path(root, collection, record_id)
    if not path.exists():
        raise FileNotFoundError(f"canonical record not found: {path}")
    return record_type.model_validate_json(path.read_text(encoding="utf-8"))
