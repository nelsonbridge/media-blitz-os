"""Canonical temporal-authority contracts for Enki.

This module keeps historical truth distinct from current authority.  Records are
immutable historical facts; authority is resolved as-of explicit effective and
valid-time coordinates rather than by rewriting prior records.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from enum import StrEnum
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256


class TemporalAuthorityDisposition(StrEnum):
    """Declared terminal/current disposition of one immutable record."""

    ACTIVE = "ACTIVE"
    HISTORICAL = "HISTORICAL"
    SUPERSEDED = "SUPERSEDED"
    REVOKED = "REVOKED"
    CONSUMED = "CONSUMED"
    RETRACTED = "RETRACTED"


class TemporalAuthorityConflict(ValueError):
    """Raised when more than one record claims the same current authority."""


class TemporalAuthorityEnvelope(BaseModel):
    """Immutable temporal and authority metadata shared by governed records."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    authority_class: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    schema_version: str = Field(min_length=1)

    recorded_at: datetime
    effective_from: datetime
    effective_to: datetime | None = None
    authority_valid_from: datetime
    authority_valid_to: datetime | None = None

    superseded_at: datetime | None = None
    revoked_at: datetime | None = None
    consumed_at: datetime | None = None
    retracted_at: datetime | None = None

    supersedes_record_id: str | None = None
    lineage_parent_ids: tuple[str, ...] = ()
    disposition: TemporalAuthorityDisposition = TemporalAuthorityDisposition.ACTIVE

    @model_validator(mode="after")
    def validate_temporal_semantics(self) -> "TemporalAuthorityEnvelope":
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot precede effective_from")
        if (
            self.authority_valid_to is not None
            and self.authority_valid_to < self.authority_valid_from
        ):
            raise ValueError("authority_valid_to cannot precede authority_valid_from")

        terminal_fields = {
            "superseded_at": self.superseded_at,
            "revoked_at": self.revoked_at,
            "consumed_at": self.consumed_at,
            "retracted_at": self.retracted_at,
        }
        for name, value in terminal_fields.items():
            if value is not None and value < self.recorded_at:
                raise ValueError(f"{name} cannot precede recorded_at")
            if value is not None and value < self.authority_valid_from:
                raise ValueError(f"{name} cannot precede authority_valid_from")

        required_terminal = {
            TemporalAuthorityDisposition.SUPERSEDED: ("superseded_at", self.superseded_at),
            TemporalAuthorityDisposition.REVOKED: ("revoked_at", self.revoked_at),
            TemporalAuthorityDisposition.CONSUMED: ("consumed_at", self.consumed_at),
            TemporalAuthorityDisposition.RETRACTED: ("retracted_at", self.retracted_at),
        }
        requirement = required_terminal.get(self.disposition)
        if requirement is not None and requirement[1] is None:
            raise ValueError(
                f"{self.disposition.value} disposition requires {requirement[0]}"
            )

        terminal_times = [value for value in terminal_fields.values() if value is not None]
        if len(terminal_times) > 1 and len(set(terminal_times)) != 1:
            raise ValueError("competing terminal timestamps are ambiguous")

        if self.supersedes_record_id == self.record_id:
            raise ValueError("a record cannot supersede itself")
        if self.record_id in self.lineage_parent_ids:
            raise ValueError("a record cannot be its own lineage parent")
        if len(self.lineage_parent_ids) != len(set(self.lineage_parent_ids)):
            raise ValueError("lineage parent ids must be unique")

        if self.authority_valid_to is not None and terminal_times:
            terminal = terminal_times[0]
            if self.authority_valid_to != terminal:
                raise ValueError(
                    "authority_valid_to must equal the declared terminal timestamp"
                )
        return self

    @property
    def authority_key(self) -> tuple[str, str, str]:
        return (self.subject_id, self.domain, self.authority_class)

    @property
    def envelope_hash(self) -> str:
        return canonical_sha256(self)

    def is_effective_at(self, at: datetime) -> bool:
        return self.effective_from <= at and (
            self.effective_to is None or at < self.effective_to
        )

    def is_authoritative_at(self, at: datetime) -> bool:
        if self.disposition != TemporalAuthorityDisposition.ACTIVE:
            return False
        return self.authority_valid_from <= at and (
            self.authority_valid_to is None or at < self.authority_valid_to
        )

    def governs(self, *, effective_at: datetime, authority_at: datetime) -> bool:
        return self.is_effective_at(effective_at) and self.is_authoritative_at(authority_at)


class TemporalAuthorityResolution(BaseModel):
    """Explicit result separating current authority from preserved history."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    effective_at: datetime
    authority_at: datetime
    current_record_ids: tuple[str, ...]
    historical_record_ids: tuple[str, ...]
    resolution_hash: str


class LegacyTemporalRecord(BaseModel):
    """Minimal legacy timing shape accepted by governed migration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    authority_class: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    observed_at: datetime
    effective_from: datetime
    effective_to: datetime | None = None
    status: TemporalAuthorityDisposition
    supersedes_record_id: str | None = None


class TemporalAuthorityTimeline:
    """Validated immutable history with deterministic as-of authority resolution."""

    def __init__(self, records: Iterable[TemporalAuthorityEnvelope]) -> None:
        self._records = tuple(records)
        self._validate_history()

    @property
    def records(self) -> tuple[TemporalAuthorityEnvelope, ...]:
        return self._records

    @property
    def timeline_hash(self) -> str:
        ordered = sorted(self._records, key=lambda item: item.record_id)
        return canonical_sha256(ordered)

    def _validate_history(self) -> None:
        by_id = {record.record_id: record for record in self._records}
        if len(by_id) != len(self._records):
            raise ValueError("record ids must be unique")

        for record in self._records:
            predecessor_id = record.supersedes_record_id
            if predecessor_id is None:
                continue
            predecessor = by_id.get(predecessor_id)
            if predecessor is None:
                raise ValueError("supersedes_record_id must reference an existing record")
            if predecessor.authority_key != record.authority_key:
                raise ValueError("supersession cannot cross an authority key")
            if predecessor.superseded_at is None:
                raise ValueError("superseded predecessor must record superseded_at")
            if predecessor.authority_valid_to != predecessor.superseded_at:
                raise ValueError("superseded predecessor authority window is inconsistent")
            if record.authority_valid_from != predecessor.superseded_at:
                raise ValueError("successor authority must begin at predecessor supersession")

        for record in self._records:
            seen: set[str] = set()
            cursor = record
            while cursor.supersedes_record_id is not None:
                if cursor.record_id in seen:
                    raise ValueError("supersession cycle detected")
                seen.add(cursor.record_id)
                cursor = by_id[cursor.supersedes_record_id]

    def resolve(
        self, *, effective_at: datetime, authority_at: datetime
    ) -> TemporalAuthorityResolution:
        by_key: dict[tuple[str, str, str], list[TemporalAuthorityEnvelope]] = defaultdict(list)
        for record in self._records:
            if record.governs(effective_at=effective_at, authority_at=authority_at):
                by_key[record.authority_key].append(record)

        conflicts = {
            key: sorted(item.record_id for item in records)
            for key, records in by_key.items()
            if len(records) > 1
        }
        if conflicts:
            raise TemporalAuthorityConflict(
                "ambiguous current authority: "
                + "; ".join(
                    f"{'/'.join(key)}={','.join(ids)}"
                    for key, ids in sorted(conflicts.items())
                )
            )

        current_ids = tuple(
            sorted(record.record_id for records in by_key.values() for record in records)
        )
        current_set = set(current_ids)
        historical_ids = tuple(
            sorted(record.record_id for record in self._records if record.record_id not in current_set)
        )
        payload = {
            "effective_at": effective_at,
            "authority_at": authority_at,
            "current_record_ids": current_ids,
            "historical_record_ids": historical_ids,
            "timeline_hash": self.timeline_hash,
        }
        return TemporalAuthorityResolution(
            effective_at=effective_at,
            authority_at=authority_at,
            current_record_ids=current_ids,
            historical_record_ids=historical_ids,
            resolution_hash=canonical_sha256(payload),
        )


def migrate_legacy_temporal_record(
    legacy: LegacyTemporalRecord,
    *,
    schema_version: str,
    terminal_at: datetime | None = None,
    lineage_parent_ids: tuple[str, ...] = (),
) -> TemporalAuthorityEnvelope:
    """Migrate legacy timing without inventing missing terminal authority evidence."""

    terminal_required = legacy.status in {
        TemporalAuthorityDisposition.SUPERSEDED,
        TemporalAuthorityDisposition.REVOKED,
        TemporalAuthorityDisposition.CONSUMED,
        TemporalAuthorityDisposition.RETRACTED,
    }
    if terminal_required and terminal_at is None:
        raise ValueError("terminal_at is required for terminal legacy dispositions")
    if not terminal_required and terminal_at is not None:
        raise ValueError("terminal_at is unsupported for nonterminal legacy dispositions")

    kwargs: dict[str, datetime | None] = {
        "superseded_at": None,
        "revoked_at": None,
        "consumed_at": None,
        "retracted_at": None,
    }
    if legacy.status == TemporalAuthorityDisposition.SUPERSEDED:
        kwargs["superseded_at"] = terminal_at
    elif legacy.status == TemporalAuthorityDisposition.REVOKED:
        kwargs["revoked_at"] = terminal_at
    elif legacy.status == TemporalAuthorityDisposition.CONSUMED:
        kwargs["consumed_at"] = terminal_at
    elif legacy.status == TemporalAuthorityDisposition.RETRACTED:
        kwargs["retracted_at"] = terminal_at

    return TemporalAuthorityEnvelope(
        record_id=legacy.record_id,
        subject_id=legacy.subject_id,
        domain=legacy.domain,
        authority_class=legacy.authority_class,
        content_hash=legacy.content_hash,
        schema_version=schema_version,
        recorded_at=legacy.observed_at,
        effective_from=legacy.effective_from,
        effective_to=legacy.effective_to,
        authority_valid_from=legacy.observed_at,
        authority_valid_to=terminal_at,
        supersedes_record_id=legacy.supersedes_record_id,
        lineage_parent_ids=lineage_parent_ids,
        disposition=legacy.status,
        **kwargs,
    )
