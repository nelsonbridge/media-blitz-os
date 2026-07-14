"""Application workflows that keep reconciliation and disclosure independent."""

from __future__ import annotations

from nks.enki.contracts import ReconciliationRequest, ReconciliationResult
from nks.enki.disclosure import (
    ConservativeDisclosureService,
    DisclosureContext,
    DisclosureResult,
)
from nks.enki.ports import DisclosureReceiptWriter, FindingWriter
from nks.enki.reconciliation import ReconciliationEngine


class ReconcileAndRecord:
    """Run reconciliation and optionally persist the resulting findings.

    Recording findings does not imply that they have been disclosed to any
    audience. The writer remains optional so pure TEST execution can remain
    side-effect free.
    """

    def __init__(
        self,
        engine: ReconciliationEngine,
        *,
        finding_writer: FindingWriter | None = None,
    ) -> None:
        self._engine = engine
        self._finding_writer = finding_writer

    def execute(self, request: ReconciliationRequest) -> ReconciliationResult:
        result = self._engine.execute(request)
        if self._finding_writer is not None:
            self._finding_writer.append_findings(result.findings)
        return result


class DiscloseAndRecord:
    """Evaluate disclosure separately and optionally persist its receipt."""

    def __init__(
        self,
        service: ConservativeDisclosureService | None = None,
        *,
        receipt_writer: DisclosureReceiptWriter | None = None,
    ) -> None:
        self._service = service or ConservativeDisclosureService()
        self._receipt_writer = receipt_writer

    def execute(
        self,
        result: ReconciliationResult,
        context: DisclosureContext,
    ) -> DisclosureResult:
        disclosure = self._service.evaluate(result, context)
        if self._receipt_writer is not None:
            self._receipt_writer.append_disclosure_receipt(disclosure.receipt)
        return disclosure
