from pathlib import Path

from nks.views.work_control import write_work_control_views


def test_repository_work_control_generator_diagnostic() -> None:
    write_work_control_views(Path("."))
