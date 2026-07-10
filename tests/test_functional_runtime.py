from pathlib import Path

from nks.adapters.filesystem import JsonEventRepository, JsonRecordRepository
from nks.application.manufacture import ManufacturePublication, ManufacturingRepositories
from nks.domain.models import (
    ArtifactRecord,
    GateStatus,
    NarrativeRecord,
    ProofRecord,
    PublicationRecord,
    RecordStatus,
    SourceRecord,
    VisualPackageRecord,
)


def build_runtime(root: Path) -> ManufacturePublication:
    repositories = ManufacturingRepositories(
        sources=JsonRecordRepository(root, SourceRecord, "sources"),
        artifacts=JsonRecordRepository(root, ArtifactRecord, "artifacts"),
        proofs=JsonRecordRepository(root, ProofRecord, "proofs"),
        narratives=JsonRecordRepository(root, NarrativeRecord, "narratives"),
        visuals=JsonRecordRepository(root, VisualPackageRecord, "visuals"),
        publications=JsonRecordRepository(root, PublicationRecord, "publications"),
        events=JsonEventRepository(root),
    )
    return ManufacturePublication(repositories)


def fixture_records():
    source = SourceRecord(
        id="NKS-SRC-TEST-0001",
        title="Functional Test Source",
        status=RecordStatus.APPROVED,
        source_type="test-fixture",
        source_location="fixtures/source.md",
    )
    artifact = ArtifactRecord(
        id="NKS-ART-TEST-0001",
        title="The Corpus Is Manufactured, Not Found",
        status=RecordStatus.REVIEW,
        source_ids=[source.id],
        proof_status=GateStatus.READY,
        narrative_status=GateStatus.READY,
        visual_status=GateStatus.READY,
    )
    proof = ProofRecord(
        id="NKS-PRF-TEST-0001",
        title="Functional Test Proof",
        status=RecordStatus.REVIEW,
        artifact_id=artifact.id,
        category="repository-derived",
        supported_claims=["The runtime persists platform-neutral canonical records."],
        unsupported_claims=["The runtime has already produced public engagement outcomes."],
        gate_status=GateStatus.READY,
    )
    narrative = NarrativeRecord(
        id="NKS-NAR-TEST-0001",
        title="Functional Test Narrative",
        status=RecordStatus.REVIEW,
        artifact_id=artifact.id,
        recognition="Knowledge exists in fragmented sources.",
        reframe="A corpus is manufactured rather than discovered intact.",
        framework="Source, proof, artifact, arc, visual, and publication records form the system.",
        proof="The test verifies deterministic persistence and policy evaluation.",
        application="Run the same workflow through any conforming adapter.",
        consequence="The runtime can move away from GitHub without rewriting domain logic.",
        invitation="Evaluate the system by its contracts rather than its current host.",
        gate_status=GateStatus.READY,
    )
    visual = VisualPackageRecord(
        id="NKS-VIS-TEST-0001",
        title="Functional Test Visual Package",
        status=RecordStatus.REVIEW,
        artifact_id=artifact.id,
        publication_id="NKS-PUB-TEST-0001",
        signature_diagram_id="NKS-DGM-TEST-0001",
        hero_image_id="NKS-HRO-TEST-0001",
        asset_ids=["NKS-DGM-TEST-0001", "NKS-HRO-TEST-0001"],
        gate_status=GateStatus.READY,
    )
    publication = PublicationRecord(
        id="NKS-PUB-TEST-0001",
        title="Functional Runtime Test Publication",
        status=RecordStatus.REVIEW,
        artifact_id=artifact.id,
        proof_id=proof.id,
        narrative_id=narrative.id,
        visual_package_id=visual.id,
        draft_path="publishing/drafts/NKS-PUB-TEST-0001.md",
        editorial_status=GateStatus.READY,
        user_approval=GateStatus.APPROVED,
    )
    return source, artifact, proof, narrative, visual, publication


def test_end_to_end_workflow_is_idempotent(tmp_path: Path):
    runtime = build_runtime(tmp_path)
    records = fixture_records()

    first = runtime.execute(
        source=records[0], artifact=records[1], proof=records[2],
        narrative=records[3], visual=records[4], publication=records[5],
    )
    second = runtime.execute(
        source=records[0], artifact=records[1], proof=records[2],
        narrative=records[3], visual=records[4], publication=records[5],
    )

    assert first.passed, first.failures
    assert second.passed, second.failures
    assert len(list((tmp_path / "sources").glob("*.json"))) == 1
    assert len(list((tmp_path / "publications").glob("*.json"))) == 1
    assert len((tmp_path / "events" / "events.jsonl").read_text().splitlines()) == 1
