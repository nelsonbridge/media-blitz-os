from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from typer.testing import CliRunner

from nks.application.consumer_contracts import compatibility_fixture
from nks.cli.root import app
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import BoundaryAction, BoundaryAuthorization, BoundaryContext


runner = CliRunner()


def test_consumer_fixture_command_is_deterministic() -> None:
    result = runner.invoke(app, ["consumer", "fixture"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == compatibility_fixture()


def test_consumer_call_executes_governed_contract(tmp_path) -> None:
    now = datetime.now(timezone.utc)
    scope = BoundaryContext(
        namespace_id="enki",
        tenant_id="tenant-cli",
        subject_id="subject-cli",
        domain="knowledge",
        audience="internal",
        execution_context=ExecutionContext.TEST,
    )
    grant = BoundaryAuthorization(
        authorization_id="AUTH-CLI-001",
        boundary=scope,
        permitted_actions={BoundaryAction.READ},
        authority_class="consumer-test",
        issued_at=now - timedelta(minutes=5),
        expires_at=now + timedelta(hours=1),
    )
    request = {
        "request_id": "REQ-CLI-001",
        "contract_version": "1.0",
        "operation": "QUERY",
        "boundary": scope.model_dump(mode="json"),
        "authorization_id": grant.authorization_id,
        "idempotency_key": "idem-cli-001",
        "payload": {"items": [{"id": "one"}]},
        "pagination": {"page_size": 10, "cursor": None},
    }
    request_path = tmp_path / "request.json"
    auth_path = tmp_path / "authorization.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    auth_path.write_text(grant.model_dump_json(), encoding="utf-8")

    result = runner.invoke(app, ["consumer", "call", str(request_path), str(auth_path)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "OK"
    assert payload["items"] == [{"id": "one"}]
    assert payload["receipt"]["idempotency_key"] == "idem-cli-001"
