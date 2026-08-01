from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from nks.adapters.canonicalization import JsonCanonicalSourceStore
from nks.domain.canonicalization import (
    CanonicalTargetReservation,
    CanonicalWriteMode,
)
from nks.domain.models import RecordStatus, SourceRecord
from nks.ports.canonicalization import CanonicalStoreConflictError

NOW = datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc)


def reservation(
    *,
    source_id: str = "NKS-SRC-000001",
    idempotency_key: str = "1" * 64,
    authorization_id: str = "NKS-AUTH-000001",
    content_sha256: str = "2" * 64,
) -> CanonicalTargetReservation:
    return CanonicalTargetReservation(
        reservation_id=f"NKS-RES-{source_id}",
        target_source_id=source_id,
        idempotency_key=idempotency_key,
        authorization_id=authorization_id,
        subject_id="NKS-FDB-000001",
        content_sha256=content_sha256,
        mode=CanonicalWriteMode.NORMAL,
        reserved_at=NOW,
    )


def source_for(
    *,
    source_id: str = "NKS-SRC-000001",
    idempotency_key: str = "1" * 64,
    content_sha256: str = "2" * 64,
) -> SourceRecord:
    return SourceRecord(
        id=source_id,
        title="Canonicalized source",
        status=RecordStatus.REVIEW,
        source_type="feedback-promotion",
        source_location=f"records/feedback/{source_id}.json",
        metadata={
            "promotion_idempotency_key": idempotency_key,
            "content_sha256": content_sha256,
        },
    )


def test_reserve_is_idempotent_for_matching_existing_reservation(tmp_path: Path):
    store = JsonCanonicalSourceStore(tmp_path / "records")
    first = reservation(source_id="NKS-SRC-000010")

    created = store.reserve(first)
    replayed = store.reserve(first)

    assert created == first
    assert replayed == first


def test_reserve_rejects_conflicting_existing_reservation(tmp_path: Path):
    store = JsonCanonicalSourceStore(tmp_path / "records")
    original = reservation(source_id="NKS-SRC-000011")
    conflicting = reservation(
        source_id="NKS-SRC-000011",
        authorization_id="NKS-AUTH-000099",
    )
    store.reserve(original)

    with pytest.raises(CanonicalStoreConflictError, match="is reserved"):
        store.reserve(conflicting)


def test_commit_rejects_missing_or_mismatched_reservation_state(tmp_path: Path):
    store = JsonCanonicalSourceStore(tmp_path / "records")
    reserved = reservation(source_id="NKS-SRC-000012")
    store.reserve(reserved)

    with pytest.raises(CanonicalStoreConflictError, match="was not reserved"):
        store.commit(reservation(source_id="NKS-SRC-UNRESERVED"), source_for(source_id="NKS-SRC-UNRESERVED"))

    with pytest.raises(CanonicalStoreConflictError, match="idempotency key changed"):
        store.commit(
            reservation(source_id="NKS-SRC-000012", idempotency_key="3" * 64),
            source_for(source_id="NKS-SRC-000012", idempotency_key="1" * 64),
        )

    with pytest.raises(CanonicalStoreConflictError, match="does not match reserved target"):
        store.commit(
            reserved,
            source_for(source_id="NKS-SRC-000099", idempotency_key="1" * 64),
        )

    with pytest.raises(
        CanonicalStoreConflictError,
        match="metadata does not match reserved idempotency key",
    ):
        store.commit(
            reserved,
            source_for(source_id="NKS-SRC-000012", idempotency_key="f" * 64),
        )


def test_commit_rejects_existing_source_with_conflicting_hash(tmp_path: Path):
    store = JsonCanonicalSourceStore(tmp_path / "records")
    reserved = reservation(source_id="NKS-SRC-000013")
    store.reserve(reserved)

    existing = source_for(
        source_id="NKS-SRC-000013",
        idempotency_key=reserved.idempotency_key,
        content_sha256="f" * 64,
    )
    store._source_path(existing.id).write_text(
        existing.model_dump_json(indent=2), encoding="utf-8"
    )

    with pytest.raises(CanonicalStoreConflictError, match="already exists"):
        store.commit(reserved, source_for(source_id="NKS-SRC-000013"))


def test_commit_allows_race_when_file_exists_with_same_source(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    store = JsonCanonicalSourceStore(tmp_path / "records")
    reserved = reservation(source_id="NKS-SRC-000014")
    store.reserve(reserved)
    source = source_for(source_id="NKS-SRC-000014")

    class _RacePath:
        def open(self, *args, **kwargs):  # pragma: no cover - behavior is the exception path itself
            raise FileExistsError

    matching = source_for(source_id="NKS-SRC-000014")
    call_count = {"get": 0}

    def fake_get(source_id: str):
        if source_id != "NKS-SRC-000014":
            return None
        call_count["get"] += 1
        if call_count["get"] == 1:
            return None
        return matching

    monkeypatch.setattr(store, "_source_path", lambda _source_id: _RacePath())
    monkeypatch.setattr(store, "get", fake_get)

    committed = store.commit(reserved, source)

    assert committed == matching


def test_commit_rejects_race_when_file_exists_with_conflicting_source(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    store = JsonCanonicalSourceStore(tmp_path / "records")
    reserved = reservation(source_id="NKS-SRC-000015")
    store.reserve(reserved)
    source = source_for(source_id="NKS-SRC-000015")

    class _RacePath:
        def open(self, *args, **kwargs):  # pragma: no cover - behavior is the exception path itself
            raise FileExistsError

    conflicting = source_for(
        source_id="NKS-SRC-000015",
        idempotency_key="a" * 64,
        content_sha256="b" * 64,
    )
    call_count = {"get": 0}

    def fake_get(source_id: str):
        if source_id != "NKS-SRC-000015":
            return None
        call_count["get"] += 1
        if call_count["get"] == 1:
            return None
        return conflicting

    monkeypatch.setattr(store, "_source_path", lambda _source_id: _RacePath())
    monkeypatch.setattr(store, "get", fake_get)

    with pytest.raises(CanonicalStoreConflictError, match="already exists"):
        store.commit(reserved, source)


def test_reserve_rejects_malformed_existing_reservation(tmp_path: Path):
    store = JsonCanonicalSourceStore(tmp_path / "records")
    reservation_path = store._reservation_path("NKS-SRC-000016")
    reservation_path.write_text("{not-valid-json", encoding="utf-8")

    with pytest.raises(CanonicalStoreConflictError, match="invalid reservation"):
        store.reserve(reservation(source_id="NKS-SRC-000016"))
