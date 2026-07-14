from __future__ import annotations

import pytest

from nks.enki.contracts import ConfidenceAssertion, ConfidenceLevel
from nks.enki.versioning import (
    CompatibilityStatus,
    ConfidenceUseDecision,
    ContractCompatibilityPolicy,
    ContractVersion,
    evaluate_confidence_for_authoritative_use,
)


def _policy() -> ContractCompatibilityPolicy:
    return ContractCompatibilityPolicy(
        contract_name="Observation",
        current_version=ContractVersion(major=2, minor=3),
        explicitly_supported_forward_versions={"2.4"},
        supported_legacy_major_versions={1},
    )


def test_contract_version_exact_path() -> None:
    assert _policy().assert_compatible(["2.3"]) == CompatibilityStatus.EXACT


def test_contract_version_backward_compatibility_paths() -> None:
    assert _policy().assert_compatible(["2.2"]) == CompatibilityStatus.BACKWARD_COMPATIBLE
    assert _policy().assert_compatible(["1.9"]) == CompatibilityStatus.BACKWARD_COMPATIBLE


def test_contract_version_explicit_forward_compatibility_path() -> None:
    assert _policy().assert_compatible(["2.4"]) == CompatibilityStatus.FORWARD_COMPATIBLE


def test_contract_version_unsupported_paths_fail_closed() -> None:
    assert _policy().evaluate(["2.5"]) == CompatibilityStatus.UNSUPPORTED
    assert _policy().evaluate(["3.0"]) == CompatibilityStatus.UNSUPPORTED
    with pytest.raises(ValueError, match="UNSUPPORTED"):
        _policy().assert_compatible(["3.0"])


def test_contract_version_ambiguous_paths_fail_closed() -> None:
    assert _policy().evaluate([]) == CompatibilityStatus.AMBIGUOUS
    assert _policy().evaluate(["2.2", "2.3"]) == CompatibilityStatus.AMBIGUOUS
    assert _policy().evaluate(["not-a-version"]) == CompatibilityStatus.AMBIGUOUS
    with pytest.raises(ValueError, match="AMBIGUOUS"):
        _policy().assert_compatible(["2.2", "2.3"])


def test_forward_compatibility_requires_explicit_same_major_declaration() -> None:
    with pytest.raises(ValueError, match="cannot cross a major"):
        ContractCompatibilityPolicy(
            contract_name="Observation",
            current_version=ContractVersion(major=2, minor=3),
            explicitly_supported_forward_versions={"3.0"},
        )


def test_unknown_confidence_is_deferred_not_upgraded() -> None:
    result = evaluate_confidence_for_authoritative_use(
        ConfidenceAssertion(
            level=ConfidenceLevel.UNKNOWN,
            rationale="Evidence is incomplete.",
            evidence_ids=[],
        ),
        known_evidence_ids=set(),
    )
    assert result.decision == ConfidenceUseDecision.DEFER


def test_non_unknown_confidence_requires_attributable_evidence() -> None:
    result = evaluate_confidence_for_authoritative_use(
        ConfidenceAssertion(
            level=ConfidenceLevel.HIGH,
            rationale="Unsupported assertion.",
            evidence_ids=[],
        ),
        known_evidence_ids=set(),
    )
    assert result.decision == ConfidenceUseDecision.REJECT


def test_unknown_evidence_reference_is_rejected() -> None:
    result = evaluate_confidence_for_authoritative_use(
        ConfidenceAssertion(
            level=ConfidenceLevel.MODERATE,
            rationale="Evidence cited.",
            evidence_ids=["E-MISSING"],
        ),
        known_evidence_ids={"E-OTHER"},
    )
    assert result.decision == ConfidenceUseDecision.REJECT
    assert "E-MISSING" in result.reasons[0]


def test_supported_confidence_is_accepted() -> None:
    result = evaluate_confidence_for_authoritative_use(
        ConfidenceAssertion(
            level=ConfidenceLevel.HIGH,
            rationale="Direct attributable evidence.",
            evidence_ids=["E-1"],
        ),
        known_evidence_ids={"E-1"},
    )
    assert result.decision == ConfidenceUseDecision.ACCEPT
