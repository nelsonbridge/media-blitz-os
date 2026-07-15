from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from nks.application.consumer_adapters import ConsumerApiAdapter, ConsumerCliAdapter
from nks.application.consumer_contracts import (
    ConsumerOperation,
    ConsumerRequest,
    PaginationRequest,
    compatibility_fixture,
    render_contract_markdown,
)
from nks.application.consumer_service import (
    ConsumerGateway,
    ConsumerServiceResult,
    DeterministicConsumerApplicationService,
)
from nks.application.sprint21_path_manifest import sprint21_consumer_path_manifest
from nks.governance.approvals import ExecutionContext
from nks.governance.boundaries import (
    BoundaryAction,
    BoundaryAuthorization,
    BoundaryContext,
)


NOW = datetime(2026, 7, 15, 6, 0, tzinfo=timezone.utc)


class CountingService(DeterministicConsumerApplicationService):
    def __init__(self) -> None:
        self.calls = 0

    def execute(
        self,
        payload: dict[str, object],
        *,
        page_size: int,
        cursor: str | None,
    ) -> ConsumerServiceResult:
        self.calls += 1
        return super().execute(payload, page_size=page_size, cursor=cursor)


def boundary(subject: str = "subject-a") -> BoundaryContext:
    return BoundaryContext(
        namespace_id="enki",
        tenant_id="tenant-a",
        subject_id=subject,
        domain="knowledge",
        audience="internal",
        execution_context=ExecutionContext.TEST,
    )


def authorization(
    *,
    scope: BoundaryContext | None = None,
    actions: set[BoundaryAction] | None = None,
) -> BoundaryAuthorization:
    return BoundaryAuthorization(
        authorization_id="AUTH-S21-001",
        boundary=scope or boundary(),
        permitted_actions=actions or {BoundaryAction.READ, BoundaryAction.WRITE},
        authority_class="consumer-test",
        issued_at=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(hours=1),
    )


def request_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "request_id": "REQ-S21-001",
        "contract_version": "1.0",
        "operation": "QUERY",
        "boundary": boundary().model_dump(mode="json"),
        "authorization_id": "AUTH-S21-001",
        "idempotency_key": "idem-s21-001",
        "payload": {"items": [{"id": "A"}, {"id": "B"}, {"id": "C"}]},
        "pagination": {"page_size": 2, "cursor": None},
    }
    payload.update(overrides)
    return payload


def build_gateway(
    *,
    auth: BoundaryAuthorization | None = None,
    service: CountingService | None = None,
) -> tuple[ConsumerGateway, CountingService]:
    selected = service or CountingService()
    grant = auth or authorization()
    return (
        ConsumerGateway(
            authorizations={grant.authorization_id: grant},
            services={
                ConsumerOperation.QUERY: selected,
                ConsumerOperation.COMMAND: selected,
            },
        ),
        selected,
    )


def test_api_and_cli_use_same_gateway_authority_and_idempotency() -> None:
    gateway, service = build_gateway()
    api = ConsumerApiAdapter(gateway)
    cli = ConsumerCliAdapter(gateway)
    payload = request_payload()

    api_result = api.invoke(payload, now=NOW)
    cli_result = json.loads(cli.invoke_json(json.dumps(payload), now=NOW))

    assert api_result == cli_result
    assert api_result["status"] == "OK"
    assert api_result["pagination"] == {"returned": 2, "next_cursor": "2"}
    assert service.calls == 1


def test_exact_retry_reuses_original_response_and_receipt() -> None:
    gateway, service = build_gateway()
    first = gateway.execute(ConsumerRequest.model_validate(request_payload()), now=NOW)
    retry_payload = request_payload(request_id="REQ-S21-RETRY")
    retry = gateway.execute(ConsumerRequest.model_validate(retry_payload), now=NOW)

    assert retry == first
    assert retry.receipt.receipt_id == first.receipt.receipt_id
    assert service.calls == 1


def test_idempotency_key_reuse_with_divergent_content_fails_closed() -> None:
    gateway, _ = build_gateway()
    api = ConsumerApiAdapter(gateway)
    assert api.invoke(request_payload(), now=NOW)["status"] == "OK"

    changed = request_payload(payload={"items": [{"id": "DIFFERENT"}]})
    result = api.invoke(changed, now=NOW)
    assert result["error_code"] == "IDEMPOTENCY_CONFLICT"


def test_unsupported_and_ambiguous_versions_fail_closed() -> None:
    gateway, _ = build_gateway()
    api = ConsumerApiAdapter(gateway)

    unsupported = api.invoke(request_payload(contract_version="2.0"), now=NOW)
    ambiguous = api.invoke(request_payload(contract_version="1.0,2.0"), now=NOW)

    assert unsupported["error_code"] == "UNSUPPORTED_VERSION"
    assert ambiguous["error_code"] == "AMBIGUOUS_VERSION"
    assert unsupported["supported_versions"] == ["1.0"]


def test_boundary_and_action_authority_are_enforced_for_every_transport() -> None:
    read_only = authorization(actions={BoundaryAction.READ})
    gateway, _ = build_gateway(auth=read_only)
    api = ConsumerApiAdapter(gateway)
    cli = ConsumerCliAdapter(gateway)

    command = request_payload(operation="COMMAND", idempotency_key="command-denied")
    mismatch = request_payload(
        boundary=boundary("subject-b").model_dump(mode="json"),
        idempotency_key="boundary-denied",
    )

    assert api.invoke(command, now=NOW)["error_code"] == "AUTHORITY_DENIED"
    assert json.loads(cli.invoke_json(json.dumps(mismatch), now=NOW))[
        "error_code"
    ] == "AUTHORITY_DENIED"


def test_repository_and_approval_shortcuts_are_denied_recursively() -> None:
    gateway, _ = build_gateway()
    api = ConsumerApiAdapter(gateway)

    direct_repo = request_payload(
        payload={"nested": {"repository_path": "records/sources"}},
        idempotency_key="shortcut-1",
    )
    direct_approval = request_payload(
        payload={"consume_approval": "APPROVAL-001"},
        idempotency_key="shortcut-2",
    )

    assert api.invoke(direct_repo, now=NOW)["error_code"] == "REPOSITORY_SHORTCUT_DENIED"
    assert api.invoke(direct_approval, now=NOW)["error_code"] == "REPOSITORY_SHORTCUT_DENIED"


def test_unknown_operation_and_invalid_json_fail_closed() -> None:
    gateway, _ = build_gateway()
    api = ConsumerApiAdapter(gateway)
    cli = ConsumerCliAdapter(gateway)

    unknown = api.invoke(request_payload(operation="DIRECT_CANONICAL_WRITE"), now=NOW)
    invalid_json = json.loads(cli.invoke_json("{not-json", now=NOW))

    assert unknown["error_code"] == "INVALID_REQUEST"
    assert invalid_json["error_code"] == "INVALID_REQUEST"


def test_pagination_cursor_is_deterministic() -> None:
    gateway, _ = build_gateway()
    first = gateway.execute(ConsumerRequest.model_validate(request_payload()), now=NOW)

    second_payload = request_payload(
        request_id="REQ-S21-002",
        idempotency_key="idem-s21-002",
        pagination=PaginationRequest(page_size=2, cursor="2").model_dump(mode="json"),
    )
    second = gateway.execute(ConsumerRequest.model_validate(second_payload), now=NOW)

    assert [item["id"] for item in first.items] == ["A", "B"]
    assert [item["id"] for item in second.items] == ["C"]
    assert second.pagination.next_cursor is None


def test_generated_contract_documentation_and_fixture_are_deterministic() -> None:
    root = Path(__file__).resolve().parents[1]
    committed_doc = (root / "generated" / "contracts" / "enki-consumer-v1.md").read_text(
        encoding="utf-8"
    )
    committed_fixture = json.loads(
        (root / "contracts" / "enki-consumer-v1.json").read_text(encoding="utf-8")
    )

    assert committed_doc == render_contract_markdown()
    assert committed_fixture == compatibility_fixture()


SPRINT21_TESTED_PATHS = {
    "api-query-authorized",
    "cli-query-authorized",
    "api-cli-service-parity",
    "command-authority-checked",
    "pagination-deterministic",
    "exact-idempotent-retry",
    "idempotency-conflict-denied",
    "unsupported-version-denied",
    "ambiguous-version-denied",
    "authority-mismatch-denied",
    "repository-shortcut-denied",
    "direct-operation-denied",
    "invalid-request-denied",
    "contract-docs-deterministic",
    "compatibility-fixture-deterministic",
}


def test_every_declared_sprint21_path_has_automated_coverage() -> None:
    sprint21_consumer_path_manifest().assert_complete_coverage(SPRINT21_TESTED_PATHS)


def test_sprint21_paths_are_test_only_and_prohibit_bypass() -> None:
    manifest = sprint21_consumer_path_manifest()
    assert manifest.execution_context == ExecutionContext.TEST
    assert all("repository-shortcut" in item.prohibited_effects for item in manifest.paths)
    assert all("direct-canonical-write" in item.prohibited_effects for item in manifest.paths)
    assert all("direct-approval-consumption" in item.prohibited_effects for item in manifest.paths)
