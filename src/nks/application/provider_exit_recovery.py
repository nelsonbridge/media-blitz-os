"""Deterministic zero-cost provider-exit and disaster-recovery proof for Enki TEST."""
from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from nks.application.governed_transactions import canonical_sha256
from nks.governance.approvals import ExecutionContext

class ArtifactKind(StrEnum):
    PROJECTION = "PROJECTION"
    CACHE = "CACHE"
    REPLICA = "REPLICA"

class RestoreFailpoint(StrEnum):
    NONE = "NONE"
    AFTER_STATE = "AFTER_STATE"
    AFTER_OBJECTS = "AFTER_OBJECTS"

class AuthoritySemantics(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    authority_class: str
    authority_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    policy_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    consent_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    temporal_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    lineage_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

class StateRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    record_id: str
    tenant_id: str
    subject_id: str
    authority: AuthoritySemantics
    payload_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    receipt_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    recorded_at: datetime
    authoritative: Literal[True] = True

class ObjectRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    object_id: str
    content_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    linked_record_ids: tuple[str, ...] = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    recorded_at: datetime
    authoritative: Literal[False] = False

class NonCanonicalArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    artifact_id: str
    kind: ArtifactKind
    source_record_ids: tuple[str, ...]
    content_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    authoritative: Literal[False] = False

class ProviderBackup(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["enki-provider-exit/v1"] = "enki-provider-exit/v1"
    backup_id: str
    source_provider_id: str
    execution_context: Literal[ExecutionContext.TEST] = ExecutionContext.TEST
    snapshot_at: datetime
    state_records: tuple[StateRecord, ...]
    object_records: tuple[ObjectRecord, ...]
    noncanonical_hashes: tuple[str, ...]
    state_fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    object_fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    manifest_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    @model_validator(mode="after")
    def validate_integrity(self) -> "ProviderBackup":
        state = tuple(sorted(self.state_records, key=lambda x: x.record_id))
        objects = tuple(sorted(self.object_records, key=lambda x: x.object_id))
        if len({x.record_id for x in state}) != len(state): raise ValueError("duplicate state id")
        if len({x.object_id for x in objects}) != len(objects): raise ValueError("duplicate object id")
        known = {x.record_id for x in state}
        if any(not set(x.linked_record_ids).issubset(known) for x in objects): raise ValueError("orphan object evidence")
        if self.state_fingerprint != canonical_sha256(state): raise ValueError("state fingerprint mismatch")
        if self.object_fingerprint != canonical_sha256(objects): raise ValueError("object fingerprint mismatch")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"manifest_sha256"}))
        if self.manifest_sha256 != expected: raise ValueError("backup manifest mismatch")
        return self

class RecoveryReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    recovery_id: str
    backup_id: str
    source_provider_id: str
    destination_provider_id: str
    state_fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    object_fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    prior_destination_fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    restored_exactly: bool
    rolled_back: bool
    ignored_noncanonical_count: int = Field(ge=0)
    provider_certification: Literal[False] = False
    production_effect: Literal[False] = False
    receipt_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    @model_validator(mode="after")
    def validate_receipt(self) -> "RecoveryReceipt":
        if self.restored_exactly and self.rolled_back: raise ValueError("rollback cannot claim restore")
        expected = canonical_sha256(self.model_dump(mode="python", exclude={"receipt_sha256"}))
        if self.receipt_sha256 != expected: raise ValueError("recovery receipt mismatch")
        return self
    @classmethod
    def create(cls, **values: object) -> "RecoveryReceipt":
        p=dict(values); p["receipt_sha256"]=canonical_sha256(p); return cls(**p)

class TestProviderDouble:
    def __init__(self, provider_id: str) -> None:
        self.provider_id=provider_id; self.available=True
        self.state: dict[str, StateRecord]={}; self.objects: dict[str, ObjectRecord]={}; self.noncanonical: dict[str, NonCanonicalArtifact]={}
    def require(self) -> None:
        if not self.available: raise ConnectionError(f"provider unavailable: {self.provider_id}")
    def add_state(self, item: StateRecord) -> None: self.require(); self.state[item.record_id]=item
    def add_object(self, item: ObjectRecord) -> None: self.require(); self.objects[item.object_id]=item
    def add_noncanonical(self, item: NonCanonicalArtifact) -> None: self.require(); self.noncanonical[item.artifact_id]=item
    def state_fingerprint(self) -> str: return canonical_sha256(tuple(sorted(self.state.values(), key=lambda x:x.record_id)))
    def object_fingerprint(self) -> str: return canonical_sha256(tuple(sorted(self.objects.values(), key=lambda x:x.object_id)))
    def fingerprint(self) -> str: return canonical_sha256({"state":self.state_fingerprint(),"objects":self.object_fingerprint()})
    def snapshot(self): return dict(self.state), dict(self.objects), dict(self.noncanonical)
    def reset(self, snap) -> None: self.state, self.objects, self.noncanonical = dict(snap[0]), dict(snap[1]), dict(snap[2])

class ProviderExitService:
    @staticmethod
    def backup(source: TestProviderDouble, *, backup_id: str, snapshot_at: datetime) -> ProviderBackup:
        source.require()
        state=tuple(sorted((x for x in source.state.values() if x.recorded_at<=snapshot_at), key=lambda x:x.record_id))
        known={x.record_id for x in state}
        objects=tuple(sorted((x for x in source.objects.values() if x.recorded_at<=snapshot_at and set(x.linked_record_ids).issubset(known)), key=lambda x:x.object_id))
        p={"schema_version":"enki-provider-exit/v1","backup_id":backup_id,"source_provider_id":source.provider_id,"execution_context":ExecutionContext.TEST,"snapshot_at":snapshot_at,"state_records":state,"object_records":objects,"noncanonical_hashes":tuple(sorted(canonical_sha256(x) for x in source.noncanonical.values())),"state_fingerprint":canonical_sha256(state),"object_fingerprint":canonical_sha256(objects)}
        return ProviderBackup(**p, manifest_sha256=canonical_sha256(p))
    @staticmethod
    def restore(backup: ProviderBackup, destination: TestProviderDouble, *, failpoint: RestoreFailpoint=RestoreFailpoint.NONE) -> RecoveryReceipt:
        ProviderBackup.model_validate(backup.model_dump(mode="python")); destination.require(); prior=destination.snapshot(); prior_fp=destination.fingerprint()
        try:
            for x in backup.state_records: destination.add_state(x)
            if failpoint==RestoreFailpoint.AFTER_STATE: raise RuntimeError("simulated restore interruption")
            for x in backup.object_records: destination.add_object(x)
            if failpoint==RestoreFailpoint.AFTER_OBJECTS: raise RuntimeError("simulated restore interruption")
            if destination.state_fingerprint()!=backup.state_fingerprint or destination.object_fingerprint()!=backup.object_fingerprint: raise RuntimeError("restore fingerprint mismatch")
            return RecoveryReceipt.create(recovery_id=f"RECOVERY-{backup.backup_id}",backup_id=backup.backup_id,source_provider_id=backup.source_provider_id,destination_provider_id=destination.provider_id,state_fingerprint=destination.state_fingerprint(),object_fingerprint=destination.object_fingerprint(),prior_destination_fingerprint=prior_fp,restored_exactly=True,rolled_back=False,ignored_noncanonical_count=len(backup.noncanonical_hashes),provider_certification=False,production_effect=False)
        except Exception:
            destination.reset(prior); raise
    @staticmethod
    def restore_with_rollback(backup: ProviderBackup, destination: TestProviderDouble, *, failpoint: RestoreFailpoint) -> RecoveryReceipt:
        prior=destination.snapshot(); prior_fp=destination.fingerprint()
        try: return ProviderExitService.restore(backup,destination,failpoint=failpoint)
        except Exception:
            destination.reset(prior)
            return RecoveryReceipt.create(recovery_id=f"ROLLBACK-{backup.backup_id}",backup_id=backup.backup_id,source_provider_id=backup.source_provider_id,destination_provider_id=destination.provider_id,state_fingerprint=destination.state_fingerprint(),object_fingerprint=destination.object_fingerprint(),prior_destination_fingerprint=prior_fp,restored_exactly=False,rolled_back=True,ignored_noncanonical_count=len(backup.noncanonical_hashes),provider_certification=False,production_effect=False)
