from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_PATHS = [
    ROOT / "src" / "nks" / "domain",
    ROOT / "src" / "nks" / "application",
    ROOT / "src" / "nks" / "policies",
    ROOT / "src" / "nks" / "ports",
]
FORBIDDEN_IMPORT_MARKERS = (
    "import github",
    "from github",
    "googleapiclient",
    "google.auth",
    "requests",
    "httpx",
)


def test_core_contains_no_platform_or_network_imports():
    violations: list[str] = []
    for base in CORE_PATHS:
        for path in base.rglob("*.py"):
            content = path.read_text(encoding="utf-8").lower()
            for marker in FORBIDDEN_IMPORT_MARKERS:
                if marker in content:
                    violations.append(f"{path.relative_to(ROOT)}: {marker}")
    assert not violations, "platform dependency leaked into core: " + ", ".join(violations)


def test_canonical_records_are_open_json_files():
    record_files = sorted((ROOT / "records").glob("*/*.json"))
    assert record_files, "no canonical JSON records found"
    for path in record_files:
        text = path.read_text(encoding="utf-8")
        assert text.lstrip().startswith("{")
        assert '"id"' in text
