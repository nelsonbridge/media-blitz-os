from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from nks.application.governed_transactions import canonical_sha256
from nks.application.operational_incident_management import (
    HealthLevel,
    IncidentLineage,
    OperationalIncident,
    OperationalObservabilityService,
    OperationalSignal,
)
from nks.application.privacy_observability import (
    CorrelationContext,
    PrivacyTelemetryCollector,
    TelemetryEvent,
    TelemetryFindingKind,
    TelemetryKind,
    TelemetryStatus,
)
from nks.application.sprint46_path_manifest import sprint46_operational_observability_path_manifest
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryContext

NOW = datetime(2026, 7, 17, 8, 30, tzinfo=timezone.utc)


def boundary(subject: str = "subject-1") -> BoundaryContext:
    return BoundaryContext(
        namespace_id="enki",
        tenant_id="tenant-1",
        subject_id=subject,
        domain="operations",
        audience="operators",
        execution_context=ExecutionContext.TEST,
    )


def correlation(
    correlation_id: str = "CORR-1",
    *,
    operation_id: str = "OP-1",
    selected_boundary: BoundaryContext | None = None,
) -> CorrelationContext:
    return CorrelationContext.from_boundary(
        selected_boundary or boundary(),
        correlation_id=correlation_id,
        operation_id=operation_id,
        transaction_id="TX-1",
    )


def event(
    event_id: str,
    sequence: int,
    *,
    corr: CorrelationContext | None = None,
    kind: TelemetryKind = TelemetryKind.TRACE,
    status: TelemetryStatus = TelemetryStatus.OK,
    metric_name: str | None = None,
    metric_value: int | float | None = None,
    metadata: dict[str, str | int | float | bool] | None = None,
) -> TelemetryEvent:
    return TelemetryEvent.create(
        event_id=event_id,
        sequence=sequence,
        kind=kind,
        status=status,
        correlation=corr or correlation(),
        metric_name=metric_name,
        metric_value=metric_value,
        metadata=metadata or {},
        occurred_at=NOW,
    )


def lineage(operation_id: str = "OP-1") -> IncidentLineage:
    return IncidentLineage.create(
        operation_id=operation_id,
        authority_sha256=canonical_sha256("authority-1"),
        evidence_sha256=(canonical_sha256("evidence-1"), canonical_sha256("evidence-2")),
        recovery_sha256=(canonical_sha256("recovery-1"),),
    )


def test_healthy_bounded_telemetry_produces_read_only_health_report() -> None:
    collector = PrivacyTelemetryCollector()
    collector.append(event("E1", 1, kind=TelemetryKind.HEALTH))
    collector.append(event("E2", 2, kind=TelemetryKind.TRACE))
    collector.append(
        event(
            "E3",
            3,
            kind=TelemetryKind.DIAGNOSTIC,
            metadata={"operation_family": "runtime", "terminal_state": "COMMITTED"},
        )
    )
    report, incidents = OperationalObservabilityService(
        collector=collector,
        lineage_by_correlation={"CORR-1": lineage()},
    ).analyze()

    assert report.level == HealthLevel.HEALTHY
    assert report.event_count == 3
    assert report.canonical_mutation is False
    assert report.recovery_authorized is False
    assert incidents == ()


def test_operational_conditions_are_visible_and_incident_lineage_is_hash_bound() -> None:
    collector = PrivacyTelemetryCollector()
    events = [
        event("Q", 1, kind=TelemetryKind.METRIC, metric_name="queue_depth", metric_value=20),
        event("S", 2, kind=TelemetryKind.METRIC, metric_name="saturation_pct", metric_value=91),
        event("L", 3, kind=TelemetryKind.METRIC, metric_name="latency_ms", metric_value=900),
        event("F", 4, status=TelemetryStatus.FAILED, metadata={"reason_code": "EXECUTION_FAILED"}),
        event("R", 5, metadata={"retry_count": 1}),
        event("RC", 6, metadata={"terminal_state": "RECOVERED"}),
        event(
            "P",
            7,
            status=TelemetryStatus.DEGRADED,
            metadata={"reason_code": "PROVIDER_DEGRADED", "adapter_kind": "hosted-test"},
        ),
    ]
    for item in events:
        collector.append(item)
    exact_lineage = lineage()
    report, incidents = OperationalObservabilityService(
        collector=collector,
        lineage_by_correlation={"CORR-1": exact_lineage},
    ).analyze()

    assert report.level == HealthLevel.CRITICAL
    assert set(report.signal_counts) == {
        signal.value
        for signal in (
            OperationalSignal.QUEUE_PRESSURE,
            OperationalSignal.SATURATION,
            OperationalSignal.HIGH_LATENCY,
            OperationalSignal.FAILURE,
            OperationalSignal.RETRY,
            OperationalSignal.RECOVERY,
            OperationalSignal.PROVIDER_DEGRADATION,
        )
    }
    assert len(incidents) == 1
    assert incidents[0].lineage_sha256 == exact_lineage.lineage_sha256
    assert incidents[0].canonical_mutation is False
    assert incidents[0].recovery_authorized is False


def test_loss_duplicate_conflict_and_correlation_mismatch_are_detected() -> None:
    collector = PrivacyTelemetryCollector()
    collector.append(event("E1", 1))
    collector.append(event("E3-A", 3))
    collector.append(event("E3-B", 3, status=TelemetryStatus.DEGRADED))
    collector.append(event("E4", 4, corr=correlation(operation_id="OP-DIFFERENT")))

    findings = collector.findings()
    assert {item.kind for item in findings} == {
        TelemetryFindingKind.LOSS,
        TelemetryFindingKind.HASH_CONFLICT,
        TelemetryFindingKind.CORRELATION_BREAK,
    }

    report, incidents = OperationalObservabilityService(
        collector=collector,
        lineage_by_correlation={"CORR-1": lineage()},
    ).analyze()
    assert report.level == HealthLevel.CRITICAL
    assert report.signal_counts[OperationalSignal.TELEMETRY_INTEGRITY.value] == 1
    assert len(incidents[0].telemetry_finding_sha256) == 3


def test_alert_without_exact_lineage_fails_closed() -> None:
    collector = PrivacyTelemetryCollector()
    collector.append(event("FAIL", 1, status=TelemetryStatus.FAILED))
    with pytest.raises(ValueError, match="requires exact lineage"):
        OperationalObservabilityService(
            collector=collector,
            lineage_by_correlation={},
        ).analyze()


def test_protected_content_and_secrets_cannot_enter_telemetry() -> None:
    with pytest.raises(ValidationError):
        event("BAD-CONTENT", 1, metadata={"content": "private person state"})
    with pytest.raises(ValidationError):
        event("BAD-SECRET", 1, metadata={"reason_code": "password=never-log-this"})


def test_observability_cannot_claim_canonical_mutation_or_recovery_authority() -> None:
    base = {
        "incident_id": "INC-1",
        "correlation_id_sha256": canonical_sha256("CORR-1"),
        "telemetry_reconstruction_sha256": canonical_sha256("reconstruction"),
        "lineage_sha256": lineage().lineage_sha256,
        "alert_sha256": (canonical_sha256("alert"),),
        "telemetry_finding_sha256": (),
        "protected_payload_included": False,
    }
    with pytest.raises(ValidationError, match="cannot mutate canonical"):
        OperationalIncident.create(**base, canonical_mutation=True, recovery_authorized=False)
    with pytest.raises(ValidationError, match="cannot authorize recovery"):
        OperationalIncident.create(**base, canonical_mutation=False, recovery_authorized=True)


def test_operational_analysis_is_deterministic() -> None:
    collector = PrivacyTelemetryCollector()
    collector.append(event("E1", 1, kind=TelemetryKind.METRIC, metric_name="latency_ms", metric_value=700))
    service = OperationalObservabilityService(
        collector=collector,
        lineage_by_correlation={"CORR-1": lineage()},
    )
    assert service.analyze() == service.analyze()


SPRINT46_TESTED_PATHS = {
    "bounded-metrics-traces-diagnostics-health",
    "stable-correlation-identifiers",
    "protected-content-denied",
    "secret-telemetry-denied",
    "queue-pressure-observable",
    "saturation-observable",
    "latency-observable",
    "failure-observable",
    "retry-observable",
    "recovery-observable",
    "provider-degradation-observable",
    "incident-authority-lineage-hash-bound",
    "incident-evidence-lineage-hash-bound",
    "incident-recovery-lineage-hash-bound",
    "telemetry-loss-detected",
    "telemetry-duplicate-conflict-detected",
    "telemetry-correlation-mismatch-detected",
    "missing-incident-lineage-denied",
    "health-report-deterministic",
    "incident-reconstruction-deterministic",
    "observability-cannot-mutate-canonical-state",
    "observability-cannot-authorize-recovery",
}


def test_declared_sprint46_paths_have_coverage_and_test_only_effects() -> None:
    manifest = sprint46_operational_observability_path_manifest()
    manifest.assert_complete_coverage(SPRINT46_TESTED_PATHS)
    assert manifest.execution_context == ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "direct-canonical-write" in path.prohibited_effects
        assert "recovery-authorization" in path.prohibited_effects
        assert "protected-payload-telemetry" in path.prohibited_effects
        assert "secret-telemetry" in path.prohibited_effects
        assert "authority-widening" in path.prohibited_effects
