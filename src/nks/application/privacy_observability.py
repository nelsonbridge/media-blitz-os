"""Privacy-preserving local observability for Enki TEST execution.

Telemetry records operational facts, hashes, bounded labels, and correlation
identifiers. It never accepts canonical payloads, human-state content, secrets,
credentials, or unauthorized boundary identifiers as telemetry metadata.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryContext


_SECRET_PATTERN = re.compile(
    r"(?i)(sk-[a-z0-9_-]{12,}|gh[pousr]_[a-z0-9]{12,}|aws[_-]?secret|password\s*[:=]|private[_ -]?key|bearer\s+[a-z0-9._-]+)"
)
_ALLOWED_METADATA_KEYS = {
    "operation_family",
    "terminal_state",
    "reason_code",
    "error_type",
    "retry_count",
    "duration_bucket",
    "record_count_bucket",
    "adapter_kind",
    "policy_version",
    "schema_version",
}
_FORBIDDEN_KEY_PARTS = {
    "content",
    "payload",
    "statement",
    "human",
    "name",
    "email",
    "address",
    "phone",
    "secret",
    "token",
    "password",
    "credential",
    "key_material",
}


class TelemetryKind(StrEnum):
    HEALTH = "HEALTH"
    METRIC = "METRIC"
    TRACE = "TRACE"
    DIAGNOSTIC = "DIAGNOSTIC"


class TelemetryStatus(StrEnum):
    OK = "OK"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    DENIED = "DENIED"


class CorrelationContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    correlation_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
    operation_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
    transaction_id: str | None = Field(
        default=None,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$",
    )
    boundary_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    execution_context: ExecutionContext

    @classmethod
    def from_boundary(
        cls,
        boundary: BoundaryContext,
        *,
        correlation_id: str,
        operation_id: str,
        transaction_id: str | None = None,
    ) -> "CorrelationContext":
        return cls(
            correlation_id=correlation_id,
            operation_id=operation_id,
            transaction_id=transaction_id,
            boundary_sha256=boundary.boundary_sha256,
            execution_context=boundary.execution_context,
        )


class TelemetryEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    kind: TelemetryKind
    status: TelemetryStatus
    correlation: CorrelationContext
    metric_name: str | None = Field(default=None, max_length=64)
    metric_value: float | int | None = None
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)
    occurred_at: datetime
    event_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_privacy_and_hash(self) -> "TelemetryEvent":
        if self.correlation.execution_context != ExecutionContext.TEST:
            raise ValueError("Sprint 18 telemetry is TEST-only")
        if len(self.metadata) > 12:
            raise ValueError("telemetry metadata exceeds bounded field count")
        for key, value in self.metadata.items():
            normalized = key.lower()
            if key not in _ALLOWED_METADATA_KEYS:
                raise ValueError(f"telemetry metadata key is not allowed: {key}")
            if any(part in normalized for part in _FORBIDDEN_KEY_PARTS):
                raise ValueError("protected telemetry metadata key is forbidden")
            rendered = str(value)
            if len(rendered) > 128:
                raise ValueError("telemetry metadata value exceeds length boundary")
            if _SECRET_PATTERN.search(rendered):
                raise ValueError("secret-like telemetry metadata is forbidden")
        if self.metric_name is not None:
            if _SECRET_PATTERN.search(self.metric_name):
                raise ValueError("secret-like metric name is forbidden")
        if self.kind == TelemetryKind.METRIC:
            if self.metric_name is None or self.metric_value is None:
                raise ValueError("metric telemetry requires name and value")
        elif self.metric_name is not None or self.metric_value is not None:
            raise ValueError("non-metric telemetry cannot carry metric values")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"event_sha256"}))
        if self.event_sha256 != expected:
            raise ValueError("telemetry event hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "TelemetryEvent":
        payload = dict(values)
        payload["event_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class TelemetryFindingKind(StrEnum):
    LOSS = "LOSS"
    DUPLICATE = "DUPLICATE"
    CORRELATION_BREAK = "CORRELATION_BREAK"
    HASH_CONFLICT = "HASH_CONFLICT"


class TelemetryFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    finding_id: str
    kind: TelemetryFindingKind
    correlation_id_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    affected_sequences: list[int]
    evidence_event_hashes: list[str]
    finding_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "TelemetryFinding":
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"finding_sha256"}))
        if self.finding_sha256 != expected:
            raise ValueError("telemetry finding hash is invalid")
        return self


class IncidentReconstruction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: str
    correlation_id_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    ordered_event_hashes: list[str]
    statuses: dict[str, int]
    findings: list[TelemetryFinding]
    protected_payload_included: bool = False
    reconstruction_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_reconstruction(self) -> "IncidentReconstruction":
        if self.protected_payload_included:
            raise ValueError("incident reconstruction cannot include protected payload")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"reconstruction_sha256"})
        )
        if self.reconstruction_sha256 != expected:
            raise ValueError("incident reconstruction hash is invalid")
        return self


class PrivacyTelemetryCollector:
    """Append-only in-memory TEST collector with deterministic integrity checks."""

    def __init__(self) -> None:
        self._events: list[TelemetryEvent] = []

    @property
    def events(self) -> tuple[TelemetryEvent, ...]:
        return tuple(self._events)

    def append(self, event: TelemetryEvent) -> TelemetryEvent:
        existing = [item for item in self._events if item.event_id == event.event_id]
        if existing:
            if existing[0] == event:
                return existing[0]
            raise ValueError("telemetry event identity conflict")
        self._events.append(event)
        return event

    def findings(self) -> list[TelemetryFinding]:
        findings: list[TelemetryFinding] = []
        grouped: dict[str, list[TelemetryEvent]] = defaultdict(list)
        for event in self._events:
            grouped[event.correlation.correlation_id].append(event)

        for correlation_id, events in sorted(grouped.items()):
            by_sequence: dict[int, list[TelemetryEvent]] = defaultdict(list)
            for event in events:
                by_sequence[event.sequence].append(event)
            sequences = sorted(by_sequence)
            if sequences:
                missing = sorted(set(range(1, max(sequences) + 1)) - set(sequences))
                if missing:
                    findings.append(
                        self._finding(
                            kind=TelemetryFindingKind.LOSS,
                            correlation_id=correlation_id,
                            sequences=missing,
                            evidence=events,
                        )
                    )
            duplicates = sorted(sequence for sequence, items in by_sequence.items() if len(items) > 1)
            if duplicates:
                conflicting = any(
                    len({item.event_sha256 for item in by_sequence[sequence]}) > 1
                    for sequence in duplicates
                )
                findings.append(
                    self._finding(
                        kind=(
                            TelemetryFindingKind.HASH_CONFLICT
                            if conflicting
                            else TelemetryFindingKind.DUPLICATE
                        ),
                        correlation_id=correlation_id,
                        sequences=duplicates,
                        evidence=events,
                    )
                )
            operation_ids = {event.correlation.operation_id for event in events}
            boundary_hashes = {event.correlation.boundary_sha256 for event in events}
            contexts = {event.correlation.execution_context for event in events}
            if len(operation_ids) > 1 or len(boundary_hashes) > 1 or len(contexts) > 1:
                findings.append(
                    self._finding(
                        kind=TelemetryFindingKind.CORRELATION_BREAK,
                        correlation_id=correlation_id,
                        sequences=sequences,
                        evidence=events,
                    )
                )
        return findings

    @staticmethod
    def _finding(
        *,
        kind: TelemetryFindingKind,
        correlation_id: str,
        sequences: list[int],
        evidence: list[TelemetryEvent],
    ) -> TelemetryFinding:
        payload = {
            "finding_id": f"TEL-{kind.value}-{canonical_sha256(correlation_id)[7:23]}",
            "kind": kind,
            "correlation_id_sha256": canonical_sha256(correlation_id),
            "affected_sequences": sequences,
            "evidence_event_hashes": sorted(event.event_sha256 for event in evidence),
        }
        return TelemetryFinding(**payload, finding_sha256=canonical_sha256(payload))

    def reconstruct(self, correlation_id: str) -> IncidentReconstruction:
        events = sorted(
            [event for event in self._events if event.correlation.correlation_id == correlation_id],
            key=lambda event: (event.sequence, event.event_id),
        )
        if not events:
            raise ValueError("correlation identifier has no telemetry evidence")
        relevant_findings = [
            finding
            for finding in self.findings()
            if finding.correlation_id_sha256 == canonical_sha256(correlation_id)
        ]
        status_counts = Counter(event.status.value for event in events)
        payload = {
            "incident_id": f"INC-{canonical_sha256(correlation_id)[7:23]}",
            "correlation_id_sha256": canonical_sha256(correlation_id),
            "ordered_event_hashes": [event.event_sha256 for event in events],
            "statuses": dict(sorted(status_counts.items())),
            "findings": relevant_findings,
            "protected_payload_included": False,
        }
        return IncidentReconstruction(
            **payload,
            reconstruction_sha256=canonical_sha256(payload),
        )


def assert_telemetry_safe_serialization(events: list[TelemetryEvent]) -> None:
    """Fail when rendered telemetry contains recognizable protected markers."""

    rendered = "\n".join(event.model_dump_json() for event in events)
    if _SECRET_PATTERN.search(rendered):
        raise ValueError("telemetry serialization contains secret-like material")
    forbidden_literals = ["@", "BEGIN PRIVATE KEY", "sk-", "ghp_"]
    if any(literal in rendered for literal in forbidden_literals):
        raise ValueError("telemetry serialization contains protected literal")
