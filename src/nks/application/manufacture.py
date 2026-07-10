"""Application service for manufacturing and validating one publication package."""

from __future__ import annotations

from dataclasses import dataclass

from nks.domain.models import (
    ArtifactRecord,
    NarrativeRecord,
    ProofRecord,
    PublicationRecord,
    SourceRecord,
    VisualPackageRecord,
    WorkflowEvent,
)
from nks.policies.readiness import ValidationResult, validate_publication_readiness
from nks.ports.repositories import EventRepository, RecordRepository


@dataclass
class ManufacturingRepositories:
    sources: RecordRepository[SourceRecord]
    artifacts: RecordRepository[ArtifactRecord]
    proofs: RecordRepository[ProofRecord]
    narratives: RecordRepository[NarrativeRecord]
    visuals: RecordRepository[VisualPackageRecord]
    publications: RecordRepository[PublicationRecord]
    events: EventRepository


class ManufacturePublication:
    def __init__(self, repositories: ManufacturingRepositories) -> None:
        self._repos = repositories

    def execute(
        self,
        *,
        source: SourceRecord,
        artifact: ArtifactRecord,
        proof: ProofRecord,
        narrative: NarrativeRecord,
        visual: VisualPackageRecord,
        publication: PublicationRecord,
    ) -> ValidationResult:
        self._repos.sources.save(source)
        self._repos.artifacts.save(artifact)
        self._repos.proofs.save(proof)
        self._repos.narratives.save(narrative)
        self._repos.visuals.save(visual)
        self._repos.publications.save(publication)

        event = WorkflowEvent(
            event_id=f"manufactured:{publication.id}",
            event_type="publication.manufactured",
            subject_id=publication.id,
            payload={"artifact_id": artifact.id, "source_id": source.id},
        )
        self._repos.events.append(event)

        return validate_publication_readiness(
            publication=publication,
            source=self._repos.sources.get(source.id),
            proof=self._repos.proofs.get(proof.id),
            narrative=self._repos.narratives.get(narrative.id),
            visual=self._repos.visuals.get(visual.id),
        )
