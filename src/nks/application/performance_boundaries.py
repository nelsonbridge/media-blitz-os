"""Governed synthetic performance and resource boundaries for Enki.

The benchmark layer is deliberately TEST-only.  It characterizes repeatable
internal workloads and enforces declared budgets; it never converts benchmark
results into production capacity guarantees.
"""

from __future__ import annotations

import gc
import math
import statistics
import time
import tracemalloc
from collections.abc import Callable, Iterable
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.governance.approvals import ExecutionContext


class OperationFamily(StrEnum):
    TRANSACTION = "TRANSACTION"
    STATE_WRITE = "STATE_WRITE"
    RECONCILIATION = "RECONCILIATION"
    TRANSITION = "TRANSITION"
    MODEL_USE = "MODEL_USE"
    RECONSTRUCTION = "RECONSTRUCTION"
    EXPORT_IMPORT = "EXPORT_IMPORT"


class WorkloadClass(StrEnum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"
    OVERLOAD = "OVERLOAD"


class BudgetDisposition(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_EVALUATED = "NOT_EVALUATED"


class SyntheticWorkload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workload_id: str = Field(min_length=1)
    operation_family: OperationFamily
    workload_class: WorkloadClass
    item_count: int = Field(ge=1)
    payload_bytes: int = Field(ge=0)
    iterations: int = Field(ge=1)
    warmup_iterations: int = Field(ge=0)
    seed: int = Field(ge=0)
    execution_context: ExecutionContext = ExecutionContext.TEST
    contains_private_data: bool = False
    contains_production_data: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_test_boundary(self) -> "SyntheticWorkload":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("performance workloads are TEST-only")
        if self.contains_private_data or self.contains_production_data:
            raise ValueError("performance workloads cannot contain private or production data")
        return self

    @property
    def workload_sha256(self) -> str:
        return canonical_sha256(self)


class PerformanceBudget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    budget_id: str = Field(min_length=1)
    operation_family: OperationFamily
    workload_class: WorkloadClass
    max_p95_latency_ns: int = Field(gt=0)
    max_peak_memory_bytes: int = Field(gt=0)
    max_storage_growth_bytes: int = Field(ge=0)
    max_recovery_cost_ratio: float = Field(ge=1.0)
    max_error_rate: float = Field(ge=0.0, le=1.0)
    execution_context: ExecutionContext = ExecutionContext.TEST
    production_capacity_guarantee: bool = False

    @model_validator(mode="after")
    def validate_boundary(self) -> "PerformanceBudget":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("performance budgets are TEST-only")
        if self.production_capacity_guarantee:
            raise ValueError("benchmark budgets cannot be production capacity guarantees")
        return self


class BenchmarkSample(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    iteration: int = Field(ge=0)
    latency_ns: int = Field(ge=0)
    peak_memory_bytes: int = Field(ge=0)
    storage_growth_bytes: int = Field(ge=0)
    succeeded: bool
    error_type: str | None = None


class BenchmarkResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workload: SyntheticWorkload
    samples: list[BenchmarkSample] = Field(min_length=1)
    min_latency_ns: int = Field(ge=0)
    median_latency_ns: int = Field(ge=0)
    p95_latency_ns: int = Field(ge=0)
    max_latency_ns: int = Field(ge=0)
    throughput_per_second: float = Field(ge=0.0)
    peak_memory_bytes: int = Field(ge=0)
    storage_growth_bytes: int = Field(ge=0)
    error_rate: float = Field(ge=0.0, le=1.0)
    recovery_cost_ratio: float | None = Field(default=None, ge=1.0)
    budget_id: str | None = None
    budget_disposition: BudgetDisposition
    budget_violations: list[str] = Field(default_factory=list)
    result_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    execution_context: ExecutionContext = ExecutionContext.TEST
    production_capacity_guarantee: bool = False

    @model_validator(mode="after")
    def validate_result(self) -> "BenchmarkResult":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("benchmark results are TEST-only")
        if self.production_capacity_guarantee:
            raise ValueError("benchmark results cannot claim production capacity")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"result_sha256"})
        )
        if self.result_sha256 != expected:
            raise ValueError("benchmark result hash is invalid")
        if self.budget_disposition == BudgetDisposition.PASS and self.budget_violations:
            raise ValueError("passing benchmark cannot contain budget violations")
        if self.budget_disposition == BudgetDisposition.FAIL and not self.budget_violations:
            raise ValueError("failed benchmark requires budget violations")
        return self

    @classmethod
    def create(cls, **values: object) -> "BenchmarkResult":
        payload = dict(values)
        payload["result_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class BenchmarkSuiteReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    suite_id: str = Field(min_length=1)
    results: list[BenchmarkResult] = Field(min_length=1)
    covered_families: set[OperationFamily]
    missing_families: set[OperationFamily]
    all_budgets_pass: bool
    execution_context: ExecutionContext = ExecutionContext.TEST
    contains_private_data: bool = False
    contains_production_data: bool = False
    production_capacity_guarantee: bool = False
    limitation: str = (
        "Synthetic TEST measurements characterize this environment only and are not a production capacity guarantee."
    )
    report_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_report(self) -> "BenchmarkSuiteReport":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("benchmark reports are TEST-only")
        if self.contains_private_data or self.contains_production_data:
            raise ValueError("benchmark reports cannot contain protected production data")
        if self.production_capacity_guarantee:
            raise ValueError("benchmark reports cannot claim production capacity")
        expected_missing = set(OperationFamily) - self.covered_families
        if self.missing_families != expected_missing:
            raise ValueError("benchmark family coverage is inconsistent")
        if self.all_budgets_pass != all(
            item.budget_disposition == BudgetDisposition.PASS for item in self.results
        ):
            raise ValueError("suite budget disposition is inconsistent")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"report_sha256"})
        )
        if self.report_sha256 != expected:
            raise ValueError("benchmark report hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "BenchmarkSuiteReport":
        payload = dict(values)
        payload["report_sha256"] = canonical_sha256(payload)
        return cls(**payload)


StorageProbe = Callable[[], int]
Operation = Callable[[int], Any]


def percentile(values: list[int], percentile_value: float) -> int:
    if not values:
        raise ValueError("percentile requires at least one value")
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile_value * len(ordered)))
    return ordered[rank - 1]


class PerformanceBoundaryRunner:
    """Measure deterministic TEST workloads with explicit failure budgets."""

    def __init__(self, *, clock_ns: Callable[[], int] = time.perf_counter_ns) -> None:
        self._clock_ns = clock_ns

    def run(
        self,
        workload: SyntheticWorkload,
        operation: Operation,
        *,
        budget: PerformanceBudget | None = None,
        storage_probe: StorageProbe | None = None,
        recovery_operation: Operation | None = None,
    ) -> BenchmarkResult:
        if budget is not None and (
            budget.operation_family != workload.operation_family
            or budget.workload_class != workload.workload_class
        ):
            raise ValueError("performance budget does not match workload")

        for index in range(workload.warmup_iterations):
            operation(-(index + 1))

        gc.collect()
        samples: list[BenchmarkSample] = []
        storage_before = storage_probe() if storage_probe is not None else 0
        tracemalloc.start()
        try:
            for iteration in range(workload.iterations):
                before_current, before_peak = tracemalloc.get_traced_memory()
                start = self._clock_ns()
                succeeded = True
                error_type: str | None = None
                try:
                    operation(iteration)
                except Exception as exc:  # benchmark records bounded failures
                    succeeded = False
                    error_type = type(exc).__name__
                elapsed = max(0, self._clock_ns() - start)
                after_current, after_peak = tracemalloc.get_traced_memory()
                samples.append(
                    BenchmarkSample(
                        iteration=iteration,
                        latency_ns=elapsed,
                        peak_memory_bytes=max(0, after_peak - before_peak, after_current - before_current),
                        storage_growth_bytes=0,
                        succeeded=succeeded,
                        error_type=error_type,
                    )
                )
        finally:
            _, suite_peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
        storage_after = storage_probe() if storage_probe is not None else storage_before
        storage_growth = max(0, storage_after - storage_before)

        latencies = [sample.latency_ns for sample in samples]
        total_ns = sum(latencies)
        throughput = (len(samples) * 1_000_000_000 / total_ns) if total_ns else 0.0
        error_rate = sum(not sample.succeeded for sample in samples) / len(samples)

        recovery_ratio: float | None = None
        if recovery_operation is not None:
            recovery_start = self._clock_ns()
            recovery_operation(workload.iterations)
            recovery_ns = max(0, self._clock_ns() - recovery_start)
            baseline = max(1, statistics.median(latencies))
            recovery_ratio = max(1.0, recovery_ns / baseline)

        violations: list[str] = []
        disposition = BudgetDisposition.NOT_EVALUATED
        p95 = percentile(latencies, 0.95)
        peak_memory = max(suite_peak, *(sample.peak_memory_bytes for sample in samples))
        if budget is not None:
            checks = [
                (p95 > budget.max_p95_latency_ns, "p95 latency exceeds budget"),
                (peak_memory > budget.max_peak_memory_bytes, "peak memory exceeds budget"),
                (storage_growth > budget.max_storage_growth_bytes, "storage growth exceeds budget"),
                (error_rate > budget.max_error_rate, "error rate exceeds budget"),
                (
                    recovery_ratio is not None
                    and recovery_ratio > budget.max_recovery_cost_ratio,
                    "recovery cost ratio exceeds budget",
                ),
            ]
            violations = [message for failed, message in checks if failed]
            disposition = BudgetDisposition.FAIL if violations else BudgetDisposition.PASS

        return BenchmarkResult.create(
            workload=workload,
            samples=samples,
            min_latency_ns=min(latencies),
            median_latency_ns=int(statistics.median(latencies)),
            p95_latency_ns=p95,
            max_latency_ns=max(latencies),
            throughput_per_second=throughput,
            peak_memory_bytes=peak_memory,
            storage_growth_bytes=storage_growth,
            error_rate=error_rate,
            recovery_cost_ratio=recovery_ratio,
            budget_id=budget.budget_id if budget is not None else None,
            budget_disposition=disposition,
            budget_violations=violations,
            execution_context=ExecutionContext.TEST,
            production_capacity_guarantee=False,
        )


def directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def build_suite_report(
    suite_id: str,
    results: Iterable[BenchmarkResult],
) -> BenchmarkSuiteReport:
    materialized = list(results)
    if not materialized:
        raise ValueError("benchmark suite requires at least one result")
    covered = {item.workload.operation_family for item in materialized}
    return BenchmarkSuiteReport.create(
        suite_id=suite_id,
        results=materialized,
        covered_families=covered,
        missing_families=set(OperationFamily) - covered,
        all_budgets_pass=all(
            item.budget_disposition == BudgetDisposition.PASS for item in materialized
        ),
        execution_context=ExecutionContext.TEST,
        contains_private_data=False,
        contains_production_data=False,
        production_capacity_guarantee=False,
    )


def assert_complete_family_coverage(report: BenchmarkSuiteReport) -> None:
    if report.missing_families:
        missing = ", ".join(sorted(item.value for item in report.missing_families))
        raise AssertionError(f"missing benchmark operation families: {missing}")


def assert_within_budgets(report: BenchmarkSuiteReport) -> None:
    failures = [
        f"{item.workload.workload_id}: {', '.join(item.budget_violations)}"
        for item in report.results
        if item.budget_disposition != BudgetDisposition.PASS
    ]
    if failures:
        raise AssertionError("benchmark budgets failed: " + "; ".join(failures))
