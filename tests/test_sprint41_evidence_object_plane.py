from __future__ import annotations
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from nks.application.evidence_object_plane import (
    EvidenceObject, EvidenceObjectPlane, LifecycleState, PackageKind,
    PackageManifest, PortableObjectBundle, TestObjectStore,
)
from nks.application.governed_transactions import canonical_sha256
from nks.application.sprint41_path_manifest import sprint41_evidence_object_plane_path_manifest
from nks.governance.approvals import ExecutionContext

NOW=datetime(2026,7,17,10,0,tzinfo=timezone.utc)
CANONICAL={"R1":canonical_sha256("canonical-1"),"R2":canonical_sha256("canonical-2")}
AUTH=canonical_sha256("retention-authority")

def plane(provider:str="object-provider-a"):
    return EvidenceObjectPlane(canonical_record_hashes=CANONICAL,store=TestObjectStore(provider))

def seed(p:EvidenceObjectPlane):
    a=p.put(object_id="O1",logical_key="evidence/source-1",evidence_type="source",content="synthetic evidence one",canonical_refs=("R1",),created_at=NOW)
    b=p.put(object_id="O2",logical_key="evidence/source-2",evidence_type="proof",content="synthetic evidence two",canonical_refs=("R2","R1"),created_at=NOW)
    return a,b

def test_objects_are_distinct_from_but_hash_linked_to_canonical_state() -> None:
    p=plane(); a,b=seed(p)
    assert a.authoritative is False and b.authoritative is False
    assert a.canonical_record_hashes==(CANONICAL["R1"],)
    assert b.canonical_record_refs==("R1","R2")
    assert b.canonical_record_hashes==(CANONICAL["R1"],CANONICAL["R2"])
    assert p.store.provider_key("O1")!=a.logical_key
    payload=a.model_dump(mode="python"); payload["authoritative"]=True
    with pytest.raises(ValidationError): EvidenceObject.model_validate(payload)


def test_all_package_families_use_deterministic_manifests() -> None:
    for kind in PackageKind:
        p=plane(); seed(p)
        first=p.manifest(package_id=f"PKG-{kind.value}",kind=kind,object_ids=("O2","O1"),created_at=NOW)
        second=p.manifest(package_id=f"PKG-{kind.value}",kind=kind,object_ids=("O1","O2"),created_at=NOW)
        assert first==second
        assert first.object_ids==("O1","O2")
        p.verify_manifest(first)


def test_archive_tombstone_delete_preserve_append_only_history() -> None:
    p=plane(); seed(p)
    e1=p.transition("O1",LifecycleState.ARCHIVED,reason="retention",authority_sha256=AUTH,recorded_at=NOW)
    e2=p.transition("O1",LifecycleState.TOMBSTONED,reason="expiry",authority_sha256=AUTH,recorded_at=NOW)
    e3=p.transition("O1",LifecycleState.DELETED,reason="governed-delete",authority_sha256=AUTH,recorded_at=NOW)
    assert [x.to_state for x in p.store.lifecycle["O1"]]==[LifecycleState.ARCHIVED,LifecycleState.TOMBSTONED,LifecycleState.DELETED]
    assert e2.previous_event_sha256==e1.event_sha256 and e3.previous_event_sha256==e2.event_sha256
    assert "O1" not in p.store.content
    assert "O1" in p.store.objects
    assert p.store.objects["O1"].authoritative is False
    with pytest.raises(ValidationError):
        p.transition("O1",LifecycleState.ACTIVE,reason="illegal",authority_sha256=AUTH,recorded_at=NOW)


def test_orphan_corruption_missing_and_manifest_tamper_fail_closed() -> None:
    p=plane(); seed(p)
    with pytest.raises(ValueError,match="orphan"):
        p.put(object_id="ORPHAN",logical_key="orphan",evidence_type="bad",content="x",canonical_refs=("MISSING",),created_at=NOW)
    p.store.content["O1"]="corrupted"
    with pytest.raises(ValueError,match="corruption"): p.read("O1")
    del p.store.content["O2"]
    with pytest.raises(FileNotFoundError): p.read("O2")

    q=plane(); seed(q); manifest=q.manifest(package_id="PKG-TAMPER",kind=PackageKind.AUDIT,object_ids=("O1",),created_at=NOW)
    payload=manifest.model_dump(mode="python"); payload["object_hashes"]=("sha256:"+"0"*64,)
    with pytest.raises(ValidationError): PackageManifest.model_validate(payload)


def test_portable_export_and_clean_room_import_reconstruct_exact_relationships() -> None:
    source=plane("provider-a"); seed(source)
    source.manifest(package_id="PKG-PUB",kind=PackageKind.PUBLICATION,object_ids=("O1","O2"),created_at=NOW)
    source.transition("O2",LifecycleState.ARCHIVED,reason="cold-retention",authority_sha256=AUTH,recorded_at=NOW)
    first=source.export_bundle(); second=source.export_bundle()
    assert first==second and first.bundle_sha256==second.bundle_sha256

    destination=TestObjectStore("provider-b")
    restored=EvidenceObjectPlane.import_bundle(first,canonical_record_hashes=CANONICAL,destination=destination)
    assert restored.store.provider_key("O1")!=source.store.provider_key("O1")
    assert restored.store.objects==source.store.objects
    assert restored.store.content==source.store.content
    assert restored.store.manifests==source.store.manifests
    assert restored.store.lifecycle==source.store.lifecycle
    assert restored.export_bundle().objects==first.objects


def test_portable_bundle_rejects_content_tamper_and_canonical_relationship_mismatch() -> None:
    source=plane(); seed(source); source.manifest(package_id="PKG-X",kind=PackageKind.EXPORT,object_ids=("O1",),created_at=NOW)
    bundle=source.export_bundle(); payload=bundle.model_dump(mode="python"); payload["content_by_object_id"]["O1"]="tampered"
    payload["bundle_sha256"]=canonical_sha256({k:v for k,v in payload.items() if k!="bundle_sha256"})
    with pytest.raises(ValidationError): PortableObjectBundle.model_validate(payload)
    with pytest.raises(ValueError,match="canonical relationship mismatch"):
        EvidenceObjectPlane.import_bundle(bundle,canonical_record_hashes={"R1":canonical_sha256("wrong"),"R2":CANONICAL["R2"]},destination=TestObjectStore("provider-c"))


def test_deleted_content_remains_historical_metadata_not_recreated_as_authority() -> None:
    p=plane(); seed(p)
    p.transition("O1",LifecycleState.TOMBSTONED,reason="expiry",authority_sha256=AUTH,recorded_at=NOW)
    p.transition("O1",LifecycleState.DELETED,reason="delete",authority_sha256=AUTH,recorded_at=NOW)
    bundle=p.export_bundle()
    restored=EvidenceObjectPlane.import_bundle(bundle,canonical_record_hashes=CANONICAL,destination=TestObjectStore("provider-d"))
    assert restored.store.current_state("O1")==LifecycleState.DELETED
    assert "O1" not in restored.store.content
    assert restored.store.objects["O1"].authoritative is False


SPRINT41_TESTED_PATHS={
"evidence-canonical-hash-link","provider-key-nonauthoritative","publication-manifest-deterministic","model-use-manifest-deterministic",
"audit-manifest-deterministic","export-manifest-deterministic","backup-manifest-deterministic","recovery-manifest-deterministic",
"archive-history-preserved","tombstone-history-preserved","deletion-history-preserved","portable-export-deterministic",
"clean-room-relationship-reconstruction","exact-provider-independent-logical-identity","orphan-evidence-denied","object-corruption-denied",
"missing-object-denied","manifest-tamper-denied","illegal-lifecycle-transition-denied","deleted-content-cannot-reappear-as-authority",
"provider-object-key-cannot-become-authority","portable-clean-room-import"}

def test_declared_sprint41_paths_have_coverage_and_test_boundary() -> None:
    manifest=sprint41_evidence_object_plane_path_manifest(); manifest.assert_complete_coverage(SPRINT41_TESTED_PATHS)
    assert manifest.execution_context==ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "object-store-authority" in path.prohibited_effects
        assert "direct-canonical-write" in path.prohibited_effects
        assert "orphan-evidence" in path.prohibited_effects
        assert "noncanonical-promotion" in path.prohibited_effects
