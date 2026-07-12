from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from nks.adapters.work_control import JsonWorkControlRepository
from nks.domain.work_control import (
    BacklogItem,
    EvidenceKind,
    SprintRecord,
    WorkEvidence,
    WorkStatus,
)
from nks.views.work_control import render_backlog, render_roadmap, write_work_control_views

NOW = datetime(2026, 7, 12, tzinfo=UTC)


def evidence(identifier: str = "EV-001") -> WorkEvidence:
    return WorkEvidence(
        evidence_id=identifier,
        kind=EvidenceKind.COMMIT,
        reference="deadbeef",
        description="implementation commit",
    )


def test_complete_work_item_requires_evidence():
    with pytest.raises(ValidationError, match="require implementation evidence"):
        BacklogItem(
            work_item_id="BL-001",
            title="Identity",
            description="Fix identity contracts",
            status=WorkStatus.COMPLETE,
            sprint_id="NKS-SPR-001",
            acceptance_criteria=["audit passes"],
            updated_at=NOW,
        )


def test_blocked_and_superseded_states_require_reason_and_target():
    with pytest.raises(ValidationError, match="blocked_reason"):
        BacklogItem(
            work_item_id="BL-002",
            title="Blocked",
            description="Blocked item",
            status=WorkStatus.BLOCKED,
            acceptance_criteria=["decision recorded"],
            updated_at=NOW,
        )

    with pytest.raises(ValidationError, match="superseded_by"):
        BacklogItem(
            work_item_id="BL-003",
            title="Old",
            description="Old item",
            status=WorkStatus.SUPERSEDED,
            acceptance_criteria=["replacement exists"],
            updated_at=NOW,
        )


def test_repository_is_idempotent_and_views_are_deterministic(tmp_path: Path):
    repository = JsonWorkControlRepository(tmp_path)
    item = BacklogItem(
        work_item_id="BL-001",
        title="Canonical identity",
        description="Resolve domain identifiers",
        status=WorkStatus.COMPLETE,
        sprint_id="NKS-SPR-001",
        acceptance_criteria=["zero unexplained identity findings"],
        evidence=[evidence()],
        updated_at=NOW,
    )
    sprint = SprintRecord(
        sprint_id="NKS-SPR-001",
        sequence=1,
        title="Canonical identity",
        objective="Establish repository truth",
        status=WorkStatus.COMPLETE,
        work_item_ids=["BL-001"],
        exit_criteria=["hosted validation passes"],
        evidence=[evidence("EV-002")],
        updated_at=NOW,
    )

    repository.save_work_item(item)
    repository.save_sprint(sprint)
    first_item = (tmp_path / "records/work-items/BL-001.json").read_text()
    first_sprint = (tmp_path / "records/sprints/NKS-SPR-001.json").read_text()
    repository.save_work_item(item)
    repository.save_sprint(sprint)

    assert (tmp_path / "records/work-items/BL-001.json").read_text() == first_item
    assert (tmp_path / "records/sprints/NKS-SPR-001.json").read_text() == first_sprint
    assert repository.get_work_item("BL-001") == item
    assert repository.get_sprint("NKS-SPR-001") == sprint

    first_backlog = render_backlog(tmp_path)
    first_roadmap = render_roadmap(tmp_path)
    outputs = write_work_control_views(tmp_path)

    assert [path.name for path in outputs] == [
        "canonical-backlog.md",
        "canonical-roadmap.md",
    ]
    assert render_backlog(tmp_path) == first_backlog
    assert render_roadmap(tmp_path) == first_roadmap
    assert "| BL-001 | complete | NKS-SPR-001 |" in first_backlog
    assert "Sprint 1 — Canonical identity" in first_roadmap


def test_complete_sprint_requires_evidence():
    with pytest.raises(ValidationError, match="completion evidence"):
        SprintRecord(
            sprint_id="NKS-SPR-001",
            sequence=1,
            title="Sprint",
            objective="Objective",
            status=WorkStatus.COMPLETE,
            work_item_ids=["BL-001"],
            exit_criteria=["done"],
            updated_at=NOW,
        )
