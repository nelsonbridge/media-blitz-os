"""Concurrent TEST operations for independent Enki downstream consumers.

Sprint 34 exercises Media Blitz, Career Intelligence and Placement, and Personal
Cognitive Continuity concurrently while preserving exact product boundaries,
privacy-safe telemetry, deterministic no-effect receipts, and portable recovery
manifests.  This module has no canonical writer and cannot authorize production.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from enum import StrEnum
from threading import Lock, RLock
from time import sleep
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.downstream_products import (
    NoEffectProductAdapter,
    NoEffectProductReceipt,
    ProductBoundaryRegistry,
    ProductPackage,
    ProductSuite,
)
from nks.application.governed_transactions import canonical_sha256
from nks.application.hosted_downstream_integration import (
    ConsumerIntent,
    ExternalActionAuthorization,
    HostedDownstreamConsumerService,
    HumanContinuityControl,
)
from nks.application.privacy_observability import (
    CorrelationContext,
    PrivacyTelemetryCollector,
    TelemetryEvent,
    TelemetryKind,
    TelemetryStatus,
    assert_telemetry_safe_serialization,
)
from nks.enki.governed_retrieval import GovernedKnowledgeRecord, GovernedRetrievalRequest
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryContext


class WorkFailureMode(StrEnum):
    NONE = "NONE"
    ONCE = "ONCE"
    ALWAYS = "ALWAYS"


class PlatformTerminalState(StrEnum):
    COMMITTED = "COMMITTED"
    RECOVERED = "RECOVERED"
    ROLLED_BACK = "ROLLED_BACK"


class PlatformIncidentKind(StrEnum):
    QUEUE_PRESSURE = "QUEUE_PRESSURE"
    CONTENTION = "CONTENTION"
    RETRY_RECOVERY = "RETRY_RECOVERY"
    CONSUMER_FAILURE = "CONSUMER_FAILURE"


class MultiConsumerWorkItem(BaseModel):
    """One immutable TEST work request for one downstream product boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    work_id: str = Field(min_length=1)
    suite: ProductSuite
    intent: ConsumerIntent
    boundary: BoundaryContext
    records: tuple[GovernedKnowledgeRecord, ...]
    retrieval_request: GovernedRetrievalRequest
    submitted_at: datetime
    simulated_feedback: tuple[str, ...] = ()
    external_action_authorization: ExternalActionAuthorization | None = None
    human_control: HumanContinuityControl | None = None
    contention_key: str | None = None
    delay_ms: int = Field(default=0, ge=0, le=250)
    failure_mode: WorkFailureMode = WorkFailureMode.NONE

    @model_validator(mode="after")
    def validate_test_boundary(self) -> "MultiConsumerWorkItem":
        if self.boundary.execution_context != ExecutionContext.TEST:
            raise ValueError("Sprint 34 multi-consumer work is TEST-only")
        request = self.retrieval_request
        if (
            request.tenant_id != self.boundary.tenant_id
            or request.subject_id != self.boundary.subject_id
            or request.domain != self.boundary.domain
            or request.audience != self.boundary.audience
        ):
            raise ValueError("work retrieval request does not match exact boundary")
        return self

    @property
    def work_sha256(self) -> str:
        return canonical_sha256(self)


class PlatformAttemptReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    attempt_id: str
    work_id: str
    attempt_number: int = Field(ge=1)
    terminal_state: PlatformTerminalState
    package_sha256: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    product_receipt_sha256: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    reason_code: str
    recorded_at: datetime
    attempt_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash_and_effect(self) -> "PlatformAttemptReceipt":
        if self.terminal_state == PlatformTerminalState.ROLLED_BACK:
            if self.package_sha256 is not None or self.product_receipt_sha256 is not None:
                raise ValueError("rolled-back attempt cannot claim package or product receipt")
        else:
            if self.package_sha256 is None or self.product_receipt_sha256 is None:
                raise ValueError("successful attempt requires package and product receipt hashes")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"attempt_sha256"}))
        if self.attempt_sha256 != expected:
            raise ValueError("platform attempt receipt hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "PlatformAttemptReceipt":
        payload = dict(values)
        payload["attempt_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class MultiConsumerWorkResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    work_id: str
    suite: ProductSuite
    terminal_state: PlatformTerminalState
    attempts: tuple[PlatformAttemptReceipt, ...]
    package_sha256: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    product_receipt_sha256: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    exact_retry: bool
    result_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "MultiConsumerWorkResult":
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"result_sha256"}))
        if self.result_sha256 != expected:
            raise ValueError("multi-consumer result hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "MultiConsumerWorkResult":
        payload = dict(values)
        payload["result_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class PlatformIncident(BaseModel):
    """Privacy-safe operational incident containing hashes and bounded counts only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: str
    kind: PlatformIncidentKind
    affected_work_sha256: tuple[str, ...]
    evidence_sha256: tuple[str, ...]
    count: int = Field(ge=1)
    protected_payload_included: bool = False
    incident_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_incident(self) -> "PlatformIncident":
        if self.protected_payload_included:
            raise ValueError("platform incidents cannot include protected payload")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"incident_sha256"}))
        if self.incident_sha256 != expected:
            raise ValueError("platform incident hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "PlatformIncident":
        payload = dict(values)
        payload["incident_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class MultiConsumerRunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    execution_context: ExecutionContext
    canonical_input_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    canonical_output_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    result_sha256: tuple[str, ...]
    product_receipt_sha256: tuple[str, ...]
    telemetry_sha256: tuple[str, ...]
    incident_sha256: tuple[str, ...]
    no_canonical_mutation: bool = True
    no_external_effect: bool = True
    manifest_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_manifest(self) -> "MultiConsumerRunManifest":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("Sprint 34 run manifest is TEST-only")
        if not self.no_canonical_mutation or not self.no_external_effect:
            raise ValueError("Sprint 34 manifest cannot claim canonical or external effects")
        if self.canonical_input_sha256 != self.canonical_output_sha256:
            raise ValueError("multi-consumer TEST operation changed canonical input state")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"manifest_sha256"}))
        if self.manifest_sha256 != expected:
            raise ValueError("multi-consumer manifest hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "MultiConsumerRunManifest":
        payload = dict(values)
        payload["manifest_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class PortableMultiConsumerBundle(BaseModel):
    """Portable, payload-free reconstruction package for one TEST platform run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    manifest: MultiConsumerRunManifest
    results: tuple[MultiConsumerWorkResult, ...]
    telemetry_event_sha256: tuple[str, ...]
    incidents: tuple[PlatformIncident, ...]
    bundle_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_bundle(self) -> "PortableMultiConsumerBundle":
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"bundle_sha256"}))
        if self.bundle_sha256 != expected:
            raise ValueError("portable multi-consumer bundle hash is invalid")
        if tuple(sorted(item.result_sha256 for item in self.results)) != self.manifest.result_sha256:
            raise ValueError("portable bundle result inventory does not match manifest")
        if self.telemetry_event_sha256 != self.manifest.telemetry_sha256:
            raise ValueError("portable bundle telemetry inventory does not match manifest")
        if tuple(sorted(item.incident_sha256 for item in self.incidents)) != self.manifest.incident_sha256:
            raise ValueError("portable bundle incident inventory does not match manifest")
        return self

    @classmethod
    def create(cls, **values: object) -> "PortableMultiConsumerBundle":
        payload = dict(values)
        payload["bundle_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class ThreadSafeNoEffectProductAdapter:
    """Thread-safe facade preserving the Sprint 33 no-effect receipt contract."""

    def __init__(self) -> None:
        self._adapter = NoEffectProductAdapter()
        self._lock = RLock()

    @property
    def receipts(self) -> dict[str, NoEffectProductReceipt]:
        with self._lock:
            return self._adapter.receipts

    def deliver(self, package: ProductPackage, *, now: datetime) -> NoEffectProductReceipt:
        with self._lock:
            return self._adapter.deliver(package, now=now)


class MultiConsumerPlatformCoordinator:
    """Run independent product consumers concurrently with deterministic recovery."""

    def __init__(
        self,
        *,
        registry: ProductBoundaryRegistry,
        max_workers: int = 3,
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be positive")
        self._adapter = ThreadSafeNoEffectProductAdapter()
        self._service = HostedDownstreamConsumerService(
            registry=registry,
            delivery_adapter=self._adapter,  # type: ignore[arg-type]
        )
        self._max_workers = max_workers
        self._telemetry = PrivacyTelemetryCollector()
        self._telemetry_lock = Lock()
        self._contention_locks: dict[str, Lock] = defaultdict(Lock)

    @property
    def telemetry(self) -> PrivacyTelemetryCollector:
        return self._telemetry

    @staticmethod
    def _canonical_fingerprint(items: Iterable[MultiConsumerWorkItem]) -> str:
        records: dict[str, dict[str, object]] = {}
        for item in items:
            for record in item.records:
                key = f"{record.tenant_id}:{record.envelope.record_id}"
                rendered = record.model_dump(mode="python")
                existing = records.get(key)
                if existing is not None and existing != rendered:
                    raise ValueError("conflicting canonical input record identity")
                records[key] = rendered
        return canonical_sha256(records)

    def _append_telemetry(
        self,
        item: MultiConsumerWorkItem,
        *,
        sequence: int,
        kind: TelemetryKind,
        status: TelemetryStatus,
        now: datetime,
        metric_name: str | None = None,
        metric_value: int | float | None = None,
        metadata: dict[str, str | int | float | bool] | None = None,
    ) -> TelemetryEvent:
        correlation = CorrelationContext.from_boundary(
            item.boundary,
            correlation_id=f"MC-{item.work_id}",
            operation_id=f"MULTI-CONSUMER-{item.suite.value}",
            transaction_id=item.work_id,
        )
        event = TelemetryEvent.create(
            event_id=f"MC-{item.work_id}-{sequence:02d}",
            sequence=sequence,
            kind=kind,
            status=status,
            correlation=correlation,
            metric_name=metric_name,
            metric_value=metric_value,
            metadata=metadata or {},
            occurred_at=now,
        )
        with self._telemetry_lock:
            return self._telemetry.append(event)

    @staticmethod
    def _rolled_back_attempt(
        item: MultiConsumerWorkItem,
        *,
        attempt_number: int,
        now: datetime,
        reason_code: str,
    ) -> PlatformAttemptReceipt:
        return PlatformAttemptReceipt.create(
            attempt_id=f"{item.work_id}-ATTEMPT-{attempt_number}",
            work_id=item.work_id,
            attempt_number=attempt_number,
            terminal_state=PlatformTerminalState.ROLLED_BACK,
            package_sha256=None,
            product_receipt_sha256=None,
            reason_code=reason_code,
            recorded_at=now,
        )

    @staticmethod
    def _successful_attempt(
        item: MultiConsumerWorkItem,
        *,
        attempt_number: int,
        package: ProductPackage,
        receipt: NoEffectProductReceipt,
        recovered: bool,
        now: datetime,
    ) -> PlatformAttemptReceipt:
        return PlatformAttemptReceipt.create(
            attempt_id=f"{item.work_id}-ATTEMPT-{attempt_number}",
            work_id=item.work_id,
            attempt_number=attempt_number,
            terminal_state=(
                PlatformTerminalState.RECOVERED if recovered else PlatformTerminalState.COMMITTED
            ),
            package_sha256=package.package_sha256,
            product_receipt_sha256=receipt.receipt_sha256,
            reason_code="EXACT_RETRY_RECOVERED" if recovered else "COMMITTED_NO_EFFECT",
            recorded_at=now,
        )

    def _execute_item(
        self,
        item: MultiConsumerWorkItem,
        *,
        queue_depth: int,
        now: datetime,
    ) -> MultiConsumerWorkResult:
        self._append_telemetry(
            item,
            sequence=1,
            kind=TelemetryKind.METRIC,
            status=TelemetryStatus.OK,
            metric_name="queue_depth",
            metric_value=queue_depth,
            metadata={
                "operation_family": "multi-consumer",
                "terminal_state": "QUEUED",
                "retry_count": 0,
                "adapter_kind": "test-no-effect",
            },
            now=now,
        )
        if item.delay_ms:
            sleep(item.delay_ms / 1000)

        lock = self._contention_locks[item.contention_key or item.work_id]
        attempts: list[PlatformAttemptReceipt] = []
        with lock:
            self._append_telemetry(
                item,
                sequence=2,
                kind=TelemetryKind.TRACE,
                status=TelemetryStatus.OK,
                metadata={
                    "operation_family": "multi-consumer",
                    "terminal_state": "RUNNING",
                    "retry_count": 0,
                    "adapter_kind": "test-no-effect",
                },
                now=now,
            )

            if item.failure_mode in {WorkFailureMode.ONCE, WorkFailureMode.ALWAYS}:
                attempts.append(
                    self._rolled_back_attempt(
                        item,
                        attempt_number=1,
                        now=now,
                        reason_code="SIMULATED_PRE_DELIVERY_FAILURE",
                    )
                )
                self._append_telemetry(
                    item,
                    sequence=3,
                    kind=TelemetryKind.DIAGNOSTIC,
                    status=TelemetryStatus.DEGRADED,
                    metadata={
                        "operation_family": "multi-consumer",
                        "terminal_state": "ROLLED_BACK",
                        "reason_code": "SIMULATED_PRE_DELIVERY_FAILURE",
                        "retry_count": 0,
                        "adapter_kind": "test-no-effect",
                    },
                    now=now,
                )
                if item.failure_mode == WorkFailureMode.ALWAYS:
                    return MultiConsumerWorkResult.create(
                        work_id=item.work_id,
                        suite=item.suite,
                        terminal_state=PlatformTerminalState.ROLLED_BACK,
                        attempts=tuple(attempts),
                        package_sha256=None,
                        product_receipt_sha256=None,
                        exact_retry=False,
                    )

            attempt_number = 2 if attempts else 1
            execution = self._service.run(
                suite=item.suite,
                intent=item.intent,
                records=list(item.records),
                retrieval_request=item.retrieval_request,
                now=now,
                external_action_authorization=item.external_action_authorization,
                human_control=item.human_control,
                simulated_feedback=item.simulated_feedback,
            )
            recovered = bool(attempts)
            successful = self._successful_attempt(
                item,
                attempt_number=attempt_number,
                package=execution.package,
                receipt=execution.receipt,
                recovered=recovered,
                now=now,
            )
            attempts.append(successful)
            self._append_telemetry(
                item,
                sequence=4 if recovered else 3,
                kind=TelemetryKind.TRACE,
                status=TelemetryStatus.OK,
                metadata={
                    "operation_family": "multi-consumer",
                    "terminal_state": (
                        "RECOVERED" if recovered else "COMMITTED"
                    ),
                    "retry_count": 1 if recovered else 0,
                    "adapter_kind": "test-no-effect",
                },
                now=now,
            )
            return MultiConsumerWorkResult.create(
                work_id=item.work_id,
                suite=item.suite,
                terminal_state=(
                    PlatformTerminalState.RECOVERED
                    if recovered
                    else PlatformTerminalState.COMMITTED
                ),
                attempts=tuple(attempts),
                package_sha256=execution.package.package_sha256,
                product_receipt_sha256=execution.receipt.receipt_sha256,
                exact_retry=recovered,
            )

    @staticmethod
    def _incident(
        kind: PlatformIncidentKind,
        items: Iterable[MultiConsumerWorkItem],
        evidence: Iterable[str],
    ) -> PlatformIncident:
        item_hashes = tuple(sorted(item.work_sha256 for item in items))
        evidence_hashes = tuple(sorted(evidence))
        return PlatformIncident.create(
            incident_id=f"MC-{kind.value}-{canonical_sha256(item_hashes)[7:23]}",
            kind=kind,
            affected_work_sha256=item_hashes,
            evidence_sha256=evidence_hashes,
            count=max(1, len(item_hashes)),
            protected_payload_included=False,
        )

    def execute_run(
        self,
        *,
        run_id: str,
        items: list[MultiConsumerWorkItem],
        now: datetime,
    ) -> tuple[MultiConsumerRunManifest, tuple[MultiConsumerWorkResult, ...], tuple[PlatformIncident, ...]]:
        if not items:
            raise ValueError("multi-consumer run requires work items")
        if len({item.work_id for item in items}) != len(items):
            raise ValueError("multi-consumer work ids must be unique")
        suites = {item.suite for item in items}
        if len(suites) < 2:
            raise ValueError("multi-consumer run requires at least two independent suites")

        canonical_before = self._canonical_fingerprint(items)
        queue_depth = len(items)
        results: list[MultiConsumerWorkResult] = []
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = {
                executor.submit(self._execute_item, item, queue_depth=queue_depth, now=now): item
                for item in items
            }
            for future in as_completed(futures):
                results.append(future.result())
        results.sort(key=lambda item: item.work_id)

        canonical_after = self._canonical_fingerprint(items)
        incidents: list[PlatformIncident] = []
        if len(items) > self._max_workers:
            incidents.append(
                self._incident(
                    PlatformIncidentKind.QUEUE_PRESSURE,
                    items,
                    (result.result_sha256 for result in results),
                )
            )
        contention_groups: dict[str, list[MultiConsumerWorkItem]] = defaultdict(list)
        for item in items:
            if item.contention_key is not None:
                contention_groups[item.contention_key].append(item)
        for group in contention_groups.values():
            if len(group) > 1:
                group_ids = {item.work_id for item in group}
                incidents.append(
                    self._incident(
                        PlatformIncidentKind.CONTENTION,
                        group,
                        (
                            result.result_sha256
                            for result in results
                            if result.work_id in group_ids
                        ),
                    )
                )
        recovered_results = [
            result for result in results if result.terminal_state == PlatformTerminalState.RECOVERED
        ]
        if recovered_results:
            recovered_ids = {result.work_id for result in recovered_results}
            incidents.append(
                self._incident(
                    PlatformIncidentKind.RETRY_RECOVERY,
                    (item for item in items if item.work_id in recovered_ids),
                    (result.result_sha256 for result in recovered_results),
                )
            )
        failed_results = [
            result for result in results if result.terminal_state == PlatformTerminalState.ROLLED_BACK
        ]
        if failed_results:
            failed_ids = {result.work_id for result in failed_results}
            incidents.append(
                self._incident(
                    PlatformIncidentKind.CONSUMER_FAILURE,
                    (item for item in items if item.work_id in failed_ids),
                    (result.result_sha256 for result in failed_results),
                )
            )
        incidents.sort(key=lambda item: (item.kind.value, item.incident_id))

        telemetry_events = sorted(
            self._telemetry.events,
            key=lambda event: (event.correlation.correlation_id, event.sequence, event.event_id),
        )
        assert_telemetry_safe_serialization(telemetry_events)
        product_receipts = tuple(
            sorted(
                result.product_receipt_sha256
                for result in results
                if result.product_receipt_sha256 is not None
            )
        )
        manifest = MultiConsumerRunManifest.create(
            run_id=run_id,
            execution_context=ExecutionContext.TEST,
            canonical_input_sha256=canonical_before,
            canonical_output_sha256=canonical_after,
            result_sha256=tuple(sorted(result.result_sha256 for result in results)),
            product_receipt_sha256=product_receipts,
            telemetry_sha256=tuple(sorted(event.event_sha256 for event in telemetry_events)),
            incident_sha256=tuple(sorted(item.incident_sha256 for item in incidents)),
            no_canonical_mutation=True,
            no_external_effect=True,
        )
        return manifest, tuple(results), tuple(incidents)

    def portable_bundle(
        self,
        *,
        manifest: MultiConsumerRunManifest,
        results: tuple[MultiConsumerWorkResult, ...],
        incidents: tuple[PlatformIncident, ...],
    ) -> PortableMultiConsumerBundle:
        telemetry_hashes = tuple(sorted(event.event_sha256 for event in self._telemetry.events))
        return PortableMultiConsumerBundle.create(
            manifest=manifest,
            results=tuple(sorted(results, key=lambda item: item.work_id)),
            telemetry_event_sha256=telemetry_hashes,
            incidents=tuple(sorted(incidents, key=lambda item: (item.kind.value, item.incident_id))),
        )


def reconstruct_multi_consumer_bundle(bundle: PortableMultiConsumerBundle) -> MultiConsumerRunManifest:
    """Revalidate a payload-free portable run bundle and return exact manifest authority."""

    validated = PortableMultiConsumerBundle.model_validate(bundle.model_dump(mode="python"))
    return MultiConsumerRunManifest.model_validate(validated.manifest.model_dump(mode="python"))
