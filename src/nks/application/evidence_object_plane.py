"""Provider-neutral evidence/object plane for zero-cost Enki TEST execution.

Object storage is never canonical authority. Evidence objects, package manifests,
lifecycle history, and portable bundles remain hash-linked to externally supplied
canonical record hashes while preserving provider portability.
"""
from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from nks.application.governed_transactions import canonical_sha256
from nks.governance.approvals import ExecutionContext

class PackageKind(StrEnum):
    PUBLICATION="PUBLICATION"; MODEL_USE="MODEL_USE"; AUDIT="AUDIT"
    EXPORT="EXPORT"; BACKUP="BACKUP"; RECOVERY="RECOVERY"

class LifecycleState(StrEnum):
    ACTIVE="ACTIVE"; ARCHIVED="ARCHIVED"; TOMBSTONED="TOMBSTONED"; DELETED="DELETED"

_ALLOWED_TRANSITIONS={
    LifecycleState.ACTIVE:{LifecycleState.ARCHIVED,LifecycleState.TOMBSTONED},
    LifecycleState.ARCHIVED:{LifecycleState.ACTIVE,LifecycleState.TOMBSTONED},
    LifecycleState.TOMBSTONED:{LifecycleState.DELETED},
    LifecycleState.DELETED:set(),
}

class EvidenceObject(BaseModel):
    model_config=ConfigDict(extra="forbid",frozen=True)
    object_id:str=Field(min_length=1)
    logical_key:str=Field(min_length=1)
    evidence_type:str=Field(min_length=1)
    content_sha256:str=Field(pattern=r"^sha256:[0-9a-f]{64}$")
    canonical_record_refs:tuple[str,...]=Field(min_length=1)
    canonical_record_hashes:tuple[str,...]=Field(min_length=1)
    created_at:datetime
    authoritative:Literal[False]=False
    metadata_sha256:str=Field(pattern=r"^sha256:[0-9a-f]{64}$")
    @model_validator(mode="after")
    def validate_metadata(self)->"EvidenceObject":
        if len(self.canonical_record_refs)!=len(self.canonical_record_hashes):
            raise ValueError("canonical reference/hash cardinality mismatch")
        if len(set(self.canonical_record_refs))!=len(self.canonical_record_refs):
            raise ValueError("canonical record references must be unique")
        expected=canonical_sha256(self.model_dump(mode="python",exclude={"metadata_sha256"}))
        if self.metadata_sha256!=expected: raise ValueError("evidence object metadata hash mismatch")
        return self
    @classmethod
    def create(cls,**values:object)->"EvidenceObject":
        p=dict(values); p["metadata_sha256"]=canonical_sha256(p); return cls(**p)

class LifecycleEvent(BaseModel):
    model_config=ConfigDict(extra="forbid",frozen=True)
    event_id:str; object_id:str
    from_state:LifecycleState; to_state:LifecycleState
    reason:str=Field(min_length=1)
    authority_sha256:str=Field(pattern=r"^sha256:[0-9a-f]{64}$")
    previous_event_sha256:str|None=Field(default=None,pattern=r"^sha256:[0-9a-f]{64}$")
    recorded_at:datetime
    event_sha256:str=Field(pattern=r"^sha256:[0-9a-f]{64}$")
    @model_validator(mode="after")
    def validate_event(self)->"LifecycleEvent":
        if self.to_state not in _ALLOWED_TRANSITIONS[self.from_state]:
            raise ValueError("illegal evidence lifecycle transition")
        expected=canonical_sha256(self.model_dump(mode="python",exclude={"event_sha256"}))
        if self.event_sha256!=expected: raise ValueError("lifecycle event hash mismatch")
        return self
    @classmethod
    def create(cls,**values:object)->"LifecycleEvent":
        p=dict(values); p["event_sha256"]=canonical_sha256(p); return cls(**p)

class PackageManifest(BaseModel):
    model_config=ConfigDict(extra="forbid",frozen=True)
    package_id:str; kind:PackageKind
    execution_context:Literal[ExecutionContext.TEST]=ExecutionContext.TEST
    canonical_record_refs:tuple[str,...]
    canonical_record_hashes:tuple[str,...]
    object_ids:tuple[str,...]=Field(min_length=1)
    object_hashes:tuple[str,...]=Field(min_length=1)
    created_at:datetime
    manifest_sha256:str=Field(pattern=r"^sha256:[0-9a-f]{64}$")
    @model_validator(mode="after")
    def validate_manifest(self)->"PackageManifest":
        if len(self.canonical_record_refs)!=len(self.canonical_record_hashes): raise ValueError("canonical manifest reference/hash mismatch")
        if len(self.object_ids)!=len(self.object_hashes): raise ValueError("object manifest id/hash mismatch")
        expected=canonical_sha256(self.model_dump(mode="python",exclude={"manifest_sha256"}))
        if self.manifest_sha256!=expected: raise ValueError("package manifest hash mismatch")
        return self
    @classmethod
    def create(cls,**values:object)->"PackageManifest":
        p=dict(values); p["manifest_sha256"]=canonical_sha256(p); return cls(**p)

class PortableObjectBundle(BaseModel):
    model_config=ConfigDict(extra="forbid",frozen=True)
    schema_version:Literal["enki-object-plane/v1"]="enki-object-plane/v1"
    source_provider_id:str
    objects:tuple[EvidenceObject,...]
    manifests:tuple[PackageManifest,...]
    lifecycle_events:tuple[LifecycleEvent,...]
    content_by_object_id:dict[str,str]
    bundle_sha256:str=Field(pattern=r"^sha256:[0-9a-f]{64}$")
    @model_validator(mode="after")
    def validate_bundle(self)->"PortableObjectBundle":
        known={x.object_id:x for x in self.objects}
        if len(known)!=len(self.objects): raise ValueError("portable object ids must be unique")
        for object_id,content in self.content_by_object_id.items():
            if object_id not in known: raise ValueError("portable content has no object metadata")
            if canonical_sha256(content)!=known[object_id].content_sha256: raise ValueError("portable object content hash mismatch")
        for manifest in self.manifests:
            if not set(manifest.object_ids).issubset(known): raise ValueError("portable manifest references missing object")
        expected=canonical_sha256(self.model_dump(mode="python",exclude={"bundle_sha256"}))
        if self.bundle_sha256!=expected: raise ValueError("portable object bundle hash mismatch")
        return self
    @classmethod
    def create(cls,**values:object)->"PortableObjectBundle":
        p=dict(values); p["bundle_sha256"]=canonical_sha256(p); return cls(**p)

class TestObjectStore:
    """In-memory provider double. Internal provider keys never confer authority."""
    def __init__(self,provider_id:str)->None:
        self.provider_id=provider_id; self.objects:dict[str,EvidenceObject]={}; self.content:dict[str,str]={}
        self.manifests:dict[str,PackageManifest]={}; self.lifecycle:dict[str,list[LifecycleEvent]]={}
    def provider_key(self,object_id:str)->str: return f"{self.provider_id}/objects/{object_id}"
    def current_state(self,object_id:str)->LifecycleState:
        events=self.lifecycle.get(object_id,[]); return events[-1].to_state if events else LifecycleState.ACTIVE

class EvidenceObjectPlane:
    def __init__(self,*,canonical_record_hashes:dict[str,str],store:TestObjectStore)->None:
        self._canonical=dict(canonical_record_hashes); self.store=store
    def put(self,*,object_id:str,logical_key:str,evidence_type:str,content:str,canonical_refs:tuple[str,...],created_at:datetime)->EvidenceObject:
        if not canonical_refs or not set(canonical_refs).issubset(self._canonical): raise ValueError("orphan evidence canonical reference")
        refs=tuple(sorted(canonical_refs)); hashes=tuple(self._canonical[x] for x in refs)
        item=EvidenceObject.create(object_id=object_id,logical_key=logical_key,evidence_type=evidence_type,content_sha256=canonical_sha256(content),canonical_record_refs=refs,canonical_record_hashes=hashes,created_at=created_at,authoritative=False)
        existing=self.store.objects.get(object_id)
        if existing is not None and (existing!=item or self.store.content.get(object_id)!=content): raise ValueError("immutable evidence object conflict")
        self.store.objects[object_id]=item; self.store.content[object_id]=content; self.store.lifecycle.setdefault(object_id,[])
        return item
    def read(self,object_id:str)->str:
        item=self.store.objects.get(object_id)
        if item is None: raise FileNotFoundError("evidence object missing")
        content=self.store.content.get(object_id)
        if content is None: raise FileNotFoundError("evidence object content missing")
        if canonical_sha256(content)!=item.content_sha256: raise ValueError("evidence object corruption detected")
        return content
    def transition(self,object_id:str,to_state:LifecycleState,*,reason:str,authority_sha256:str,recorded_at:datetime)->LifecycleEvent:
        if object_id not in self.store.objects: raise FileNotFoundError("evidence object missing")
        events=self.store.lifecycle.setdefault(object_id,[]); current=self.store.current_state(object_id)
        event=LifecycleEvent.create(event_id=f"LIFE-{object_id}-{len(events)+1}",object_id=object_id,from_state=current,to_state=to_state,reason=reason,authority_sha256=authority_sha256,previous_event_sha256=events[-1].event_sha256 if events else None,recorded_at=recorded_at)
        events.append(event)
        if to_state==LifecycleState.DELETED: self.store.content.pop(object_id,None)
        return event
    def manifest(self,*,package_id:str,kind:PackageKind,object_ids:tuple[str,...],created_at:datetime)->PackageManifest:
        ids=tuple(sorted(object_ids)); objects=[]
        for object_id in ids:
            self.read(object_id); objects.append(self.store.objects[object_id])
        canonical_refs=tuple(sorted({ref for item in objects for ref in item.canonical_record_refs}))
        hashes=tuple(self._canonical[x] for x in canonical_refs)
        manifest=PackageManifest.create(package_id=package_id,kind=kind,execution_context=ExecutionContext.TEST,canonical_record_refs=canonical_refs,canonical_record_hashes=hashes,object_ids=ids,object_hashes=tuple(self.store.objects[x].content_sha256 for x in ids),created_at=created_at)
        existing=self.store.manifests.get(package_id)
        if existing is not None and existing!=manifest: raise ValueError("immutable package manifest conflict")
        self.store.manifests[package_id]=manifest; return manifest
    def verify_manifest(self,manifest:PackageManifest)->None:
        PackageManifest.model_validate(manifest.model_dump(mode="python"))
        for object_id,expected_hash in zip(manifest.object_ids,manifest.object_hashes):
            self.read(object_id)
            if self.store.objects[object_id].content_sha256!=expected_hash: raise ValueError("manifest object hash mismatch")
        for ref,expected_hash in zip(manifest.canonical_record_refs,manifest.canonical_record_hashes):
            if self._canonical.get(ref)!=expected_hash: raise ValueError("manifest canonical link mismatch")
    def export_bundle(self)->PortableObjectBundle:
        content={object_id:self.read(object_id) for object_id in sorted(self.store.content)}
        return PortableObjectBundle.create(source_provider_id=self.store.provider_id,objects=tuple(sorted(self.store.objects.values(),key=lambda x:x.object_id)),manifests=tuple(sorted(self.store.manifests.values(),key=lambda x:x.package_id)),lifecycle_events=tuple(event for key in sorted(self.store.lifecycle) for event in self.store.lifecycle[key]),content_by_object_id=content)
    @classmethod
    def import_bundle(cls,bundle:PortableObjectBundle,*,canonical_record_hashes:dict[str,str],destination:TestObjectStore)->"EvidenceObjectPlane":
        PortableObjectBundle.model_validate(bundle.model_dump(mode="python")); plane=cls(canonical_record_hashes=canonical_record_hashes,store=destination)
        for item in bundle.objects:
            for ref,expected_hash in zip(item.canonical_record_refs,item.canonical_record_hashes):
                if canonical_record_hashes.get(ref)!=expected_hash: raise ValueError("portable canonical relationship mismatch")
            destination.objects[item.object_id]=item
            if item.object_id in bundle.content_by_object_id: destination.content[item.object_id]=bundle.content_by_object_id[item.object_id]
            destination.lifecycle.setdefault(item.object_id,[])
        for event in bundle.lifecycle_events: destination.lifecycle.setdefault(event.object_id,[]).append(event)
        for manifest in bundle.manifests: destination.manifests[manifest.package_id]=manifest; plane.verify_manifest(manifest)
        return plane
