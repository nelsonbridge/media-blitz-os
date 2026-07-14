"""Reproducible release, SBOM, and supply-chain integrity controls.

The verifier operates entirely from repository content.  It does not read
production credentials, contact external services, or issue release authority.
All attestations are TEST-scoped evidence prepared for later human review.
"""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from enum import StrEnum
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.application.integrated_test_proof import (
    EnkiReleaseCandidate,
    ReleaseCandidateStatus,
)
from nks.governance.approvals import ExecutionContext


VERIFIER_VERSION = "enki-release-integrity/v1"

RELEASE_ARTIFACT_FILES: dict[str, str] = {
    "calibration-report": "calibration-report.md",
    "evidence-manifest": "evidence-manifest.md",
    "human-release-decision": "human-release-decision.md",
    "known-limitations": "known-limitations.md",
    "nonpublication-loop-receipt-file": "nonpublication-loop-receipt.json",
    "publication-loop-receipt-file": "publication-loop-receipt.json",
    "release-notes": "release-notes.md",
    "rollback-package": "rollback-package.md",
    "runbook": "runbook.md",
    "threat-model": "threat-model.md",
}

_SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_USES_PATTERN = re.compile(r"^\s*(?:-\s*)?uses:\s*[\"']?([^\"'#\s]+)")

_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\bghp_[A-Za-z0-9]{36}\b")),
    ("github-fine-grained-token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("openai-key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    (
        "private-key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
)


class DependencyScope(StrEnum):
    BUILD = "BUILD"
    RUNTIME = "RUNTIME"
    TEST = "TEST"


class FindingSeverity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"


class DependencyComponent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    requirement: str = Field(min_length=1)
    scope: DependencyScope
    source_file: str = Field(min_length=1)


class WorkflowAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow_path: str = Field(min_length=1)
    reference: str = Field(min_length=1)
    action: str = Field(min_length=1)
    revision: str | None = None
    local: bool = False


class ReleaseInventory(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    project_name: str = Field(min_length=1)
    project_version: str = Field(min_length=1)
    python_requirement: str = Field(min_length=1)
    dependencies: list[DependencyComponent]
    workflow_actions: list[WorkflowAction]
    dependency_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    workflow_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    inventory_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_inventory_hashes(self) -> "ReleaseInventory":
        dependency_hash = canonical_sha256(self.dependencies)
        workflow_hash = canonical_sha256(self.workflow_actions)
        payload = {
            "project_name": self.project_name,
            "project_version": self.project_version,
            "python_requirement": self.python_requirement,
            "dependencies": self.dependencies,
            "workflow_actions": self.workflow_actions,
            "dependency_sha256": dependency_hash,
            "workflow_sha256": workflow_hash,
        }
        if self.dependency_sha256 != dependency_hash:
            raise ValueError("dependency inventory hash is invalid")
        if self.workflow_sha256 != workflow_hash:
            raise ValueError("workflow inventory hash is invalid")
        if self.inventory_sha256 != canonical_sha256(payload):
            raise ValueError("release inventory hash is invalid")
        return self


class ReleaseVerificationFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(min_length=1)
    severity: FindingSeverity
    message: str = Field(min_length=1)
    path: str | None = None


class SupplyChainAttestation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    attestation_id: str = Field(min_length=1)
    verifier_version: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    candidate_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    source_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    inventory_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    dependency_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    workflow_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    sbom_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    artifact_hashes: dict[str, str]
    execution_context: ExecutionContext = ExecutionContext.TEST
    production_credentials_used: bool = False
    human_release_decision_issued: bool = False
    attestation_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_attestation(self) -> "SupplyChainAttestation":
        if self.execution_context != ExecutionContext.TEST:
            raise ValueError("release integrity attestations are TEST-only")
        if self.production_credentials_used:
            raise ValueError("release verification cannot use production credentials")
        if self.human_release_decision_issued:
            raise ValueError("release verification cannot issue a human decision")
        if any(not _SHA256_PATTERN.fullmatch(value) for value in self.artifact_hashes.values()):
            raise ValueError("attestation artifact hashes must be sha256 values")
        payload = self.model_dump(mode="python", exclude={"attestation_sha256"})
        if self.attestation_sha256 != canonical_sha256(payload):
            raise ValueError("supply-chain attestation hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "SupplyChainAttestation":
        payload = dict(values)
        payload["attestation_sha256"] = canonical_sha256(payload)
        return cls(**payload)


class ReleaseIntegrityResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    valid: bool
    candidate: EnkiReleaseCandidate | None = None
    inventory: ReleaseInventory | None = None
    sbom: dict[str, object] | None = None
    attestation: SupplyChainAttestation | None = None
    findings: list[ReleaseVerificationFinding] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_result(self) -> "ReleaseIntegrityResult":
        has_errors = any(item.severity == FindingSeverity.ERROR for item in self.findings)
        if self.valid == has_errors:
            raise ValueError("release integrity validity does not match findings")
        if self.valid and (
            self.candidate is None
            or self.inventory is None
            or self.sbom is None
            or self.attestation is None
        ):
            raise ValueError("valid release integrity results require complete evidence")
        if not self.valid and self.attestation is not None:
            raise ValueError("invalid release packages cannot receive an attestation")
        return self


def raw_file_sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _dependency_name(requirement: str) -> str:
    name = re.split(r"[<>=!~;\s\[]", requirement.strip(), maxsplit=1)[0]
    if not name:
        raise ValueError(f"cannot determine dependency name from {requirement!r}")
    return name.lower().replace("_", "-")


def _workflow_action(reference: str, workflow_path: str) -> WorkflowAction:
    local = reference.startswith("./")
    if "@" in reference and not local:
        action, revision = reference.rsplit("@", 1)
    else:
        action, revision = reference, None
    return WorkflowAction(
        workflow_path=workflow_path,
        reference=reference,
        action=action,
        revision=revision,
        local=local,
    )


def build_release_inventory(repository_root: Path) -> ReleaseInventory:
    """Build deterministic dependency and workflow-action inventories."""

    root = repository_root.resolve()
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.is_file():
        raise FileNotFoundError("pyproject.toml is required for release inventory")
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = pyproject.get("project")
    if not isinstance(project, dict):
        raise ValueError("pyproject.toml has no [project] table")

    components: list[DependencyComponent] = []

    def add_requirements(requirements: object, scope: DependencyScope) -> None:
        if requirements is None:
            return
        if not isinstance(requirements, list) or not all(
            isinstance(item, str) for item in requirements
        ):
            raise ValueError(f"{scope.value} dependencies must be a list of strings")
        for requirement in requirements:
            components.append(
                DependencyComponent(
                    name=_dependency_name(requirement),
                    requirement=requirement,
                    scope=scope,
                    source_file="pyproject.toml",
                )
            )

    add_requirements(pyproject.get("build-system", {}).get("requires"), DependencyScope.BUILD)
    add_requirements(project.get("dependencies"), DependencyScope.RUNTIME)
    optional = project.get("optional-dependencies", {})
    if not isinstance(optional, dict):
        raise ValueError("[project.optional-dependencies] must be a table")
    add_requirements(optional.get("test"), DependencyScope.TEST)
    components.sort(key=lambda item: (item.scope.value, item.name, item.requirement))

    workflow_actions: list[WorkflowAction] = []
    workflow_root = root / ".github" / "workflows"
    if workflow_root.is_dir():
        workflow_paths = sorted(
            [*workflow_root.glob("*.yml"), *workflow_root.glob("*.yaml")],
            key=lambda path: path.as_posix(),
        )
        for workflow_path in workflow_paths:
            relative = workflow_path.relative_to(root).as_posix()
            for line in workflow_path.read_text(encoding="utf-8").splitlines():
                match = _USES_PATTERN.match(line)
                if match:
                    workflow_actions.append(_workflow_action(match.group(1), relative))
    workflow_actions.sort(
        key=lambda item: (item.workflow_path, item.action, item.revision or "", item.reference)
    )

    dependency_hash = canonical_sha256(components)
    workflow_hash = canonical_sha256(workflow_actions)
    payload = {
        "project_name": str(project.get("name", "")),
        "project_version": str(project.get("version", "")),
        "python_requirement": str(project.get("requires-python", "")),
        "dependencies": components,
        "workflow_actions": workflow_actions,
        "dependency_sha256": dependency_hash,
        "workflow_sha256": workflow_hash,
    }
    return ReleaseInventory(
        **payload,
        inventory_sha256=canonical_sha256(payload),
    )


def build_cyclonedx_sbom(inventory: ReleaseInventory) -> dict[str, object]:
    """Create a deterministic CycloneDX-shaped SBOM without network lookups."""

    components: list[dict[str, object]] = []
    for dependency in inventory.dependencies:
        components.append(
            {
                "type": "library",
                "name": dependency.name,
                "version": dependency.requirement,
                "scope": dependency.scope.value.lower(),
                "properties": [
                    {"name": "enki:requirement", "value": dependency.requirement},
                    {"name": "enki:source", "value": dependency.source_file},
                ],
            }
        )
    for action in inventory.workflow_actions:
        components.append(
            {
                "type": "application",
                "name": action.action,
                "version": action.revision or "local",
                "scope": "required",
                "properties": [
                    {"name": "enki:workflow", "value": action.workflow_path},
                    {"name": "enki:reference", "value": action.reference},
                ],
            }
        )
    components.sort(
        key=lambda item: (
            str(item["type"]),
            str(item["name"]),
            str(item["version"]),
            canonical_sha256(item),
        )
    )
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:sha256:{inventory.inventory_sha256.removeprefix('sha256:')}",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": inventory.project_name,
                "version": inventory.project_version,
            },
            "properties": [
                {"name": "enki:python-requirement", "value": inventory.python_requirement},
                {"name": "enki:inventory-sha256", "value": inventory.inventory_sha256},
            ],
        },
        "components": components,
    }


def scan_for_secrets(paths: Iterable[Path], repository_root: Path) -> list[ReleaseVerificationFinding]:
    findings: list[ReleaseVerificationFinding] = []
    root = repository_root.resolve()
    files: list[Path] = []
    for candidate in paths:
        path = candidate.resolve()
        if path.is_dir():
            files.extend(item for item in path.rglob("*") if item.is_file())
        elif path.is_file():
            files.append(path)
    for path in sorted(set(files), key=lambda item: item.as_posix()):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            relative = path.as_posix()
        for secret_type, pattern in _SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(
                    ReleaseVerificationFinding(
                        code="secret-leak",
                        severity=FindingSeverity.ERROR,
                        message=f"potential {secret_type} detected",
                        path=relative,
                    )
                )
    return findings


def _finding(code: str, message: str, path: Path | str | None = None) -> ReleaseVerificationFinding:
    return ReleaseVerificationFinding(
        code=code,
        severity=FindingSeverity.ERROR,
        message=message,
        path=str(path) if path is not None else None,
    )


def _load_candidate(candidate_path: Path) -> tuple[EnkiReleaseCandidate | None, list[ReleaseVerificationFinding]]:
    if not candidate_path.is_file():
        return None, [_finding("missing-candidate", "release-candidate.json is missing", candidate_path)]
    try:
        return (
            EnkiReleaseCandidate.model_validate_json(candidate_path.read_text(encoding="utf-8")),
            [],
        )
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        return None, [_finding("invalid-candidate", f"release candidate is invalid: {exc}", candidate_path)]


def verify_release_integrity(
    repository_root: Path,
    release_directory: Path,
    *,
    expected_source_commit: str | None = None,
    expected_dependency_sha256: str | None = None,
    expected_workflow_sha256: str | None = None,
) -> ReleaseIntegrityResult:
    """Verify a release package and construct a deterministic TEST attestation."""

    root = repository_root.resolve()
    release = release_directory.resolve()
    findings: list[ReleaseVerificationFinding] = []
    candidate, candidate_findings = _load_candidate(release / "release-candidate.json")
    findings.extend(candidate_findings)

    try:
        inventory = build_release_inventory(root)
    except (FileNotFoundError, ValueError, tomllib.TOMLDecodeError) as exc:
        findings.append(_finding("invalid-inventory", str(exc), root / "pyproject.toml"))
        inventory = None

    sbom: dict[str, object] | None = (
        build_cyclonedx_sbom(inventory) if inventory is not None else None
    )

    if inventory is not None:
        if (
            expected_dependency_sha256 is not None
            and inventory.dependency_sha256 != expected_dependency_sha256
        ):
            findings.append(
                _finding(
                    "dependency-drift",
                    "dependency inventory differs from the declared release baseline",
                    root / "pyproject.toml",
                )
            )
        if (
            expected_workflow_sha256 is not None
            and inventory.workflow_sha256 != expected_workflow_sha256
        ):
            findings.append(
                _finding(
                    "workflow-drift",
                    "workflow action inventory differs from the declared release baseline",
                    root / ".github" / "workflows",
                )
            )

    if candidate is not None:
        manifest = candidate.manifest
        if manifest.execution_context != ExecutionContext.TEST:
            findings.append(_finding("context-escalation", "release candidate is not TEST-scoped"))
        if candidate.status != ReleaseCandidateStatus.READY_FOR_HUMAN_DECISION:
            findings.append(
                _finding("invalid-candidate-state", "candidate is not ready for human decision")
            )
        if candidate.external_effect:
            findings.append(_finding("external-effect", "TEST candidate claims an external effect"))
        if expected_source_commit is not None and manifest.source_commit_sha != expected_source_commit:
            findings.append(
                _finding(
                    "source-provenance-mismatch",
                    "candidate source commit does not match the declared clean-room source",
                )
            )
        if not _COMMIT_PATTERN.fullmatch(manifest.source_commit_sha):
            findings.append(_finding("missing-source-provenance", "source commit is not exact"))

        declared_artifacts = set(manifest.artifact_hashes)
        expected_artifacts = set(RELEASE_ARTIFACT_FILES)
        if declared_artifacts != expected_artifacts:
            missing = sorted(expected_artifacts - declared_artifacts)
            unexpected = sorted(declared_artifacts - expected_artifacts)
            findings.append(
                _finding(
                    "artifact-manifest-mismatch",
                    f"artifact manifest mismatch; missing={missing}, unexpected={unexpected}",
                    release / "release-candidate.json",
                )
            )

        for artifact_id, filename in RELEASE_ARTIFACT_FILES.items():
            artifact_path = release / filename
            if not artifact_path.is_file():
                findings.append(
                    _finding("missing-artifact", f"release artifact {artifact_id} is missing", artifact_path)
                )
                continue
            declared_hash = manifest.artifact_hashes.get(artifact_id)
            actual_hash = raw_file_sha256(artifact_path)
            if declared_hash != actual_hash:
                findings.append(
                    _finding(
                        "artifact-substitution",
                        f"release artifact {artifact_id} does not match its declared hash",
                        artifact_path,
                    )
                )

        receipt_hashes: set[str] = set()
        for filename in ("publication-loop-receipt.json", "nonpublication-loop-receipt.json"):
            receipt_path = release / filename
            if not receipt_path.is_file():
                continue
            try:
                payload = json.loads(receipt_path.read_text(encoding="utf-8"))
                claimed = payload.pop("receipt_sha256")
                actual = canonical_sha256(payload)
                if claimed != actual:
                    findings.append(
                        _finding(
                            "loop-receipt-tamper",
                            f"{filename} does not match its self-hash",
                            receipt_path,
                        )
                    )
                else:
                    receipt_hashes.add(claimed)
                if payload.get("execution_context") != ExecutionContext.TEST.value:
                    findings.append(
                        _finding("receipt-context-escalation", f"{filename} is not TEST-scoped", receipt_path)
                    )
                if payload.get("external_effect") is not False:
                    findings.append(
                        _finding("receipt-external-effect", f"{filename} claims an external effect", receipt_path)
                    )
            except (KeyError, ValueError, json.JSONDecodeError) as exc:
                findings.append(
                    _finding("invalid-loop-receipt", f"{filename} is invalid: {exc}", receipt_path)
                )
        if receipt_hashes != set(manifest.loop_receipt_hashes):
            findings.append(
                _finding(
                    "loop-receipt-manifest-mismatch",
                    "adaptive-loop receipt hashes do not match the candidate manifest",
                )
            )

        decision_path = release / "human-release-decision.md"
        if decision_path.is_file():
            decision_text = decision_path.read_text(encoding="utf-8")
            if "Decision: **Not recorded**" not in decision_text or (
                "Decided by: **Not recorded**" not in decision_text
            ):
                findings.append(
                    _finding(
                        "self-issued-release-decision",
                        "release package contains a populated human decision",
                        decision_path,
                    )
                )

    scan_paths: list[Path] = [release, root / "pyproject.toml", root / ".github" / "workflows"]
    findings.extend(scan_for_secrets(scan_paths, root))

    has_errors = any(item.severity == FindingSeverity.ERROR for item in findings)
    attestation: SupplyChainAttestation | None = None
    if not has_errors and candidate is not None and inventory is not None and sbom is not None:
        attestation = SupplyChainAttestation.create(
            attestation_id=f"ATTEST-{candidate.manifest.candidate_id}",
            verifier_version=VERIFIER_VERSION,
            candidate_id=candidate.manifest.candidate_id,
            candidate_sha256=candidate.candidate_sha256,
            source_commit_sha=candidate.manifest.source_commit_sha,
            inventory_sha256=inventory.inventory_sha256,
            dependency_sha256=inventory.dependency_sha256,
            workflow_sha256=inventory.workflow_sha256,
            sbom_sha256=canonical_sha256(sbom),
            artifact_hashes=dict(sorted(candidate.manifest.artifact_hashes.items())),
            execution_context=ExecutionContext.TEST,
            production_credentials_used=False,
            human_release_decision_issued=False,
        )

    return ReleaseIntegrityResult(
        valid=not has_errors,
        candidate=candidate,
        inventory=inventory,
        sbom=sbom,
        attestation=attestation,
        findings=findings,
    )
