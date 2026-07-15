from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from nks.application.privacy_observability import (
    CorrelationContext,
    PrivacyTelemetryCollector,
    TelemetryEvent,
    TelemetryFindingKind,
    TelemetryKind,
    TelemetryStatus,
    assert_telemetry_safe_serialization,
)
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryContext


def _now() -> datetime:
    return datetime(2026, 7, 15, 5, 0, tzinfo=timezone.utc)


def _boundary(tenant: str = "TENANT-A") -> BoundaryContext:
    return BoundaryContext(
        namespace_id="NKS-TEST",
        tenant_id=tenant,
        subject_id="SUBJECT-1",
        domain="operations",
        audience="internal",
        execution_context=ExecutionContext.TEST,
    )


def _correlation(
    *,
    correlation_id: str = "CORR-1",
    operation_id: str = "OP-1",
    boundary: BoundaryContext | None = None,
) -> CorrelationContext:
    return CorrelationContext.from_boundary(
        boundary or _boundary(),
        correlation_id=correlation_id,
        operation_id=operation_id,
        transaction_id="TX-1",
    )


def _event(
    sequence: int,
    *,
    event_id: str | None = None,
    correlation: CorrelationContext | None = None,
    kind: TelemetryKind = TelemetryKind.TRACE,
    status: TelemetryStatus = TelemetryStatus.OK,
    metadata: dict[str, str | int | float | bool] | None = None,
) -> TelemetryEvent:
    values: dict[str, object] = {
        "event_id": event_id or f"EVT-{sequence}",
        "sequence": sequence,
        "kind": kind,
        "status": status,
        "correlation": correlation or _correlation(),
        "metadata": metadata or {"operation_family": "state-write"},
        "occurred_at": _now(),
    }
    if kind == TelemetryKind.METRIC:
        values.update(metric_name="duration_ms", metric_value=12.5)
    return TelemetryEvent.create(**values)


def test_health_metric_trace_and_diagnostic_events_store_bounded_operational_facts() -> None:
    collector = PrivacyTelemetryCollector()
    events = [
        _event(1, kind=TelemetryKind.HEALTH),
        _event(2, kind=TelemetryKind.METRIC),
        _event(3, kind=TelemetryKind.TRACE),
        _event(
            4,
            kind=TelemetryKind.DIAGNOSTIC,
            status=TelemetryStatus.DEGRADED,
            metadata={"reason_code": "RETRY_REQUIRED", "retry_count": 1},
        ),
    ]
    for event in events:
        collector.append(event)

    assert collector.events == tuple(events)
    assert collector.findings() == []
    assert_telemetry_safe_serialization(list(collector.events))


@pytest.mark.parametrize(
    "metadata, message",
    [
        ({"payload": "canonical human statement"}, "key is not allowed"),
        ({"human_name": "Person"}, "key is not allowed"),
        ({"reason_code": "password=secret"}, "secret-like"),
        ({"error_type": "sk-abcdefghijklmnop"}, "secret-like"),
        ({"operation_family": "x" * 129}, "length boundary"),
    ],
)
def test_protected_content_human_state_and_secrets_are_rejected(
    metadata: dict[str, str],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        _event(1, metadata=metadata)


def test_unauthorized_production_context_is_rejected() -> None:
    production = BoundaryContext(
        namespace_id="NKS-PROD",
        tenant_id="TENANT-A",
        subject_id="SUBJECT-1",
        domain="operations",
        audience="internal",
        execution_context=ExecutionContext.PRODUCTION,
    )
    with pytest.raises(ValidationError, match="TEST-only"):
        _event(1, correlation=_correlation(boundary=production))


def test_sequence_loss_is_detected_and_reconstructable_without_payload() -> None:
    collector = PrivacyTelemetryCollector()
    collector.append(_event(1))
    collector.append(_event(3))

    findings = collector.findings()
    assert len(findings) == 1
    assert findings[0].kind == TelemetryFindingKind.LOSS
    assert findings[0].affected_sequences == [2]

    reconstruction = collector.reconstruct("CORR-1")
    assert reconstruction.findings == findings
    assert reconstruction.protected_payload_included is False
    serialized = reconstruction.model_dump_json()
    assert "SUBJECT-1" not in serialized
    assert "TENANT-A" not in serialized


def test_duplicate_and_conflicting_sequence_delivery_are_detected() -> None:
    duplicate = PrivacyTelemetryCollector()
    first = _event(1, event_id="EVT-A")
    duplicate.append(first)
    duplicate.append(first.model_copy(update={"event_id": "EVT-B"}))
    finding = duplicate.findings()[0]
    assert finding.kind == TelemetryFindingKind.DUPLICATE
    assert finding.affected_sequences == [1]

    conflicting = PrivacyTelemetryCollector()
    conflicting.append(_event(1, event_id="EVT-A"))
    conflicting.append(
        _event(
            1,
            event_id="EVT-B",
            status=TelemetryStatus.FAILED,
            metadata={"reason_code": "INJECTED_FAILURE"},
        )
    )
    assert conflicting.findings()[0].kind == TelemetryFindingKind.HASH_CONFLICT


def test_correlation_break_detects_operation_or_boundary_mismatch() -> None:
    collector = PrivacyTelemetryCollector()
    collector.append(_event(1))
    collector.append(
        _event(
            2,
            correlation=_correlation(operation_id="OP-2", boundary=_boundary("TENANT-B")),
        )
    )
    assert TelemetryFindingKind.CORRELATION_BREAK in {
        finding.kind for finding in collector.findings()
    }


def test_exact_duplicate_event_is_idempotent_but_identity_conflict_fails() -> None:
    collector = PrivacyTelemetryCollector()
    event = _event(1)
    assert collector.append(event) == event
    assert collector.append(event) == event
    assert len(collector.events) == 1

    with pytest.raises(ValueError, match="identity conflict"):
        collector.append(
            _event(
                1,
                event_id=event.event_id,
                status=TelemetryStatus.FAILED,
                metadata={"reason_code": "OTHER"},
            )
        )


def test_event_and_reconstruction_hash_tampering_fail_closed() -> None:
    event = _event(1)
    with pytest.raises(ValidationError, match="event hash is invalid"):
        TelemetryEvent.model_validate(
            event.model_dump(mode="python") | {"event_sha256": "sha256:" + "0" * 64}
        )

    collector = PrivacyTelemetryCollector()
    collector.append(event)
    reconstruction = collector.reconstruct("CORR-1")
    with pytest.raises(ValidationError, match="reconstruction hash is invalid"):
        reconstruction.model_validate(
            reconstruction.model_dump(mode="python")
            | {"reconstruction_sha256": "sha256:" + "0" * 64}
        )


def test_safe_serialization_detects_protected_literals_even_after_model_creation() -> None:
    event = _event(1)
    unsafe = event.model_copy(update={"metadata": {"reason_code": "user@example.com"}})
    with pytest.raises(ValueError, match="protected literal"):
        assert_telemetry_safe_serialization([unsafe])
