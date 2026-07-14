"""Machine-readable operation path manifests and coverage enforcement."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import (
    RecoveryStrategy,
    TransactionTerminalState,
)
from nks.governance.approvals import ExecutionContext


class OperationPathExpectation(BaseModel):
    """Expected terminal behavior for one declared operation path."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    expected_terminal_state: TransactionTerminalState
    state_changing: bool
    recovery_strategy: RecoveryStrategy
    prohibited_effects: list[str] = Field(default_factory=list)


class OperationPathManifest(BaseModel):
    """Complete path catalog for one governed operation family."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_family: str = Field(min_length=1)
    execution_context: ExecutionContext
    paths: list[OperationPathExpectation] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_paths(self) -> "OperationPathManifest":
        path_ids = [path.path_id for path in self.paths]
        if len(path_ids) != len(set(path_ids)):
            raise ValueError("path ids must be unique")
        if self.execution_context == ExecutionContext.TEST:
            for path in self.paths:
                if "production-effect" not in path.prohibited_effects:
                    raise ValueError(
                        "every TEST path must prohibit production-effect"
                    )
        return self

    @property
    def declared_path_ids(self) -> set[str]:
        return {path.path_id for path in self.paths}

    def assert_complete_coverage(self, observed_path_ids: set[str]) -> None:
        missing = sorted(self.declared_path_ids - observed_path_ids)
        unknown = sorted(observed_path_ids - self.declared_path_ids)
        if missing or unknown:
            details: list[str] = []
            if missing:
                details.append(f"missing paths: {', '.join(missing)}")
            if unknown:
                details.append(f"undeclared paths: {', '.join(unknown)}")
            raise AssertionError("; ".join(details))
