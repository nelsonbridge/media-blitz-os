"""Append-only filesystem persistence for versioned policy lifecycle records."""

from __future__ import annotations

import json
from pathlib import Path

from nks.application.policy_lifecycle import (
    PolicyActivationRecord,
    PolicyBundle,
    PolicyLifecycleAction,
)
from nks.governance.boundaries import BoundaryContext


class PolicyRecordConflict(RuntimeError):
    pass


class JsonPolicyRepository:
    def __init__(self, root: Path) -> None:
        self._bundles = root / "records" / "policy-bundles"
        self._activations = root / "records" / "policy-activations"
        self._bundles.mkdir(parents=True, exist_ok=True)
        self._activations.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _token(value: str) -> str:
        return value.replace("/", "_").replace("\\", "_").replace(":", "_")

    @staticmethod
    def _append(path: Path, record: PolicyBundle | PolicyActivationRecord) -> None:
        content = json.dumps(
            record.model_dump(mode="json", exclude_none=False),
            indent=2,
            sort_keys=True,
        ) + "\n"
        if path.exists():
            if path.read_text(encoding="utf-8") == content:
                return
            raise PolicyRecordConflict(f"immutable policy record conflict: {path.name}")
        path.write_text(content, encoding="utf-8")

    def append_bundle(self, bundle: PolicyBundle) -> None:
        token = bundle.bundle_sha256.removeprefix("sha256:")
        self._append(self._bundles / f"{token}.json", bundle)

    def get_bundle(self, bundle_sha256: str) -> PolicyBundle | None:
        path = self._bundles / f"{bundle_sha256.removeprefix('sha256:')}.json"
        if not path.exists():
            return None
        return PolicyBundle.model_validate_json(path.read_text(encoding="utf-8"))

    def list_bundles(self, policy_id: str) -> list[PolicyBundle]:
        records = [
            PolicyBundle.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self._bundles.glob("*.json"))
        ]
        return sorted(
            [record for record in records if record.policy_id == policy_id],
            key=lambda record: record.version,
        )

    def append_activation(self, record: PolicyActivationRecord) -> None:
        self._append(
            self._activations / f"{self._token(record.activation_id)}.json",
            record,
        )

    def list_activations(self, policy_id: str) -> list[PolicyActivationRecord]:
        records = [
            PolicyActivationRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self._activations.glob("*.json"))
        ]
        return sorted(
            [record for record in records if record.policy_id == policy_id],
            key=lambda record: (record.recorded_at, record.activation_id),
        )

    def get_active_bundle(
        self,
        policy_id: str,
        boundary: BoundaryContext,
    ) -> PolicyBundle | None:
        matching = [
            record
            for record in self.list_activations(policy_id)
            if record.boundary == boundary
        ]
        if not matching:
            return None
        latest = matching[-1]
        if latest.action == PolicyLifecycleAction.RETIRE or latest.to_bundle_sha256 is None:
            return None
        return self.get_bundle(latest.to_bundle_sha256)
