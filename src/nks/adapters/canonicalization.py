"""Filesystem persistence available only through the restricted canonical writer."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from nks.domain.canonicalization import (
    CanonicalTargetReservation,
    ReservationStatus,
)
from nks.domain.models import SourceRecord
from nks.ports.canonicalization import CanonicalStoreConflictError


class JsonCanonicalSourceStore:
    """Reserve and commit canonical source identifiers using open JSON records."""

    def __init__(self, records_root: Path) -> None:
        self._sources = records_root / "sources"
        self._reservations = records_root / "canonical-reservations"
        self._sources.mkdir(parents=True, exist_ok=True)
        self._reservations.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_id(value: str) -> str:
        return value.replace("/", "_")

    def _source_path(self, source_id: str) -> Path:
        return self._sources / f"{self._safe_id(source_id)}.json"

    def _reservation_path(self, source_id: str) -> Path:
        return self._reservations / f"{self._safe_id(source_id)}.json"

    def get(self, source_id: str) -> SourceRecord | None:
        path = self._source_path(source_id)
        if not path.exists():
            return None
        return SourceRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def get_reservation(
        self, source_id: str
    ) -> CanonicalTargetReservation | None:
        path = self._reservation_path(source_id)
        if not path.exists():
            return None
        return CanonicalTargetReservation.model_validate_json(
            path.read_text(encoding="utf-8")
        )

    def reserve(
        self, reservation: CanonicalTargetReservation
    ) -> CanonicalTargetReservation:
        path = self._reservation_path(reservation.target_source_id)
        serialized = reservation.model_dump_json(indent=2)
        try:
            with path.open("x", encoding="utf-8") as handle:
                handle.write(serialized)
            return reservation
        except FileExistsError:
            existing = CanonicalTargetReservation.model_validate_json(
                path.read_text(encoding="utf-8")
            )
            if (
                existing.target_source_id == reservation.target_source_id
                and existing.idempotency_key == reservation.idempotency_key
                and existing.authorization_id == reservation.authorization_id
                and existing.content_sha256 == reservation.content_sha256
                and existing.mode == reservation.mode
            ):
                return existing
            raise CanonicalStoreConflictError(
                f"canonical source identifier {reservation.target_source_id} is reserved"
            )

    def commit(
        self,
        reservation: CanonicalTargetReservation,
        source: SourceRecord,
    ) -> SourceRecord:
        current = self.get_reservation(reservation.target_source_id)
        if current is None:
            raise CanonicalStoreConflictError("canonical target was not reserved")
        if current.idempotency_key != reservation.idempotency_key:
            raise CanonicalStoreConflictError("reservation idempotency key changed")
        if source.id != current.target_source_id:
            raise CanonicalStoreConflictError("source does not match reserved target")
        if source.metadata.get("promotion_idempotency_key") != current.idempotency_key:
            raise CanonicalStoreConflictError(
                "source metadata does not match reserved idempotency key"
            )

        existing = self.get(source.id)
        if existing is not None:
            if (
                existing.metadata.get("promotion_idempotency_key")
                == current.idempotency_key
                and existing.metadata.get("content_sha256")
                == current.content_sha256
            ):
                return existing
            raise CanonicalStoreConflictError(
                f"canonical source identifier {source.id} already exists"
            )

        source_path = self._source_path(source.id)
        try:
            with source_path.open("x", encoding="utf-8") as handle:
                handle.write(source.model_dump_json(indent=2))
        except FileExistsError:
            existing = self.get(source.id)
            if existing is not None and (
                existing.metadata.get("promotion_idempotency_key")
                == current.idempotency_key
                and existing.metadata.get("content_sha256")
                == current.content_sha256
            ):
                return existing
            raise CanonicalStoreConflictError(
                f"canonical source identifier {source.id} already exists"
            )

        committed = current.model_copy(
            update={
                "status": ReservationStatus.COMMITTED,
                "committed_at": datetime.now(timezone.utc),
            }
        )
        reservation_path = self._reservation_path(source.id)
        temporary_path = reservation_path.with_suffix(".json.tmp")
        temporary_path.write_text(
            committed.model_dump_json(indent=2), encoding="utf-8"
        )
        temporary_path.replace(reservation_path)
        return source
