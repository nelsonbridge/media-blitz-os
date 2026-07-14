"""Repository audit capabilities for the Nelson Knowledge System."""

from nks.audit import repository as _repository

# Register append-only governed transaction families with the canonical census.
# Package initialization runs before direct ``nks.audit.repository`` imports, so
# audit entry points observe the extended collections and identifier contracts.
_repository.RECORD_COLLECTIONS = (
    *_repository.RECORD_COLLECTIONS,
    "governed-transaction-events",
    "governed-transaction-receipts",
)
_repository.IDENTIFIER_FIELDS_BY_COLLECTION.update(
    {
        "governed-transaction-events": ("event_id",),
        "governed-transaction-receipts": ("receipt_id",),
    }
)

AuditResult = _repository.AuditResult
audit_repository = _repository.audit_repository

__all__ = ["AuditResult", "audit_repository"]
