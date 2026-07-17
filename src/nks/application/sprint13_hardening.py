"""Sprint 13 chaos, recovery, and release-artifact hardening.

This module builds on the Sprint 12 recoverable portability boundary and the Sprint 13
TEST-only release-candidate contracts. It deliberately contains no production transport,
credentials, endpoints, callbacks, or production mutation capability.
"""

from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.sprint12_recovery import (
    InterruptedOperationError,
    export_portable_state_recoverable,
    import_portable_state_recoverable,
    restore_and_reconstruct_recoverable,
    validate_portable_package,
)
from nks.application.sprint13_release_candidate import (
    ReleaseCandidate,
    ReleaseDecisionRequest,
    ReleaseEvidenceManifest,
    canonical_sha256,
)


class ChaosDrillName(StrEnum):
    EXPORT_INTERRUPTION = "EXPORT_INTERRUPTION"
    IMPORT_INTERRUPTION = "IMPORT_INTERRUPTION"
    ROLLBACK_AFTER_BACKUP = "ROLLBACK_AFTER_BACKUP"
    RECONSTRUCTION_INTERRUPTION = "RECONSTRUCTION_INTERRUPTION"
    TAMPER_REJECTION = "TAMPER_REJECTION"


class ChaosDrillResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    drill: ChaosDrillName
    passed: bool
    recovered: bool
    external_effect: bool = False
    authority_escalated: bool = False
    duplicate_effect: bool = False
    detail: str = Field(min_length=1)
    evidence_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @classmethod
    def create(
        cls,
        drill: ChaosDrillName,
        *,
        passed: bool,
        recovered: bool,
        detail: str,
        external_effect: bool = False,
        authority_escalated: bool = False,
        duplicate_effect: bool = False,
    ) -> "ChaosDrillResult":
        body = {
            "drill": drill.value,
            "passed": passed,
            "recovered": recovered,
            "external_effect": external_effect,
            "authority_escalated": authority_escalated,
            "duplicate_effect": duplicate_effect,
            "detail": detail,
        }
        return cls(**body, evidence_sha256=canonical_sha256(body))


class HardeningReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    drills: list[ChaosDrillResult] = Field(min_length=5)
    all_passed: bool
    report_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_report(self) -> "HardeningReport":
        names = [item.drill for item in self.drills]
        if len(set(names)) != len(names):
            raise ValueError("hardening report contains duplicate chaos drills")
        if not set(ChaosDrillName).issubset(set(names)):
            raise ValueError("hardening report is missing required chaos drills")
        safe = all(
            item.passed
            and item.recovered
            and not item.external_effect
            and not item.authority_escalated
            and not item.duplicate_effect
            for item in self.drills
        )
        if self.all_passed != safe:
            raise ValueError("hardening report all_passed does not match drill evidence")
        body = {
            "candidate_sha256": self.candidate_sha256,
            "drills": [item.model_dump(mode="json") for item in self.drills],
            "all_passed": self.all_passed,
        }
        if self.report_sha256 != canonical_sha256(body):
            raise ValueError("hardening report hash does not match report contents")
        return self

    @classmethod
    def create(
        cls,
        *,
        candidate_sha256: str,
        drills: list[ChaosDrillResult],
    ) -> "HardeningReport":
        all_passed = all(
            item.passed
            and item.recovered
            and not item.external_effect
            and not item.authority_escalated
            and not item.duplicate_effect
            for item in drills
        )
        body = {
            "candidate_sha256": candidate_sha256,
            "drills": [item.model_dump(mode="json") for item in drills],
            "all_passed": all_passed,
        }
        return cls(**body, report_sha256=canonical_sha256(body))


def _tamper_archive(source_archive: Path, tampered_archive: Path) -> str:
    shutil.copy2(source_archive, tampered_archive)
    with zipfile.ZipFile(tampered_archive, "r") as bundle:
        manifest_bytes = bundle.read("manifest.json")
        entries = {
            name: bundle.read(name)
            for name in bundle.namelist()
            if name != "manifest.json"
        }
    if not entries:
        raise ValueError("portable package contains no payload files to tamper")
    target = sorted(entries)[0]
    entries[target] = entries[target] + b"\nTAMPER"
    with zipfile.ZipFile(tampered_archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("manifest.json", manifest_bytes)
        for name in sorted(entries):
            bundle.writestr(name, entries[name])
    return target


def execute_recovery_chaos_drills(
    *,
    source_root: Path,
    work_root: Path,
    candidate_sha256: str,
) -> HardeningReport:
    """Execute deterministic TEST-only recovery drills using the Sprint 12 boundary."""

    work_root.mkdir(parents=True, exist_ok=True)
    archive = work_root / "portable.zip"
    journal = work_root / "recovery.jsonl"
    drills: list[ChaosDrillResult] = []

    try:
        export_portable_state_recoverable(
            source_root,
            archive,
            journal_path=journal,
            operation_id="s13-export-interruption",
            failpoint="after_export_stage",
        )
        export_interrupted = False
    except InterruptedOperationError:
        export_interrupted = True
    partial = archive.with_name(f"{archive.name}.partial")
    export_result = export_portable_state_recoverable(
        source_root,
        archive,
        journal_path=journal,
        operation_id="s13-export-interruption",
    )
    validate_portable_package(archive)
    export_recovered = (
        export_interrupted
        and archive.exists()
        and not partial.exists()
        and len(export_result.manifest_sha256) == 64
    )
    drills.append(
        ChaosDrillResult.create(
            ChaosDrillName.EXPORT_INTERRUPTION,
            passed=export_recovered,
            recovered=export_recovered,
            detail="validated export interruption retried to one complete portable package",
        )
    )

    import_destination = work_root / "import-destination"
    import_destination.mkdir(exist_ok=True)
    sentinel = import_destination / "sentinel.txt"
    sentinel.write_text("original", encoding="utf-8")
    try:
        import_portable_state_recoverable(
            archive,
            import_destination,
            replace=True,
            journal_path=journal,
            operation_id="s13-import-interruption",
            failpoint="after_import_stage",
        )
        import_interrupted = False
    except InterruptedOperationError:
        import_interrupted = True
    destination_untouched = sentinel.exists() and sentinel.read_text(encoding="utf-8") == "original"
    import_portable_state_recoverable(
        archive,
        import_destination,
        replace=True,
        journal_path=journal,
        operation_id="s13-import-interruption",
    )
    import_recovered = (
        import_interrupted
        and destination_untouched
        and (import_destination / "records").exists()
        and not sentinel.exists()
    )
    drills.append(
        ChaosDrillResult.create(
            ChaosDrillName.IMPORT_INTERRUPTION,
            passed=import_recovered,
            recovered=import_recovered,
            detail="staged import interruption preserved prior state and retry committed once",
        )
    )

    rollback_destination = work_root / "rollback-destination"
    rollback_destination.mkdir(exist_ok=True)
    rollback_sentinel = rollback_destination / "sentinel.txt"
    rollback_sentinel.write_text("prior-state", encoding="utf-8")
    try:
        import_portable_state_recoverable(
            archive,
            rollback_destination,
            replace=True,
            journal_path=journal,
            operation_id="s13-rollback",
            failpoint="after_destination_backup",
        )
        rollback_interrupted = False
    except InterruptedOperationError:
        rollback_interrupted = True
    rollback_recovered = (
        rollback_interrupted
        and rollback_sentinel.exists()
        and rollback_sentinel.read_text(encoding="utf-8") == "prior-state"
        and not (rollback_destination / "records").exists()
    )
    drills.append(
        ChaosDrillResult.create(
            ChaosDrillName.ROLLBACK_AFTER_BACKUP,
            passed=rollback_recovered,
            recovered=rollback_recovered,
            detail="destination-backup interruption restored the exact prior destination",
        )
    )

    reconstruction_destination = work_root / "reconstruction-destination"
    try:
        restore_and_reconstruct_recoverable(
            archive,
            reconstruction_destination,
            replace=True,
            journal_path=journal,
            operation_id="s13-reconstruction",
            failpoint="before_reconstruction",
        )
        reconstruction_interrupted = False
    except InterruptedOperationError:
        reconstruction_interrupted = True
    reconstructed = restore_and_reconstruct_recoverable(
        archive,
        reconstruction_destination,
        replace=True,
        journal_path=journal,
        operation_id="s13-reconstruction",
    )
    reconstruction_recovered = reconstruction_interrupted and bool(
        reconstructed.canonical_fingerprint()
    )
    drills.append(
        ChaosDrillResult.create(
            ChaosDrillName.RECONSTRUCTION_INTERRUPTION,
            passed=reconstruction_recovered,
            recovered=reconstruction_recovered,
            detail="pre-reconstruction interruption retried to deterministic governed state",
        )
    )

    tampered = work_root / "tampered.zip"
    target = _tamper_archive(archive, tampered)
    try:
        validate_portable_package(tampered)
        tamper_rejected = False
    except ValueError:
        tamper_rejected = True
    drills.append(
        ChaosDrillResult.create(
            ChaosDrillName.TAMPER_REJECTION,
            passed=tamper_rejected,
            recovered=tamper_rejected,
            detail=f"tampered portable entry rejected before import: {target}",
        )
    )

    return HardeningReport.create(candidate_sha256=candidate_sha256, drills=drills)


class ReleaseArtifactBundle(BaseModel):
    """Hashable RC evidence package that preserves the unresolved human release gate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate: ReleaseCandidate
    hardening_report: HardeningReport
    threat_model: dict[str, Any]
    runbook: dict[str, Any]
    limitations: dict[str, Any]
    rollback_package: dict[str, Any]
    release_notes: dict[str, Any]
    production_readiness: dict[str, Any]
    decision_request: ReleaseDecisionRequest

    @model_validator(mode="after")
    def validate_bundle(self) -> "ReleaseArtifactBundle":
        candidate_hash = canonical_sha256(self.candidate)
        if self.hardening_report.candidate_sha256 != candidate_hash:
            raise ValueError("hardening report is not bound to the release candidate")
        if self.decision_request.candidate_sha256 != candidate_hash:
            raise ValueError("decision request is not bound to the release candidate")
        if not self.hardening_report.all_passed:
            raise ValueError("release artifact bundle requires a passing hardening report")
        if self.candidate.production_authorized:
            raise ValueError("Sprint 13 release artifacts cannot authorize production")
        if self.production_readiness.get("production_approval_status") != "PENDING_HUMAN_DECISION":
            raise ValueError("production readiness must remain pending human decision")
        return self

    def artifact_payloads(self) -> dict[str, Any]:
        return {
            "release-candidate.json": self.candidate.model_dump(mode="json"),
            "hardening-report.json": self.hardening_report.model_dump(mode="json"),
            "threat-model.json": self.threat_model,
            "runbook.json": self.runbook,
            "limitations.json": self.limitations,
            "rollback-package.json": self.rollback_package,
            "release-notes.json": self.release_notes,
            "production-readiness.json": self.production_readiness,
            "release-decision-request.json": self.decision_request.model_dump(mode="json"),
        }


def build_release_artifact_bundle(
    *,
    candidate: ReleaseCandidate,
    hardening_report: HardeningReport,
    generated_at: datetime,
    requested_from: str,
) -> ReleaseArtifactBundle:
    """Build deterministic RC artifacts without crossing the production authority boundary."""

    candidate_hash = canonical_sha256(candidate)
    threat_model = {
        "version": candidate.version,
        "generated_at": generated_at.isoformat(),
        "execution_context": "TEST",
        "threats": [
            "TEST-to-PRODUCTION authority escalation",
            "portable package tampering",
            "replay presented as new REAL feedback",
            "duplicate effects after retry",
            "partial destination replacement",
            "silent historical-authority promotion",
        ],
        "controls": [
            "TEST-only proof lanes",
            "no-effect receipts",
            "hash-bound portable packages",
            "explicit feedback provenance",
            "transactional staging and rollback",
            "deterministic reconstruction",
            "human-only release decision",
        ],
    }
    runbook = {
        "version": candidate.version,
        "generated_at": generated_at.isoformat(),
        "preflight": [
            "validate Sprint 12 portable package",
            "verify release evidence hashes",
            "run Sprint 12 and Sprint 13 regression suites",
            "run chaos and recovery drills",
            "verify zero external effects and zero authority escalation",
        ],
        "release_gate": [
            "present hash-bound candidate to human authority",
            "record APPROVE, APPROVE_WITH_CONDITIONS, DEFER, or REJECT",
            "do not infer production approval from Sprint completion",
        ],
        "recovery": [
            "stop before external effect on invariant failure",
            "restore prior destination from rollback boundary",
            "retry exact operation only",
            "reconstruct governed state from persisted history",
        ],
    }
    limitations = {
        "version": candidate.version,
        "generated_at": generated_at.isoformat(),
        "limitations": [
            "no live external publication has been performed by Sprint 13",
            "no production audience response is claimed",
            "no production validation is claimed",
            "no external model transport is authorized",
            "no production canonical mutation is authorized",
            "REAL/TEST feedback cannot satisfy a REAL/PRODUCTION evidence gate",
        ],
    }
    rollback_package = {
        "version": candidate.version,
        "generated_at": generated_at.isoformat(),
        "procedure": [
            "halt before any production effect",
            "preserve append-only recovery journal",
            "restore last valid destination snapshot",
            "validate portable package and history checksums",
            "reconstruct governed state",
            "compare canonical fingerprint to last accepted authority state",
        ],
    }
    release_notes = {
        "version": candidate.version,
        "generated_at": generated_at.isoformat(),
        "status": "READY_FOR_HUMAN_DECISION",
        "scope": [
            "Sprint 12 reconstructable portability and recovery",
            "Sprint 13 two-lane TEST proof",
            "TEST feedback provenance and calibration",
            "chaos, rollback, tamper, and deterministic reconstruction hardening",
        ],
        "production_effects": False,
    }
    production_readiness = {
        "version": candidate.version,
        "generated_at": generated_at.isoformat(),
        "production_approval_status": "PENDING_HUMAN_DECISION",
        "remaining_sprint3_ownership": [
            "exact production content approval",
            "exact visual approval",
            "production channel and account configuration",
            "production transport authorization",
            "external publication receipts",
            "observation window",
            "REAL/PRODUCTION feedback or zero-feedback receipt",
            "post-release calibration",
        ],
    }
    decision_request = ReleaseDecisionRequest(
        candidate_sha256=candidate_hash,
        requested_at=generated_at,
        requested_from=requested_from,
    )
    return ReleaseArtifactBundle(
        candidate=candidate,
        hardening_report=hardening_report,
        threat_model=threat_model,
        runbook=runbook,
        limitations=limitations,
        rollback_package=rollback_package,
        release_notes=release_notes,
        production_readiness=production_readiness,
        decision_request=decision_request,
    )


def write_release_artifact_bundle(
    bundle: ReleaseArtifactBundle,
    output_root: Path,
) -> ReleaseEvidenceManifest:
    """Write deterministic JSON release artifacts and return their exact hash manifest."""

    output_root.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for filename, payload in sorted(bundle.artifact_payloads().items()):
        path = output_root / filename
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        paths.append(path)
    manifest = ReleaseEvidenceManifest.from_paths(paths, root=output_root)
    (output_root / "evidence-manifest.json").write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest
