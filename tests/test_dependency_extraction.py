import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_PATHS = [
    ROOT / "src" / "nks" / "domain",
    ROOT / "src" / "nks" / "application",
    ROOT / "src" / "nks" / "policies",
    ROOT / "src" / "nks" / "ports",
]
FORBIDDEN_MODULE_PREFIXES = (
    "github",
    "googleapiclient",
    "google.auth",
    "requests",
    "httpx",
)
CANONICAL_IDENTIFIER_KEYS = (
    '"id"',
    '"event_id"',
    '"request_id"',
    '"registry_id"',
    '"feedback_id"',
    '"observation_id"',
    '"transition_id"',
    '"policy_id"',
    '"receipt_id"',
    '"work_item_id"',
    '"sprint_id"',
    '"reservation_id"',
)


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def test_core_contains_no_platform_or_network_imports():
    violations: list[str] = []
    for base in CORE_PATHS:
        for path in base.rglob("*.py"):
            for module in _imported_modules(path):
                if any(
                    module == prefix or module.startswith(f"{prefix}.")
                    for prefix in FORBIDDEN_MODULE_PREFIXES
                ):
                    violations.append(f"{path.relative_to(ROOT)}: {module}")
    assert not violations, "platform dependency leaked into core: " + ", ".join(
        violations
    )


def test_canonical_records_are_open_json_files():
    record_files = sorted((ROOT / "records").glob("*/*.json"))
    assert record_files, "no canonical JSON records found"
    for path in record_files:
        text = path.read_text(encoding="utf-8")
        assert text.lstrip().startswith("{")
        assert any(key in text for key in CANONICAL_IDENTIFIER_KEYS), (
            f"canonical JSON record has no recognized identifier: {path.relative_to(ROOT)}"
        )


def test_application_source_creation_is_restricted_to_canonicalization():
    application_root = ROOT / "src" / "nks" / "application"
    violations: list[str] = []
    for path in application_root.glob("*.py"):
        if path.name == "canonicalization.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "SourceRecord"
            ):
                violations.append(str(path.relative_to(ROOT)))
    assert not violations, (
        "canonical SourceRecord construction bypasses restricted writer: "
        + ", ".join(violations)
    )
