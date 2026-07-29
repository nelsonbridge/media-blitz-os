from pathlib import Path

from nks.adapters.manual_delivery import ManualPublicationAdapter
from nks.adapters.retry import RetryingEventRepository, RetryingPublicationAdapter
from nks.domain.delivery import PublicationPayload
from nks.ports.repositories import EventRepository
from typer.testing import CliRunner
from nks.cli.main import app


def test_retrying_publication_adapter_retries(tmp_path: Path):
    class FailingAdapter(ManualPublicationAdapter):
        def __init__(self, output_root: Path) -> None:
            super().__init__(output_root)
            self.calls = 0

        def prepare(self, payload: PublicationPayload):
            self.calls += 1
            if self.calls < 2:
                raise RuntimeError("transient failure")
            return super().prepare(payload)

    output_root = tmp_path / "repo"
    adapter = RetryingPublicationAdapter(FailingAdapter(output_root), max_attempts=3)
    payload = PublicationPayload(
        publication_id="NKS-PUB-000001",
        platform="medium",
        title="Test",
        body="body",
        asset_ids=[],
        metadata={},
    )

    receipt = adapter.prepare(payload)

    assert receipt.publication_id == "NKS-PUB-000001"


def test_retrying_event_repository_retries_and_lists_events(tmp_path: Path):
    class FailingRepository(EventRepository):
        def __init__(self) -> None:
            self.events = []
            self.append_calls = 0

        def append(self, event):
            self.append_calls += 1
            if self.append_calls < 2:
                raise RuntimeError("transient failure")
            self.events.append(event)

        def list(self):
            return list(self.events)

    repo = RetryingEventRepository(FailingRepository(), max_attempts=3)
    event = object()
    repo.append(event)

    assert repo.list() == [event]


def test_retrying_event_repository_raises_after_exhausting_retries():
    class FailingRepository(EventRepository):
        def append(self, event):
            raise RuntimeError("persistent failure")

        def list(self):
            return []

    repo = RetryingEventRepository(FailingRepository(), max_attempts=2)

    try:
        repo.append(object())
    except RuntimeError as exc:
        assert str(exc) == "persistent failure"
    else:
        raise AssertionError("expected retry adapter to raise")


def test_runtime_status_cli_command(tmp_path: Path):
    repository_root = tmp_path / "repo"
    publications = repository_root / "records" / "publications"
    publications.mkdir(parents=True, exist_ok=True)
    (publications / "NKS-PUB-000001.json").write_text(
        "{\"id\": \"NKS-PUB-000001\", \"title\": \"Test\", \"artifact_id\": \"NKS-ART-000001\", \"proof_id\": \"NKS-PRF-000001\", \"narrative_id\": \"NKS-NAR-000001\", \"visual_package_id\": \"NKS-VIS-000001\", \"draft_path\": \"publishing/drafts/NKS-PUB-000001.md\", \"editorial_status\": \"ready\", \"user_approval\": \"approved\"}\n",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(app, ["runtime-status", str(repository_root)])
    assert result.exit_code == 0
    assert "Runtime Status Summary" in result.output
