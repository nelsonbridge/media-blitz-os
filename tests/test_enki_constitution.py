from __future__ import annotations

from nks.enki.constitution import (
    ControlStatus,
    EnkiInvariant,
    TRACEABILITY_CONTROLS,
    validate_traceability,
)


def test_every_enki_invariant_has_one_traceability_control() -> None:
    assert validate_traceability() == []
    assert {control.invariant for control in TRACEABILITY_CONTROLS} == set(EnkiInvariant)
    assert len(TRACEABILITY_CONTROLS) == len(EnkiInvariant)


def test_implemented_controls_name_contract_service_and_test_evidence() -> None:
    implemented = [
        control
        for control in TRACEABILITY_CONTROLS
        if control.status == ControlStatus.IMPLEMENTED
    ]

    assert implemented
    for control in implemented:
        assert control.contract_refs
        assert control.service_refs
        assert control.test_refs


def test_traceability_registry_does_not_admit_product_specific_maturity_models() -> None:
    serialized = "\n".join(
        [
            *[ref for control in TRACEABILITY_CONTROLS for ref in control.contract_refs],
            *[ref for control in TRACEABILITY_CONTROLS for ref in control.service_refs],
        ]
    ).lower()

    assert "erikson" not in serialized
    assert "maturity_level" not in serialized
    assert "person_object" not in serialized
