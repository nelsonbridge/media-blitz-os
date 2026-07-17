"""Production-shaped, privacy-preserving operational observability for Enki TEST.

The service analyzes bounded telemetry and hash-only lineage. It can detect operational
and telemetry-integrity conditions and reconstruct incidents, but it has no canonical
writer and cannot authorize recovery or production effects.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.application.privacy_observability import (
    IncidentReconstruction,
    PrivacyTelemetryCollector,
    TelemetryEvent,
    TelemetryFinding,
    TelemetryStatus,
    assert_telemetry_safe_serialization,
)
from nks.governance.approvals import ExecutionContext


class OperationalSignal(StrEnum):
    QUEUE_PRESSURE = "QUEUE_PRESSURE"
    SATURATION = "SATURATION"
    HIGH_LATENCY = "HIGH_LATENCY"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    RECOVERY = "RECOVERY"
    PROVIDER_DEGRADATION = "PROVIDER_DEGRADATION"
    TELEMETRY_INTEGRITY = "TELEMETRY_INTEGRITY"


class OperationalSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class HealthLevel(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


class OperationalThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    queue_depth_warning: int = Field(default=10, ge=1)
    saturation_warning_pct: float = Field(default=80.0, ge=0.0, le=100.0)
    latency_warning_ms: float = Field(default=500.0, ge=0.0)


class IncidentLineage(BaseModel):
    """Hash-only lineage required to explain an incident without protected payload."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_id: str = Field(min_length=1)
    authority_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    evidence_sha256: tuple[str, ...] = Field(min_length=1)
    recovery_sha256: tuple[str, ...] = ()
    lineage_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "IncidentLineage":
        for value in (*self.evidence_sha256, *self.recovery_sha256):
            if not value.startswith("sha256:") or len(value) != 71:
                raise ValueError("incident lineage references must be sha256 values")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"lineage_sha256"})
        )
        if self.lineage_sha256 != expected:
            raise ValueError("incident lineage hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "IncidentLineage":
        payload = dict(values)
        payload["lineage_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class OperationalAlert(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    alert_id: str = Field(min_length=1)
    signal: OperationalSignal
    severity: OperationalSeverity
    correlation_id_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    evidence_event_hashes: tuple[str, ...] = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    alert_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "OperationalAlert":
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"alert_sha256"}))
        if self.alert_sha256 != expected:
            raise ValueError("operational alert hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "OperationalAlert":
        payload = dict(values)
        payload["alert_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class OperationalIncident(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: str
    correlation_id_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    telemetry_reconstruction_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    lineage_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    alert_sha256: tuple[str, ...]
    telemetry_finding_sha256: tuple[str, ...]
    canonical_mutation: bool = False
    recovery_authorized: bool = False
    protected_payload_included: bool = False
    incident_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_safety_and_hash(self) -> "OperationalIncident":
        if self.canonical_mutation:
            raise ValueError("observability cannot mutate canonical state")
        if self.recovery_authorized:
            raise ValueError("observability cannot authorize recovery effects")
        if self.protected_payload_included:
            raise ValueError("operational incident cannot include protected payload")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"incident_sha256"}))
        if self.incident_sha256 != expected:
            raise ValueError("operational incident hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "OperationalIncident":
        payload = dict(values)
        payload["incident_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class OperationalHealthReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    execution_context: ExecutionContext
    level: HealthLevel
    event_count: int = Field(ge=0)
    correlation_count: int = Field(ge=0)
    status_counts: dict[str, int]
    signal_counts: dict[str, int]
    incident_sha256: tuple[str, ...]
    canonical_mutation: bool = False
    recovery_authorized: bool = False
    report_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_report(self) -> "OperationalHealthReport":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("Sprint 46 operational report is TEST-only")
        if self.canonical_mutation or self.recovery_authorized:
            raise ValueError("operational report cannot mutate state or authorize recovery")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"report_sha256"}))
        if self.report_sha256 != expected:
            raise ValueError("operational health report hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "OperationalHealthReport":
        payload = dict(values)
        payload["report_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class OperationalObservabilityService:
    """Read-only analysis over privacy-safe telemetry and hash-only lineage."""

    def __init__(
        self,
        *,
        collector: PrivacyTelemetryCollector,
        lineage_by_correlation: dict[str, IncidentLineage],
        thresholds: OperationalThresholds | None = None,
    ) -> None:
        self._collector = collector
        self._lineage = dict(lineage_by_correlation)
        self._thresholds = thresholds or OperationalThresholds()

    @staticmethod
    def _alert(
        *,
        signal: OperationalSignal,
        severity: OperationalSeverity,
        correlation_id: str,
        events: list[TelemetryEvent],
        reason_code: str,
    ) -> OperationalAlert:
        correlation_hash = canonical_sha256(correlation_id)
        payload = {
            "alert_id": f"ALERT-{signal.value}-{correlation_hash[7:23]}",
            "signal": signal,
            "severity": severity,
            "correlation_id_sha256": correlation_hash,
            "evidence_event_hashes": tuple(sorted(item.event_sha256 for item in events)),
            "reason_code": reason_code,
        }
        return OperationalAlert.create(**payload)

    def _alerts_for(self, correlation_id: str, events: list[TelemetryEvent]) -> list[OperationalAlert]:
        alerts: dict[OperationalSignal, OperationalAlert] = {}

        def add(signal: OperationalSignal, severity: OperationalSeverity, reason: str) -> None:
            alerts.setdefault(
                signal,
                self._alert(
                    signal=signal,
                    severity=severity,
                    correlation_id=correlation_id,
                    events=events,
                    reason_code=reason,
                ),
            )

        for event in events:
            if event.status == TelemetryStatus.FAILED:
                add(OperationalSignal.FAILURE, OperationalSeverity.CRITICAL, "FAILED_TELEMETRY_STATUS")
            if event.status == TelemetryStatus.DEGRADED and event.metadata.get("reason_code") == "PROVIDER_DEGRADED":
                add(
                    OperationalSignal.PROVIDER_DEGRADATION,
                    OperationalSeverity.WARNING,
                    "PROVIDER_DEGRADED",
                )
            retry_count = event.metadata.get("retry_count", 0)
            if isinstance(retry_count, (int, float)) and retry_count > 0:
                add(OperationalSignal.RETRY, OperationalSeverity.WARNING, "RETRY_OBSERVED")
            if event.metadata.get("terminal_state") == "RECOVERED":
                add(OperationalSignal.RECOVERY, OperationalSeverity.INFO, "RECOVERY_OBSERVED")
            if event.metric_name == "queue_depth" and event.metric_value is not None:
                if float(event.metric_value) >= self._thresholds.queue_depth_warning:
                    add(OperationalSignal.QUEUE_PRESSURE, OperationalSeverity.WARNING, "QUEUE_THRESHOLD")
            if event.metric_name == "saturation_pct" and event.metric_value is not None:
                if float(event.metric_value) >= self._thresholds.saturation_warning_pct:
                    add(OperationalSignal.SATURATION, OperationalSeverity.WARNING, "SATURATION_THRESHOLD")
            if event.metric_name == "latency_ms" and event.metric_value is not None:
                if float(event.metric_value) >= self._thresholds.latency_warning_ms:
                    add(OperationalSignal.HIGH_LATENCY, OperationalSeverity.WARNING, "LATENCY_THRESHOLD")
        return sorted(alerts.values(), key=lambda item: item.signal.value)

    def analyze(
        self,
    ) -> tuple[OperationalHealthReport, tuple[OperationalIncident, ...]]:
        events = list(self._collector.events)
        assert_telemetry_safe_serialization(events)
        if any(event.correlation.execution_context != ExecutionContext.TEST for event in events):
            raise ValueError("operational analysis cannot consume non-TEST telemetry")

        grouped: dict[str, list[TelemetryEvent]] = defaultdict(list)
        for event in events:
            grouped[event.correlation.correlation_id].append(event)

        findings = self._collector.findings()
        findings_by_correlation: dict[str, list[TelemetryFinding]] = defaultdict(list)
        for finding in findings:
            findings_by_correlation[finding.correlation_id_sha256].append(finding)

        incidents: list[OperationalIncident] = []
        all_alerts: list[OperationalAlert] = []
        for correlation_id, correlated_events in sorted(grouped.items()):
            reconstruction: IncidentReconstruction = self._collector.reconstruct(correlation_id)
            alerts = self._alerts_for(correlation_id, correlated_events)
            related_findings = findings_by_correlation[canonical_sha256(correlation_id)]
            if related_findings:
                alerts.append(
                    self._alert(
                        signal=OperationalSignal.TELEMETRY_INTEGRITY,
                        severity=OperationalSeverity.CRITICAL,
                        correlation_id=correlation_id,
                        events=correlated_events,
                        reason_code="TELEMETRY_INTEGRITY_FINDING",
                    )
                )
            alerts = sorted({item.signal: item for item in alerts}.values(), key=lambda item: item.signal.value)
            all_alerts.extend(alerts)
            if not alerts and not related_findings:
                continue
            lineage = self._lineage.get(correlation_id)
            if lineage is None:
                raise ValueError("incident reconstruction requires exact lineage")
            incidents.append(
                OperationalIncident.create(
                    incident_id=reconstruction.incident_id,
                    correlation_id_sha256=reconstruction.correlation_id_sha256,
                    telemetry_reconstruction_sha256=reconstruction.reconstruction_sha256,
                    lineage_sha256=lineage.lineage_sha256,
                    alert_sha256=tuple(item.alert_sha256 for item in alerts),
                    telemetry_finding_sha256=tuple(
                        sorted(item.finding_sha256 for item in related_findings)
                    ),
                    canonical_mutation=False,
                    recovery_authorized=False,
                    protected_payload_included=False,
                )
            )

        signal_counts = Counter(item.signal.value for item in all_alerts)
        status_counts = Counter(item.status.value for item in events)
        if any(item.severity == OperationalSeverity.CRITICAL for item in all_alerts):
            level = HealthLevel.CRITICAL
        elif all_alerts:
            level = HealthLevel.DEGRADED
        else:
            level = HealthLevel.HEALTHY

        incidents.sort(key=lambda item: item.incident_id)
        report = OperationalHealthReport.create(
            execution_context=ExecutionContext.TEST,
            level=level,
            event_count=len(events),
            correlation_count=len(grouped),
            status_counts=dict(sorted(status_counts.items())),
            signal_counts=dict(sorted(signal_counts.items())),
            incident_sha256=tuple(item.incident_sha256 for item in incidents),
            canonical_mutation=False,
            recovery_authorized=False,
        )
        return report, tuple(incidents)
