"""Comparative hosting evaluation and decision packaging for Sprint 30.

This module builds a deterministic, TEST-only decision package from finalist
validation state. It never creates production approval or production deployment
authority.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.application.hosting_options import REQUIRED_PRODUCTION_PREREQUISITES
from nks.application.hosting_validation import FINALISTS
from nks.governance.approvals import ExecutionContext


class FinalistEvidenceState(StrEnum):
    BLOCKED = "BLOCKED"
    NOT_EXECUTED = "NOT_EXECUTED"
    COMPLETE = "COMPLETE"


class RecommendationConfidence(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DecisionOption(StrEnum):
    SELECT_RECOMMENDED = "SELECT_RECOMMENDED"
    DEFER = "DEFER"
    REQUEST_MORE_EVIDENCE = "REQUEST_MORE_EVIDENCE"
    REJECT = "REJECT"


class ProductionPrerequisiteStatus(StrEnum):
    UNRESOLVED = "UNRESOLVED"
    PARTIALLY_VALIDATED = "PARTIALLY_VALIDATED"
    VALIDATED = "VALIDATED"


class FinalistEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    option_id: str = Field(min_length=1)
    state: FinalistEvidenceState
    evidence_ids: tuple[str, ...] = ()
    notes: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_result(self) -> "FinalistEvaluationResult":
        if self.option_id not in FINALISTS:
            raise ValueError("comparative evaluation references a non-finalist option")
        if self.state != FinalistEvidenceState.COMPLETE and self.evidence_ids:
            raise ValueError("non-complete finalist evidence must not claim campaign evidence ids")
        return self


class CrossFinalistEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["enki-cross-finalist-evaluation-v1"] = (
        "enki-cross-finalist-evaluation-v1"
    )
    execution_context: Literal[ExecutionContext.TEST] = ExecutionContext.TEST
    external_services_budget_usd: Literal[0] = 0
    comparison_dimensions: tuple[str, ...] = (
        "security",
        "governance",
        "resilience",
        "performance",
        "cost",
        "egress",
        "portability",
        "complexity",
        "recovery",
        "privacy",
        "support",
    )
    finalist_results: tuple[FinalistEvaluationResult, ...] = Field(min_length=3, max_length=3)
    recommendation: str = Field(min_length=1)
    confidence: RecommendationConfidence
    winner_option_id: str | None = None
    human_decision_required: Literal[True] = True
    evaluation_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_evaluation(self) -> "CrossFinalistEvaluation":
        option_ids = tuple(item.option_id for item in self.finalist_results)
        if option_ids != FINALISTS:
            raise ValueError("comparative evaluation must report finalists in canonical order")

        has_incomplete = any(
            item.state != FinalistEvidenceState.COMPLETE for item in self.finalist_results
        )
        if has_incomplete:
            if self.winner_option_id is not None:
                raise ValueError("winner cannot be selected when finalist evidence is incomplete")
            if "DEFER" not in self.recommendation:
                raise ValueError("incomplete evidence must preserve an explicit defer recommendation")

        expected = canonical_sha256(self.model_dump(mode="python", exclude={"evaluation_sha256"}))
        if self.evaluation_sha256 != expected:
            raise ValueError("comparative evaluation hash is invalid")
        return self


class ProductionControlStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    prerequisite_id: str = Field(min_length=1)
    status: ProductionPrerequisiteStatus
    validation_path: str = Field(min_length=1)


class HostingDirectionDecisionPackage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["enki-hosting-direction-v1"] = "enki-hosting-direction-v1"
    generated_at: datetime
    execution_context: Literal[ExecutionContext.TEST] = ExecutionContext.TEST
    comparative_evaluation: CrossFinalistEvaluation
    production_controls: tuple[ProductionControlStatus, ...] = Field(min_length=7, max_length=7)
    decision_options: tuple[DecisionOption, ...] = (
        DecisionOption.SELECT_RECOMMENDED,
        DecisionOption.DEFER,
        DecisionOption.REQUEST_MORE_EVIDENCE,
        DecisionOption.REJECT,
    )
    recommendation: str = Field(min_length=1)
    recommended_option_id: str | None = None
    confidence: RecommendationConfidence
    limitations: tuple[str, ...] = Field(min_length=1)
    accepted_risks: tuple[str, ...] = ()
    human_decision_required: Literal[True] = True
    production_approval: Literal[False] = False
    production_deployment_authorized: Literal[False] = False
    package_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_package(self) -> "HostingDirectionDecisionPackage":
        prerequisite_ids = {item.prerequisite_id for item in self.production_controls}
        if prerequisite_ids != REQUIRED_PRODUCTION_PREREQUISITES:
            raise ValueError("package must declare every required production prerequisite exactly once")

        has_unresolved = any(
            item.status != ProductionPrerequisiteStatus.VALIDATED
            for item in self.production_controls
        )
        if has_unresolved and self.recommended_option_id is not None:
            raise ValueError("recommended option cannot be selected while production controls remain unresolved")
        if self.recommended_option_id is None and "DEFER" not in self.recommendation:
            raise ValueError("missing recommended option must preserve an explicit defer recommendation")

        expected = canonical_sha256(self.model_dump(mode="python", exclude={"package_sha256"}))
        if self.package_sha256 != expected:
            raise ValueError("hosting direction package hash is invalid")
        return self


def build_cross_finalist_evaluation() -> CrossFinalistEvaluation:
    draft = CrossFinalistEvaluation.model_construct(
        finalist_results=(
            FinalistEvaluationResult(
                option_id="CF-NATIVE",
                state=FinalistEvidenceState.BLOCKED,
                notes=(
                    "Sprint 26 remains blocked: Cloudflare TEST identity, TEST credentials, "
                    "and teardown authority are not currently available in the execution surface."
                ),
            ),
            FinalistEvaluationResult(
                option_id="CF-NEON-R2",
                state=FinalistEvidenceState.NOT_EXECUTED,
                notes="Sprint 27 hosted TEST validation has not started.",
            ),
            FinalistEvaluationResult(
                option_id="GCP-NEON-R2",
                state=FinalistEvidenceState.NOT_EXECUTED,
                notes="Sprint 28 hosted TEST validation has not started.",
            ),
        ),
        recommendation=(
            "DEFER hosting direction until finalist TEST campaigns complete and cross-finalist "
            "evidence is comparable."
        ),
        confidence=RecommendationConfidence.LOW,
        evaluation_sha256="sha256:" + "0" * 64,
    )
    payload = draft.model_dump(mode="python")
    payload["evaluation_sha256"] = canonical_sha256(
        draft.model_dump(mode="python", exclude={"evaluation_sha256"})
    )
    return CrossFinalistEvaluation.model_validate(payload)


def build_hosting_direction_decision_package() -> HostingDirectionDecisionPackage:
    evaluation = build_cross_finalist_evaluation()
    controls = tuple(
        ProductionControlStatus(
            prerequisite_id=prerequisite,
            status=ProductionPrerequisiteStatus.UNRESOLVED,
            validation_path=(
                "UNRESOLVED: requires production-scope validation evidence in a separate "
                "human-approved production-control program."
            ),
        )
        for prerequisite in sorted(REQUIRED_PRODUCTION_PREREQUISITES)
    )

    draft = HostingDirectionDecisionPackage.model_construct(
        generated_at=datetime(2026, 7, 16, 21, 30, tzinfo=timezone.utc),
        comparative_evaluation=evaluation,
        production_controls=controls,
        recommendation=(
            "DEFER production hosting selection until BL-027, BL-028, and BL-029 evidence "
            "is complete and independently reviewed."
        ),
        confidence=RecommendationConfidence.LOW,
        limitations=(
            "CF-NATIVE campaign is blocked on missing TEST credential and teardown authority.",
            "CF-NEON-R2 and GCP-NEON-R2 campaigns are not yet executed.",
            "No production-control prerequisite has production-scope validation evidence.",
        ),
        accepted_risks=(
            "Decision latency while finalist validation evidence is incomplete.",
        ),
        package_sha256="sha256:" + "0" * 64,
    )
    payload = draft.model_dump(mode="python")
    payload["package_sha256"] = canonical_sha256(
        draft.model_dump(mode="python", exclude={"package_sha256"})
    )
    return HostingDirectionDecisionPackage.model_validate(payload)
