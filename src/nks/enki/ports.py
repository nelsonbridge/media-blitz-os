"""Ports that keep Enki core independent from persistence and products."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Protocol

from nks.enki.contracts import (
    DisclosureDecision,
    Observation,
    ReconciliationFinding,
    ReconciliationRequest,
    RelationshipAssertion,
    SubjectRef,
)
from nks.enki.disclosure import DisclosureReceipt


class ObservationReader(Protocol):
    def list_observations(self, subject: SubjectRef, domain: str) -> Sequence[Observation]: ...


class RelationshipReader(Protocol):
    def list_relationships(
        self,
        subject: SubjectRef,
        domain: str,
    ) -> Sequence[RelationshipAssertion]: ...


class FindingWriter(Protocol):
    def append_findings(self, findings: Iterable[ReconciliationFinding]) -> None: ...


class DisclosureReceiptWriter(Protocol):
    def append_disclosure_receipt(self, receipt: DisclosureReceipt) -> None: ...


class DisclosureEvaluator(Protocol):
    def evaluate(
        self,
        request: ReconciliationRequest,
        findings: Sequence[ReconciliationFinding],
    ) -> Sequence[DisclosureDecision]: ...


class ReconciliationStrategy(Protocol):
    def reconcile(self, request: ReconciliationRequest) -> Sequence[ReconciliationFinding]: ...
