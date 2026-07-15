"""Governed synthetic performance and resource-boundary measurements.

The benchmark harness is TEST-only, uses representative synthetic payloads,
performs no network access, and cannot make a production-capacity claim.
"""

from __future__ import annotations

import json
import math
import tempfile
import time
import tracemalloc
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path

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
    PORTABILITY = "PORTABILITY"


class SyntheticWorkload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workload_id: str = Field(min_length=1)
    family: OperationFamily
    operation_count: int = Field(ge=1)
    payload_size_bytes: int = Field(ge=1)
    recovery_fraction: float = Field(ge=0.0, le=1.0)
    execution_context: ExecutionContext = ExecutionContext.TEST
    data_classification: str = "SYNTHETIC/TEST"
    private_data_used: bool = False
    production_data_used: bool = False

    @model_validator(mode="after")
    def validate_test_only(self) -> "SyntheticWorkload":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("performance workloads are TEST-only")
        if self.data_classification != "SYNTHETIC/TEST":
            raise ValueError("performance workloads require SYNTHETIC/TEST data")
        if self.private_data_used or self.production_data_used:
            raise ValueError("performance workloads cannot use private or production data")
        return self


class PerformanceBudget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    family: OperationFamily
    max_operations: int = Field(ge=1)
    max_p95_latency_ms: float = Field(gt=0)
    min_throughput_ops_per_second: float = Field(gt=0)
    max_peak_memory_bytes: int = Field(ge=1)
    max_storage_bytes_per_operation: int = Field(ge=0)
    max_error_rate: float = Field(ge=0.0, le=1.0)
    max_recovery_cost_ms: float = Field(gt=0)


class PerformanceMeasurement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workload_id: str
    family: OperationFamily
    operation_count: int
    payload_size_bytes: int
    p50_latency_ms: float = Field(ge=0)
    p95_latency_ms: float = Field(ge=0)
    throughput_ops_per_second: float = Field(ge=0)
    peak_memory_bytes: int = Field(ge=0)
    storage_growth_bytes: int = Field(ge=0)
    storage_bytes_per_operation: float = Field(ge=0)
    error_count: int = Field(ge=0)
    error_rate: float = Field(ge=0.0, le=1.0)
    recovery_count: int = Field(ge=0)
    mean_recovery_cost_ms: float = Field(ge=0)


class PerformanceReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    report_id: str = Field(min_length=1)
    workload: SyntheticWorkload
    budget: PerformanceBudget
    measurement: PerformanceMeasurement
    within_budget: bool
    violations: list[str] = Field(default_factory=list)
    execution_context: ExecutionContext = ExecutionContext.TEST
    external_effect: bool = False
    production_capacity_claim: bool = False
    report_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_claims_and_hash(self) -> "PerformanceReport":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("performance reports are TEST-only")
        if self.external_effect:
            raise ValueError("performance reports cannot claim external effects")
        if self.production_capacity_claim:
            raise ValueError("synthetic benchmarks cannot claim production capacity")
        if self.within_budget == bool(self.violations):
            raise ValueError("within_budget must agree with violations")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"report_sha256"}))
        if self.report_sha256 != expected:
            raise ValueError("performance report hash is invalid")
        return self


class PerformanceOverloadError(RuntimeError):
    pass


SyntheticOperation = Callable[[int, bytes, Path], int]
RecoveryOperation = Callable[[int, bytes, Path], None]


def _percentile(samples: list[float], percentile: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    index = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
    return ordered[index]


def _payload(index: int, size: int) -> bytes:
    seed = f"SYNTHETIC/TEST:{index:08d}:".encode("utf-8")
    repeat = (size // len(seed)) + 1
    return (seed * repeat)[:size]


def _write_json(path: Path, value: object) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    path.write_bytes(encoded)
    return len(encoded)


def _kernel(family: OperationFamily) -> tuple[SyntheticOperation, RecoveryOperation]:
    def operation(index: int, payload: bytes, root: Path) -> int:
        payload_hash = canonical_sha256(payload.hex())
        family_root = root / family.value.lower()
        if family == OperationFamily.TRANSACTION:
            value = {
                "transaction_id": f"TX-{index:08d}",
                "plan_sha256": payload_hash,
                "stage": "COMMITTED",
            }
            return _write_json(family_root / f"{index:08d}.journal.json", value)
        if family == OperationFamily.STATE_WRITE:
            value = {
                "record_id": f"REC-{index:08d}",
                "content_sha256": payload_hash,
                "classification": "SYNTHETIC/TEST",
            }
            return _write_json(family_root / f"{index:08d}.state.json", value)
        if family == OperationFamily.RECONCILIATION:
            value = {
                "finding_id": f"FIND-{index:08d}",
                "left_sha256": payload_hash,
                "right_sha256": canonical_sha256(payload[::-1].hex()),
                "disposition": "SYNTHETIC_MATCH",
            }
            return _write_json(family_root / f"{index:08d}.finding.json", value)
        if family == OperationFamily.TRANSITION:
            value = {
                "transition_id": f"TR-{index:08d}",
                "before_sha256": payload_hash,
                "after_sha256": canonical_sha256((payload + b":after").hex()),
                "transition_type": "REFINEMENT",
            }
            return _write_json(family_root / f"{index:08d}.transition.json", value)
        if family == OperationFamily.MODEL_USE:
            value = {
                "package_id": f"MODEL-{index:08d}",
                "input_sha256": payload_hash,
                "execution_context": "TEST",
                "external_effect": False,
            }
            return _write_json(family_root / f"{index:08d}.model.json", value)
        if family == OperationFamily.RECONSTRUCTION:
            evidence = {
                "event_id": f"EVT-{index:08d}",
                "payload_sha256": payload_hash,
                "terminal_state": "COMPLETE",
            }
            path = family_root / f"{index:08d}.evidence.json"
            written = _write_json(path, evidence)
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if canonical_sha256(loaded["payload_sha256"]) != canonical_sha256(payload_hash):
                raise ValueError("synthetic reconstruction mismatch")
            return written
        if family == OperationFamily.PORTABILITY:
            package = {
                "package_id": f"PKG-{index:08d}",
                "content_sha256": payload_hash,
                "context": "TEST",
            }
            exported = family_root / "export" / f"{index:08d}.json"
            imported = family_root / "import" / f"{index:08d}.json"
            written = _write_json(exported, package)
            imported.parent.mkdir(parents=True, exist_ok=True)
            imported.write_bytes(exported.read_bytes())
            if imported.read_bytes() != exported.read_bytes():
                raise ValueError("synthetic portability mismatch")
            return written + imported.stat().st_size
        raise AssertionError(f"unsupported operation family: {family}")

    def recover(index: int, payload: bytes, root: Path) -> None:
        family_root = root / family.value.lower()
        candidates = sorted(family_root.rglob(f"{index:08d}*.json"))
        if not candidates:
            raise FileNotFoundError("synthetic recovery evidence is missing")
        for path in candidates:
            json.loads(path.read_text(encoding="utf-8"))
        canonical_sha256(payload.hex())

    return operation, recover


def default_budget(family: OperationFamily) -> PerformanceBudget:
    return PerformanceBudget(
        family=family,
        max_operations=256,
        max_p95_latency_ms=250.0,
        min_throughput_ops_per_second=1.0,
        max_peak_memory_bytes=128 * 1024 * 1024,
        max_storage_bytes_per_operation=32 * 1024,
        max_error_rate=0.0,
        max_recovery_cost_ms=250.0,
    )


def run_benchmark(
    workload: SyntheticWorkload,
    budget: PerformanceBudget,
    *,
    operation: SyntheticOperation | None = None,
    recovery_operation: RecoveryOperation | None = None,
    root: Path | None = None,
) -> PerformanceReport:
    if budget.family != workload.family:
        raise ValueError("budget family does not match workload")
    if workload.operation_count > budget.max_operations:
        raise PerformanceOverloadError(
            f"workload exceeds TEST operation budget of {budget.max_operations}"
        )

    selected_operation, selected_recovery = _kernel(workload.family)
    operation = operation or selected_operation
    recovery_operation = recovery_operation or selected_recovery

    owned_temp: tempfile.TemporaryDirectory[str] | None = None
    if root is None:
        owned_temp = tempfile.TemporaryDirectory(prefix="enki-performance-")
        root = Path(owned_temp.name)
    root.mkdir(parents=True, exist_ok=True)

    latencies: list[float] = []
    recovery_latencies: list[float] = []
    storage_growth = 0
    errors = 0
    recovery_target = int(workload.operation_count * workload.recovery_fraction)

    tracemalloc.start()
    started = time.perf_counter_ns()
    try:
        for index in range(workload.operation_count):
            payload = _payload(index, workload.payload_size_bytes)
            operation_started = time.perf_counter_ns()
            try:
                storage_growth += max(0, int(operation(index, payload, root)))
            except Exception:
                errors += 1
            finally:
                latencies.append((time.perf_counter_ns() - operation_started) / 1_000_000)

            if index < recovery_target and errors == 0:
                recovery_started = time.perf_counter_ns()
                try:
                    recovery_operation(index, payload, root)
                except Exception:
                    errors += 1
                finally:
                    recovery_latencies.append(
                        (time.perf_counter_ns() - recovery_started) / 1_000_000
                    )
        elapsed_seconds = max((time.perf_counter_ns() - started) / 1_000_000_000, 1e-9)
        _, peak_memory = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
        if owned_temp is not None:
            owned_temp.cleanup()

    measurement = PerformanceMeasurement(
        workload_id=workload.workload_id,
        family=workload.family,
        operation_count=workload.operation_count,
        payload_size_bytes=workload.payload_size_bytes,
        p50_latency_ms=_percentile(latencies, 0.50),
        p95_latency_ms=_percentile(latencies, 0.95),
        throughput_ops_per_second=workload.operation_count / elapsed_seconds,
        peak_memory_bytes=peak_memory,
        storage_growth_bytes=storage_growth,
        storage_bytes_per_operation=storage_growth / workload.operation_count,
        error_count=errors,
        error_rate=errors / workload.operation_count,
        recovery_count=len(recovery_latencies),
        mean_recovery_cost_ms=(
            sum(recovery_latencies) / len(recovery_latencies)
            if recovery_latencies
            else 0.0
        ),
    )

    violations: list[str] = []
    if measurement.p95_latency_ms > budget.max_p95_latency_ms:
        violations.append("P95_LATENCY_EXCEEDED")
    if measurement.throughput_ops_per_second < budget.min_throughput_ops_per_second:
        violations.append("THROUGHPUT_BELOW_MINIMUM")
    if measurement.peak_memory_bytes > budget.max_peak_memory_bytes:
        violations.append("PEAK_MEMORY_EXCEEDED")
    if measurement.storage_bytes_per_operation > budget.max_storage_bytes_per_operation:
        violations.append("STORAGE_GROWTH_EXCEEDED")
    if measurement.error_rate > budget.max_error_rate:
        violations.append("ERROR_RATE_EXCEEDED")
    if measurement.mean_recovery_cost_ms > budget.max_recovery_cost_ms:
        violations.append("RECOVERY_COST_EXCEEDED")

    payload = {
        "report_id": f"PERF-{workload.family.value}-{workload.workload_id}",
        "workload": workload,
        "budget": budget,
        "measurement": measurement,
        "within_budget": not violations,
        "violations": violations,
        "execution_context": ExecutionContext.TEST,
        "external_effect": False,
        "production_capacity_claim": False,
    }
    return PerformanceReport(**payload, report_sha256=canonical_sha256(payload))


def run_default_synthetic_suite() -> list[PerformanceReport]:
    reports: list[PerformanceReport] = []
    for family in OperationFamily:
        workload = SyntheticWorkload(
            workload_id=f"S15-{family.value}-SMALL",
            family=family,
            operation_count=16,
            payload_size_bytes=512,
            recovery_fraction=0.25,
        )
        reports.append(run_benchmark(workload, default_budget(family)))
    return reports
