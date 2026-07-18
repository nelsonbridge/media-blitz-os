"""Deterministic Enki 1.0 operational release package for Sprint 48.

The package assembles the validated software and TEST evidence accumulated through the
hosted roadmap while preserving production-control gaps as explicit external requirements.
It can request a human launch decision but can never authorize operational production launch.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.application.hosted_release_candidate import HumanDecisionDisposition
from nks.application.production_control_readiness import ProductionControl


OPERATIONAL_RELEASE_VERSION = "enki-1.0-operational-rc1"


class OperationalEvidenceDomain(StrEnum):
    SOFTWARE = "SOFTWARE"
    ARCHITECTURE = "ARCHITECTURE"
    HOSTING = "HOSTING"
    SECURITY = "SECURITY"
    IDENTITY = "IDENTITY"
    CANONICAL_DATA = "CANONICAL_DATA"
    EVIDENCE = "EVIDENCE"
    RECOVERY = "RECOVERY"
    PORTABILITY = "PORTABILITY"
    MULTI_CONSUMER = "MULTI_CONSUMER"
    OPERATIONS = "OPERATIONS"
    COST = "COST"


class OperationalEvidenceStatus(StrEnum):
    VALIDATED_TEST = "VALIDATED_TEST"
    VALIDATED = "VALIDATED"
    CONDITIONAL = "CONDITIONAL"
    INCOMPLETE = "INCOMPLETE"
    EXTERNALLY_REQUIRED = "EXTERNALLY_REQUIRED"


class ProductionControlClassification(StrEnum):
    VALIDATED = "VALIDATED"
    PARTIALLY_VALIDATED = "PARTIALLY_VALIDATED"
    UNVALIDATED = "UNVALIDATED"
    EXTERNALLY_REQUIRED = "EXTERNALLY_REQUIRED"


class OperationalReadinessStatus(StrEnum):
    READY = "READY"
    CONDITIONAL = "CONDITIONAL"
    NOT_READY = "NOT_READY"


class LaunchDecisionState(StrEnum):
    PENDING_HUMAN_DECISION = "PENDING_HUMAN_DECISION"


class OperationalEvidencePointer(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str = Field(min_length=1)
    domain: OperationalEvidenceDomain
    reference: str = Field(min_length=1)
    status: OperationalEvidenceStatus
    qualification: str = Field(min_length=1)
    evidence_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash(self) -> "OperationalEvidencePointer":
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"evidence_sha256"})
        )
        if self.evidence_sha256 != expected:
            raise ValueError("operational evidence pointer hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "OperationalEvidencePointer":
        payload = dict(values)
        payload["evidence_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class ProductionControlStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    control: ProductionControl
    classification: ProductionControlClassification
    reason: str = Field(min_length=1)
    sprint45_reference: Literal["records/sprints/NKS-SPR-045.json"] = (
        "records/sprints/NKS-SPR-045.json"
    )
    qualifying_production_evidence_present: bool
    independent_assessment_required: bool
    status_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_status(self) -> "ProductionControlStatus":
        if self.classification == ProductionControlClassification.VALIDATED:
            if not self.qualifying_production_evidence_present:
                raise ValueError("VALIDATED control requires qualifying production evidence")
        if self.control == ProductionControl.INDEPENDENT_PENETRATION_TESTING:
            if not self.independent_assessment_required:
                raise ValueError("penetration testing must require independent assessment")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"status_sha256"})
        )
        if self.status_sha256 != expected:
            raise ValueError("production control status hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "ProductionControlStatus":
        payload = dict(values)
        payload.setdefault("sprint45_reference", "records/sprints/NKS-SPR-045.json")
        payload["status_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class OperationalReadinessConclusion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    software_ready: bool
    hosted_platform_status: OperationalReadinessStatus
    production_controls_status: OperationalReadinessStatus
    operational_status: OperationalReadinessStatus
    blockers: tuple[str, ...]
    statement: str = Field(min_length=1)
    production_launch_authorized: Literal[False] = False
    conclusion_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_conclusion(self) -> "OperationalReadinessConclusion":
        if self.production_controls_status == OperationalReadinessStatus.READY:
            if any("production-control" in blocker for blocker in self.blockers):
                raise ValueError("ready production controls cannot retain production-control blockers")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"conclusion_sha256"})
        )
        if self.conclusion_sha256 != expected:
            raise ValueError("operational readiness conclusion hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "OperationalReadinessConclusion":
        payload = dict(values)
        payload.setdefault("production_launch_authorized", False)
        payload["conclusion_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class HumanLaunchDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(min_length=1)
    release_version: str = Field(min_length=1)
    release_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    supported_dispositions: tuple[HumanDecisionDisposition, ...]
    decision_state: Literal[LaunchDecisionState.PENDING_HUMAN_DECISION] = (
        LaunchDecisionState.PENDING_HUMAN_DECISION
    )
    decision_authority: Literal["HUMAN"] = "HUMAN"
    selected_disposition: None = None
    request_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_request(self) -> "HumanLaunchDecisionRequest":
        if set(self.supported_dispositions) != set(HumanDecisionDisposition):
            raise ValueError("launch request must support all four human dispositions")
        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"request_sha256"})
        )
        if self.request_sha256 != expected:
            raise ValueError("human launch decision request hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "HumanLaunchDecisionRequest":
        payload = dict(values)
        payload.setdefault("decision_state", LaunchDecisionState.PENDING_HUMAN_DECISION)
        payload.setdefault("decision_authority", "HUMAN")
        payload.setdefault("selected_disposition", None)
        payload["request_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class EnkiOperationalReleasePackage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    release_version: Literal["enki-1.0-operational-rc1"] = OPERATIONAL_RELEASE_VERSION
    architecture_documents: tuple[str, ...]
    evidence: tuple[OperationalEvidencePointer, ...]
    production_controls: tuple[ProductionControlStatus, ...]
    readiness: OperationalReadinessConclusion
    known_limitations: tuple[str, ...]
    rollback_reference: str = Field(min_length=1)
    migration_reference: str = Field(min_length=1)
    independent_review_reference: str = Field(min_length=1)
    external_services_budget_usd: Literal[0] = 0
    production_launch_authorized: Literal[False] = False
    launch_decision_state: Literal[LaunchDecisionState.PENDING_HUMAN_DECISION] = (
        LaunchDecisionState.PENDING_HUMAN_DECISION
    )
    release_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_package(self) -> "EnkiOperationalReleasePackage":
        expected_architecture = {
            "architecture/enki/enki-split-cloud-reference-architecture.md",
            "architecture/enki/enki-canonical-nine-layer-architecture.md",
        }
        if set(self.architecture_documents) != expected_architecture:
            raise ValueError("operational release must bind exactly the corrected architecture baseline")

        domains = {item.domain for item in self.evidence}
        if domains != set(OperationalEvidenceDomain):
            raise ValueError("operational release must represent every evidence domain")

        controls = [item.control for item in self.production_controls]
        if set(controls) != set(ProductionControl) or len(controls) != len(set(controls)):
            raise ValueError("operational release must classify exactly all seven production controls")

        if self.readiness.production_controls_status == OperationalReadinessStatus.READY:
            if any(
                item.classification != ProductionControlClassification.VALIDATED
                for item in self.production_controls
            ):
                raise ValueError("production controls cannot be READY unless all controls are validated")

        if self.production_launch_authorized:
            raise ValueError("operational release package cannot self-authorize launch")

        expected = canonical_sha256(
            self.model_dump(mode="python", exclude={"release_sha256"})
        )
        if self.release_sha256 != expected:
            raise ValueError("operational release package hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "EnkiOperationalReleasePackage":
        payload = dict(values)
        payload.setdefault("schema_version", 1)
        payload.setdefault("release_version", OPERATIONAL_RELEASE_VERSION)
        payload.setdefault("external_services_budget_usd", 0)
        payload.setdefault("production_launch_authorized", False)
        payload.setdefault("launch_decision_state", LaunchDecisionState.PENDING_HUMAN_DECISION)
        payload["release_sha256"] = canonical_sha256(payload)
        return cls(**payload)


def _evidence(
    evidence_id: str,
    domain: OperationalEvidenceDomain,
    reference: str,
    status: OperationalEvidenceStatus,
    qualification: str,
) -> OperationalEvidencePointer:
    return OperationalEvidencePointer.create(
        evidence_id=evidence_id,
        domain=domain,
        reference=reference,
        status=status,
        qualification=qualification,
    )


def build_operational_release_package() -> EnkiOperationalReleasePackage:
    """Build the current evidence-bound release without manufacturing Sprint 45 evidence."""

    evidence = (
        _evidence("SOFTWARE-S42", OperationalEvidenceDomain.SOFTWARE, "records/sprints/NKS-SPR-042.json", OperationalEvidenceStatus.VALIDATED_TEST, "Governed hosted mutation runtime validated in TEST."),
        _evidence("ARCH-BASELINE", OperationalEvidenceDomain.ARCHITECTURE, "architecture/enki/enki-canonical-nine-layer-architecture.md", OperationalEvidenceStatus.VALIDATED, "Corrected nine-layer architecture is versioned and authoritative."),
        _evidence("HOSTING-S38", OperationalEvidenceDomain.HOSTING, "records/sprints/NKS-SPR-038.json", OperationalEvidenceStatus.VALIDATED_TEST, "Human-authorized CF-NEON-R2 architecture has deterministic TEST infrastructure definitions."),
        _evidence("SECURITY-S35", OperationalEvidenceDomain.SECURITY, "records/sprints/NKS-SPR-035.json", OperationalEvidenceStatus.CONDITIONAL, "Production-control contracts are defined; qualifying Sprint 45 production evidence is not yet present."),
        _evidence("IDENTITY-S39", OperationalEvidenceDomain.IDENTITY, "records/sprints/NKS-SPR-039.json", OperationalEvidenceStatus.VALIDATED_TEST, "Hosted identity and boundary enforcement validated adversarially in TEST."),
        _evidence("CANONICAL-S40", OperationalEvidenceDomain.CANONICAL_DATA, "records/sprints/NKS-SPR-040.json", OperationalEvidenceStatus.VALIDATED_TEST, "Physical temporal authority, migration, rollback, and reconstruction validated in TEST."),
        _evidence("EVIDENCE-S41", OperationalEvidenceDomain.EVIDENCE, "records/sprints/NKS-SPR-041.json", OperationalEvidenceStatus.VALIDATED_TEST, "Evidence/object plane and deterministic manifests validated in TEST."),
        _evidence("RECOVERY-S44", OperationalEvidenceDomain.RECOVERY, "records/sprints/NKS-SPR-044.json", OperationalEvidenceStatus.VALIDATED_TEST, "Disaster-recovery and provider-loss paths validated in TEST."),
        _evidence("PORTABILITY-S44", OperationalEvidenceDomain.PORTABILITY, "records/sprints/NKS-SPR-044.json", OperationalEvidenceStatus.VALIDATED_TEST, "Open deterministic export and provider-exit reconstruction validated in TEST."),
        _evidence("MULTI-S47", OperationalEvidenceDomain.MULTI_CONSUMER, "records/sprints/NKS-SPR-047.json", OperationalEvidenceStatus.VALIDATED_TEST, "All three downstream suites execute through isolated governed TEST boundaries."),
        _evidence("OPS-S46", OperationalEvidenceDomain.OPERATIONS, "records/sprints/NKS-SPR-046.json", OperationalEvidenceStatus.VALIDATED_TEST, "Privacy-preserving observability and incident reconstruction validated in TEST."),
        _evidence("COST-ZERO", OperationalEvidenceDomain.COST, "records/sprints/NKS-SPR-038.json", OperationalEvidenceStatus.CONDITIONAL, "Current validated path preserves the zero-dollar external-services boundary; production operating cost remains unvalidated."),
    )

    controls = tuple(
        ProductionControlStatus.create(
            control=control,
            classification=ProductionControlClassification.EXTERNALLY_REQUIRED,
            reason=(
                "Qualifying production-scope evidence is not present; Sprint 45 remains incomplete."
                if control != ProductionControl.INDEPENDENT_PENETRATION_TESTING
                else "An authorized independent assessor must perform and evidence penetration testing."
            ),
            qualifying_production_evidence_present=False,
            independent_assessment_required=(
                control == ProductionControl.INDEPENDENT_PENETRATION_TESTING
            ),
        )
        for control in ProductionControl
    )

    readiness = OperationalReadinessConclusion.create(
        software_ready=True,
        hosted_platform_status=OperationalReadinessStatus.CONDITIONAL,
        production_controls_status=OperationalReadinessStatus.NOT_READY,
        operational_status=OperationalReadinessStatus.CONDITIONAL,
        blockers=(
            "production-control-evidence-missing",
            "independent-penetration-testing-required",
            "production-operating-cost-unvalidated",
        ),
        statement=(
            "Enki software and hosted TEST operation are validated through the available evidence. "
            "Operational production launch remains not authorized because Sprint 45 production controls "
            "and independent assessment are incomplete."
        ),
    )

    return EnkiOperationalReleasePackage.create(
        architecture_documents=(
            "architecture/enki/enki-split-cloud-reference-architecture.md",
            "architecture/enki/enki-canonical-nine-layer-architecture.md",
        ),
        evidence=evidence,
        production_controls=controls,
        readiness=readiness,
        known_limitations=(
            "No qualifying Sprint 45 production-control validation evidence is currently bound.",
            "Independent penetration testing has not been performed by an authorized independent assessor.",
            "Production operating cost is not validated; the current execution program preserves an absolute zero-dollar external-services boundary.",
            "TEST success cannot satisfy a production launch gate.",
        ),
        rollback_reference="records/sprints/NKS-SPR-044.json",
        migration_reference="records/sprints/NKS-SPR-040.json",
        independent_review_reference="records/sprints/NKS-SPR-045.json",
    )


def build_human_launch_decision_request(
    release: EnkiOperationalReleasePackage,
) -> HumanLaunchDecisionRequest:
    return HumanLaunchDecisionRequest.create(
        request_id=f"{release.release_version}-launch-decision",
        release_version=release.release_version,
        release_sha256=release.release_sha256,
        supported_dispositions=tuple(HumanDecisionDisposition),
    )
