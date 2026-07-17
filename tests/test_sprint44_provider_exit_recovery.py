from __future__ import annotations
from datetime import datetime, timedelta, timezone
import json
import pytest
from pydantic import ValidationError
from nks.application.governed_transactions import canonical_sha256
from nks.application.provider_exit_recovery import (
    ArtifactKind, AuthoritySemantics, NonCanonicalArtifact, ObjectRecord,
    ProviderBackup, ProviderExitService, RecoveryReceipt, RestoreFailpoint,
    StateRecord, TestProviderDouble,
)
from nks.application.sprint44_path_manifest import sprint44_provider_exit_path_manifest
from nks.governance.approvals import ExecutionContext

NOW=datetime(2026,7,17,9,0,tzinfo=timezone.utc)

def auth(tag: str="1") -> AuthoritySemantics:
    return AuthoritySemantics(
        authority_class="canonical-authority",
        authority_sha256=canonical_sha256(f"authority-{tag}"),
        policy_sha256=canonical_sha256(f"policy-{tag}"),
        consent_sha256=canonical_sha256(f"consent-{tag}"),
        temporal_sha256=canonical_sha256(f"temporal-{tag}"),
        lineage_sha256=canonical_sha256(f"lineage-{tag}"),
    )

def state(record_id: str, at: datetime=NOW, tag: str="1") -> StateRecord:
    return StateRecord(
        record_id=record_id,tenant_id="tenant-1",subject_id="subject-1",authority=auth(tag),
        payload_sha256=canonical_sha256(f"payload-{record_id}"),
        receipt_sha256=canonical_sha256(f"receipt-{record_id}"),recorded_at=at,authoritative=True,
    )

def obj(object_id: str, linked: tuple[str,...], at: datetime=NOW) -> ObjectRecord:
    return ObjectRecord(
        object_id=object_id,content_sha256=canonical_sha256(f"object-{object_id}"),
        linked_record_ids=linked,manifest_sha256=canonical_sha256({"object":object_id,"links":linked}),
        recorded_at=at,authoritative=False,
    )

def source_provider() -> TestProviderDouble:
    p=TestProviderDouble("provider-source")
    p.add_state(state("R1")); p.add_state(state("R2", tag="2"))
    p.add_object(obj("O1",("R1",))); p.add_object(obj("O2",("R2",)))
    for kind in ArtifactKind:
        p.add_noncanonical(NonCanonicalArtifact(
            artifact_id=f"A-{kind.value}",kind=kind,source_record_ids=("R1",),
            content_sha256=canonical_sha256(kind.value),authoritative=False,
        ))
    return p

def test_coordinated_backup_is_open_deterministic_and_independently_verifiable() -> None:
    source=source_provider()
    first=ProviderExitService.backup(source,backup_id="B1",snapshot_at=NOW)
    second=ProviderExitService.backup(source,backup_id="B1",snapshot_at=NOW)
    assert first==second
    assert first.state_fingerprint==canonical_sha256(first.state_records)
    assert first.object_fingerprint==canonical_sha256(first.object_records)
    assert len(first.noncanonical_hashes)==3
    assert json.loads(first.model_dump_json())["schema_version"]=="enki-provider-exit/v1"
    assert ProviderBackup.model_validate(first.model_dump(mode="python"))==first


def test_point_in_time_backup_excludes_later_state_and_orphaned_later_objects() -> None:
    source=source_provider(); later=NOW+timedelta(hours=1)
    source.add_state(state("R-LATE",later)); source.add_object(obj("O-LATE",("R-LATE",),later))
    backup=ProviderExitService.backup(source,backup_id="B-PIT",snapshot_at=NOW)
    assert {x.record_id for x in backup.state_records}=={"R1","R2"}
    assert {x.object_id for x in backup.object_records}=={"O1","O2"}


def test_clean_room_restore_preserves_authority_receipts_and_exact_fingerprints() -> None:
    source=source_provider(); backup=ProviderExitService.backup(source,backup_id="B-CLEAN",snapshot_at=NOW)
    destination=TestProviderDouble("provider-destination")
    receipt=ProviderExitService.restore(backup,destination)
    assert receipt.restored_exactly is True and receipt.rolled_back is False
    assert destination.state_fingerprint()==backup.state_fingerprint
    assert destination.object_fingerprint()==backup.object_fingerprint
    assert destination.state["R1"].authority==source.state["R1"].authority
    assert destination.state["R2"].receipt_sha256==source.state["R2"].receipt_sha256
    assert destination.noncanonical=={}
    assert receipt.ignored_noncanonical_count==3
    assert receipt.provider_certification is False and receipt.production_effect is False


def test_source_provider_can_be_unavailable_during_restore_and_provider_exit() -> None:
    source=source_provider(); backup=ProviderExitService.backup(source,backup_id="B-EXIT",snapshot_at=NOW)
    source.available=False
    destination=TestProviderDouble("independent-provider-double")
    receipt=ProviderExitService.restore(backup,destination)
    assert receipt.source_provider_id=="provider-source"
    assert receipt.destination_provider_id=="independent-provider-double"
    assert destination.state_fingerprint()==backup.state_fingerprint


@pytest.mark.parametrize("failpoint",[RestoreFailpoint.AFTER_STATE,RestoreFailpoint.AFTER_OBJECTS])
def test_interrupted_restore_rolls_back_exact_prior_destination(failpoint: RestoreFailpoint) -> None:
    source=source_provider(); backup=ProviderExitService.backup(source,backup_id=f"B-{failpoint.value}",snapshot_at=NOW)
    destination=TestProviderDouble("provider-existing")
    destination.add_state(state("PREEXISTING",tag="prior")); before=destination.fingerprint()
    receipt=ProviderExitService.restore_with_rollback(backup,destination,failpoint=failpoint)
    assert receipt.rolled_back is True and receipt.restored_exactly is False
    assert destination.fingerprint()==before==receipt.prior_destination_fingerprint
    assert set(destination.state)=={"PREEXISTING"}


def test_tampered_backup_fails_independent_verification() -> None:
    backup=ProviderExitService.backup(source_provider(),backup_id="B-TAMPER",snapshot_at=NOW)
    payload=backup.model_dump(mode="python"); payload["state_fingerprint"]="sha256:"+"0"*64
    with pytest.raises(ValidationError): ProviderBackup.model_validate(payload)


def test_noncanonical_projection_cache_and_replica_cannot_become_canonical() -> None:
    source=source_provider(); backup=ProviderExitService.backup(source,backup_id="B-NONCANON",snapshot_at=NOW)
    destination=TestProviderDouble("provider-clean")
    ProviderExitService.restore(backup,destination)
    assert destination.noncanonical=={}
    assert all(item.authoritative is True for item in destination.state.values())
    assert all(item.authoritative is False for item in destination.objects.values())
    assert len(backup.noncanonical_hashes)==3


def test_recovery_retry_converges_to_same_state_and_object_fingerprints() -> None:
    backup=ProviderExitService.backup(source_provider(),backup_id="B-RETRY",snapshot_at=NOW)
    destination=TestProviderDouble("provider-retry")
    first=ProviderExitService.restore(backup,destination); second=ProviderExitService.restore(backup,destination)
    assert first.state_fingerprint==second.state_fingerprint==backup.state_fingerprint
    assert first.object_fingerprint==second.object_fingerprint==backup.object_fingerprint


def test_test_receipt_cannot_claim_provider_validation_or_production_effect() -> None:
    backup=ProviderExitService.backup(source_provider(),backup_id="B-SAFETY",snapshot_at=NOW)
    receipt=ProviderExitService.restore(backup,TestProviderDouble("provider-safe"))
    payload=receipt.model_dump(mode="python"); payload["provider_certification"]=True
    with pytest.raises(ValidationError): RecoveryReceipt.model_validate(payload)
    payload=receipt.model_dump(mode="python"); payload["production_effect"]=True
    with pytest.raises(ValidationError): RecoveryReceipt.model_validate(payload)


SPRINT44_TESTED_PATHS={
"coordinated-state-object-backup","point-in-time-backup","open-deterministic-export","independent-manifest-verification",
"authority-semantics-preserved","policy-consent-temporal-lineage-preserved","receipts-preserved","noncanonical-artifacts-inventoried-not-restored",
"clean-room-exact-restore","source-provider-outage-restore","provider-exit-to-independent-destination","recovery-retry-deterministic",
"tampered-manifest-denied","interrupted-after-state-rolls-back","interrupted-after-objects-rolls-back","projection-cannot-become-canonical",
"cache-cannot-become-canonical","replica-cannot-become-canonical","test-proof-cannot-claim-real-provider-validation"}

def test_declared_sprint44_paths_have_coverage_and_test_boundary() -> None:
    manifest=sprint44_provider_exit_path_manifest(); manifest.assert_complete_coverage(SPRINT44_TESTED_PATHS)
    assert manifest.execution_context==ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "authority-widening" in path.prohibited_effects
        assert "noncanonical-promotion" in path.prohibited_effects
