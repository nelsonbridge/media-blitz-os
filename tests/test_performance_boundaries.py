from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from nks.application.performance_boundaries import (
    OperationFamily,
    PerformanceBudget,
    PerformanceOverloadError,
    PerformanceReport,
    SyntheticWorkload,
    default_budget,
    run_benchmark,
    run_default_synthetic_suite,
)
from nks.governance.approvals import ExecutionContext


def _workload(
    family: OperationFamily,
    *,
    count: int = 8,
    size: int = 256,
    recovery_fraction: float = 0.25,
) -> SyntheticWorkload:
    return SyntheticWorkload(
        workload_id=f"TEST-{family.value}",
        family=family,
        operation_count=count,
        payload_size_bytes=size,
        recovery_fraction=recovery_fraction,
    )


def test_default_suite_covers_every_required_operation_family() -> None:
    reports = run_default_synthetic_suite()
    assert {report.workload.family for report in reports} == set(OperationFamily)
    assert all(report.within_budget for report in reports)
    assert all(report.execution_context == ExecutionContext.TEST for report in reports)
    assert all(not report.external_effect for report in reports)
    assert all(not report.production_capacity_claim for report in reports)


@pytest.mark.parametrize("family", list(OperationFamily))
def test_each_family_reports_latency_throughput_memory_storage_and_recovery(
    family: OperationFamily,
) -> None:
    report = run_benchmark(_workload(family), default_budget(family))
    measurement = report.measurement

    assert measurement.operation_count == 8
    assert measurement.p50_latency_ms >= 0
    assert measurement.p95_latency_ms >= measurement.p50_latency_ms
    assert measurement.throughput_ops_per_second > 0
    assert measurement.peak_memory_bytes > 0
    assert measurement.storage_growth_bytes > 0
    assert measurement.storage_bytes_per_operation > 0
    assert measurement.error_rate == 0
    assert measurement.recovery_count == 2
    assert measurement.mean_recovery_cost_ms >= 0
    assert report.report_sha256.startswith("sha256:")


def test_overload_fails_before_work_is_executed() -> None:
    workload = _workload(OperationFamily.TRANSACTION, count=3)
    budget = default_budget(OperationFamily.TRANSACTION).model_copy(
        update={"max_operations": 2}
    )
    called = False

    def operation(index: int, payload: bytes, root: Path) -> int:
        nonlocal called
        called = True
        return 0

    with pytest.raises(PerformanceOverloadError, match="exceeds TEST operation budget"):
        run_benchmark(workload, budget, operation=operation)
    assert not called


def test_operation_errors_are_measured_and_fail_the_error_budget() -> None:
    workload = _workload(OperationFamily.STATE_WRITE, recovery_fraction=0)

    def failing_operation(index: int, payload: bytes, root: Path) -> int:
        raise OSError("synthetic injected failure")

    report = run_benchmark(
        workload,
        default_budget(OperationFamily.STATE_WRITE),
        operation=failing_operation,
    )
    assert not report.within_budget
    assert report.measurement.error_count == workload.operation_count
    assert report.measurement.error_rate == 1.0
    assert "ERROR_RATE_EXCEEDED" in report.violations


def test_explicit_resource_budgets_fail_closed() -> None:
    family = OperationFamily.TRANSACTION
    workload = _workload(family, count=2, recovery_fraction=0)
    impossible = PerformanceBudget(
        family=family,
        max_operations=2,
        max_p95_latency_ms=0.000001,
        min_throughput_ops_per_second=1_000_000_000.0,
        max_peak_memory_bytes=1,
        max_storage_bytes_per_operation=1,
        max_error_rate=0,
        max_recovery_cost_ms=0.000001,
    )
    report = run_benchmark(workload, impossible)
    assert not report.within_budget
    assert "P95_LATENCY_EXCEEDED" in report.violations
    assert "THROUGHPUT_BELOW_MINIMUM" in report.violations
    assert "PEAK_MEMORY_EXCEEDED" in report.violations
    assert "STORAGE_GROWTH_EXCEEDED" in report.violations


@pytest.mark.parametrize(
    "updates, message",
    [
        ({"private_data_used": True}, "private or production data"),
        ({"production_data_used": True}, "private or production data"),
        ({"data_classification": "REAL/PRODUCTION"}, "SYNTHETIC/TEST"),
        ({"execution_context": ExecutionContext.PRODUCTION}, "TEST-only"),
    ],
)
def test_private_production_or_non_test_workloads_are_rejected(
    updates: dict[str, object],
    message: str,
) -> None:
    payload = _workload(OperationFamily.RECONCILIATION).model_dump(mode="python")
    with pytest.raises(ValidationError, match=message):
        SyntheticWorkload.model_validate(payload | updates)


def test_report_cannot_be_relabelled_as_production_capacity() -> None:
    report = run_benchmark(
        _workload(OperationFamily.PORTABILITY),
        default_budget(OperationFamily.PORTABILITY),
    )
    payload = report.model_dump(mode="python")
    with pytest.raises(ValidationError, match="cannot claim production capacity"):
        PerformanceReport.model_validate(payload | {"production_capacity_claim": True})
    with pytest.raises(ValidationError, match="report hash is invalid"):
        PerformanceReport.model_validate(
            payload | {"report_sha256": "sha256:" + "0" * 64}
        )


def test_budget_family_must_match_workload_family() -> None:
    with pytest.raises(ValueError, match="budget family does not match"):
        run_benchmark(
            _workload(OperationFamily.TRANSACTION),
            default_budget(OperationFamily.MODEL_USE),
        )
