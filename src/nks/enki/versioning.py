"""Fail-closed Enki contract version compatibility and confidence-use rules."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.enki.contracts import ConfidenceAssertion, ConfidenceLevel


class CompatibilityStatus(StrEnum):
    EXACT = "EXACT"
    BACKWARD_COMPATIBLE = "BACKWARD_COMPATIBLE"
    FORWARD_COMPATIBLE = "FORWARD_COMPATIBLE"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"


class ContractVersion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, order=True)

    major: int = Field(ge=1)
    minor: int = Field(ge=0)

    @classmethod
    def parse(cls, value: str) -> "ContractVersion":
        parts = value.split(".")
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            raise ValueError("contract version must use MAJOR.MINOR")
        return cls(major=int(parts[0]), minor=int(parts[1]))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"


class ContractCompatibilityPolicy(BaseModel):
    """Compatibility rules for one named Enki contract family."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: str = Field(min_length=1)
    current_version: ContractVersion
    explicitly_supported_forward_versions: set[str] = Field(default_factory=set)
    supported_legacy_major_versions: set[int] = Field(default_factory=set)

    @model_validator(mode="after")
    def validate_forward_versions(self) -> "ContractCompatibilityPolicy":
        for version_text in self.explicitly_supported_forward_versions:
            version = ContractVersion.parse(version_text)
            if version.major != self.current_version.major:
                raise ValueError("forward compatibility cannot cross a major version")
            if version.minor <= self.current_version.minor:
                raise ValueError("forward versions must be newer than current")
        return self

    def evaluate(self, declared_versions: list[str]) -> CompatibilityStatus:
        unique = set(declared_versions)
        if len(unique) != 1:
            return CompatibilityStatus.AMBIGUOUS
        try:
            observed = ContractVersion.parse(next(iter(unique)))
        except ValueError:
            return CompatibilityStatus.AMBIGUOUS

        current = self.current_version
        if observed == current:
            return CompatibilityStatus.EXACT
        if observed.major == current.major and observed.minor < current.minor:
            return CompatibilityStatus.BACKWARD_COMPATIBLE
        if str(observed) in self.explicitly_supported_forward_versions:
            return CompatibilityStatus.FORWARD_COMPATIBLE
        if observed.major in self.supported_legacy_major_versions:
            return CompatibilityStatus.BACKWARD_COMPATIBLE
        return CompatibilityStatus.UNSUPPORTED

    def assert_compatible(self, declared_versions: list[str]) -> CompatibilityStatus:
        status = self.evaluate(declared_versions)
        if status in {CompatibilityStatus.UNSUPPORTED, CompatibilityStatus.AMBIGUOUS}:
            raise ValueError(f"contract version is {status.value}")
        return status


class ConfidenceUseDecision(StrEnum):
    ACCEPT = "ACCEPT"
    DEFER = "DEFER"
    REJECT = "REJECT"


class ConfidenceUseResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: ConfidenceUseDecision
    reasons: list[str] = Field(default_factory=list)


def evaluate_confidence_for_authoritative_use(
    assertion: ConfidenceAssertion,
    *,
    known_evidence_ids: set[str],
) -> ConfidenceUseResult:
    """Preserve uncertainty and reject unsupported confidence claims."""

    unknown_evidence = set(assertion.evidence_ids) - known_evidence_ids
    if unknown_evidence:
        return ConfidenceUseResult(
            decision=ConfidenceUseDecision.REJECT,
            reasons=[f"unknown evidence ids: {sorted(unknown_evidence)}"],
        )
    if assertion.level == ConfidenceLevel.UNKNOWN:
        return ConfidenceUseResult(
            decision=ConfidenceUseDecision.DEFER,
            reasons=["UNKNOWN confidence cannot control authoritative use"],
        )
    if not assertion.evidence_ids:
        return ConfidenceUseResult(
            decision=ConfidenceUseDecision.REJECT,
            reasons=["non-UNKNOWN confidence requires attributable evidence"],
        )
    return ConfidenceUseResult(
        decision=ConfidenceUseDecision.ACCEPT,
        reasons=["confidence is attributable and supported"],
    )
