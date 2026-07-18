"""Multi-product hosted TEST integration for Enki Sprint 47.

This module intentionally composes the product-consumer contracts established in
Sprint 33 with the concurrent multi-consumer platform coordinator established in
Sprint 34. It does not introduce a second hosted state store, canonical writer, or
provider runtime abstraction.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.downstream_products import ProductBoundaryRegistry, ProductSuite
from nks.application.governed_transactions import canonical_sha256
from nks.application.multi_consumer_operations import (
    MultiConsumerPlatformCoordinator,
    MultiConsumerRunManifest,
    MultiConsumerWorkItem,
    MultiConsumerWorkResult,
    PlatformIncident,
    PortableMultiConsumerBundle,
    reconstruct_multi_consumer_bundle,
)
from nks.application.privacy_observability import assert_telemetry_safe_serialization
from nks.governance.approvals import ExecutionContext


class MultiProductIntegrationError(RuntimeError):
    """Raised when a multi-product integration contract fails closed."""


class MultiProductHostedReport(BaseModel):
    """Deterministic report for one three-product TEST integration run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str = Field(min_length=1)
    execution_context: ExecutionContext
    suites: tuple[ProductSuite, ...]
    result_sha256: tuple[str, ...]
    incident_sha256: tuple[str, ...]
    manifest_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    portable_bundle_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    reconstructed_manifest_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    telemetry_sha256: tuple[str, ...]
    no_canonical_mutation: bool
    no_external_effect: bool
    provider_effects: int = Field(ge=0)
    report_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_report(self) -> "MultiProductHostedReport":
        expected_suites = {
            ProductSuite.MEDIA_BLITZ,
            ProductSuite.CAREER_INTELLIGENCE_PLACEMENT,
            ProductSuite.PERSONAL_COGNITIVE_CONTINUITY,
        }
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("Sprint 47 multi-product integration is TEST-only")
        if set(self.suites) != expected_suites:
            raise ValueError("Sprint 47 report must include all three product suites")
        if not self.no_canonical_mutation or not self.no_external_effect:
            raise ValueError("Sprint 47 cannot claim canonical mutation or external effects")
        if self.provider_effects != 0:
            raise ValueError("Sprint 47 provider-neutral TEST integration cannot claim provider effects")
        if self.reconstructed_manifest_sha256 != self.manifest_sha256:
            raise ValueError("portable reconstruction must preserve the exact manifest hash")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"report_sha256"}))
        if self.report_sha256 != expected:
            raise ValueError("multi-product hosted report hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "MultiProductHostedReport":
        payload = dict(values)
        payload["report_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class MultiProductHostedIntegration:
    """Run all three downstream products through one governed TEST platform surface."""

    def __init__(
        self,
        *,
        registry: ProductBoundaryRegistry,
        max_workers: int = 3,
    ) -> None:
        self._coordinator = MultiConsumerPlatformCoordinator(
            registry=registry,
            max_workers=max_workers,
        )

    @property
    def coordinator(self) -> MultiConsumerPlatformCoordinator:
        return self._coordinator

    @staticmethod
    def _validate_workload(items: list[MultiConsumerWorkItem]) -> None:
        if not items:
            raise MultiProductIntegrationError("multi-product integration requires work")
        suites = {item.suite for item in items}
        expected = {
            ProductSuite.MEDIA_BLITZ,
            ProductSuite.CAREER_INTELLIGENCE_PLACEMENT,
            ProductSuite.PERSONAL_COGNITIVE_CONTINUITY,
        }
        if suites != expected:
            raise MultiProductIntegrationError(
                "multi-product integration requires exactly the three governed product suites"
            )
        for item in items:
            if item.boundary.execution_context != ExecutionContext.TEST:
                raise MultiProductIntegrationError("production context is not permitted")

    def execute(
        self,
        *,
        run_id: str,
        items: list[MultiConsumerWorkItem],
        now: datetime,
    ) -> tuple[
        MultiProductHostedReport,
        MultiConsumerRunManifest,
        tuple[MultiConsumerWorkResult, ...],
        tuple[PlatformIncident, ...],
        PortableMultiConsumerBundle,
    ]:
        self._validate_workload(items)
        manifest, results, incidents = self._coordinator.execute_run(
            run_id=run_id,
            items=items,
            now=now,
        )
        bundle = self._coordinator.portable_bundle(
            manifest=manifest,
            results=results,
            incidents=incidents,
        )
        reconstructed = reconstruct_multi_consumer_bundle(bundle)
        telemetry = tuple(
            sorted(event.event_sha256 for event in self._coordinator.telemetry.events)
        )
        assert_telemetry_safe_serialization(list(self._coordinator.telemetry.events))

        report = MultiProductHostedReport.create(
            run_id=run_id,
            execution_context=ExecutionContext.TEST,
            suites=tuple(sorted({item.suite for item in items}, key=lambda suite: suite.value)),
            result_sha256=tuple(sorted(result.result_sha256 for result in results)),
            incident_sha256=tuple(sorted(incident.incident_sha256 for incident in incidents)),
            manifest_sha256=manifest.manifest_sha256,
            portable_bundle_sha256=bundle.bundle_sha256,
            reconstructed_manifest_sha256=reconstructed.manifest_sha256,
            telemetry_sha256=telemetry,
            no_canonical_mutation=manifest.no_canonical_mutation,
            no_external_effect=manifest.no_external_effect,
            provider_effects=0,
        )
        return report, manifest, results, incidents, bundle
