from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".toml", ".json", ".yml", ".yaml", ".txt", ".tf", ".sh"}

LEGACY_PARENT_IDENTITIES = (
    "Media Blitz OS",
    "Nelson Knowledge System",
    "nelson-knowledge-system",
)
LEGACY_REPOSITORY_SLUG = "nelsonbridge/media-blitz-os"

# These surfaces preserve historical truth, source language, generated evidence,
# or product-scoped Media Blitz records. They may contain legacy terminology but
# must not be used as current parent-system authority.
ALLOWED_LEGACY_PREFIXES = (
    "corpus/",
    "publishing/",
    "records/",
    "generated/",
    "docs/audits/",
)
ALLOWED_LEGACY_FILES = {
    "docs/project-state.md",
    "docs/canonical-records-context.md",
    "docs/chatgpt-handover.md",
}


def _iter_current_authority_text_files() -> list[Path]:
    paths: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(ROOT).as_posix()
        if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
            continue
        if relative in ALLOWED_LEGACY_FILES:
            continue
        if relative.startswith(ALLOWED_LEGACY_PREFIXES):
            continue
        paths.append(path)
    return sorted(paths)


def test_current_authority_uses_project_enki_identity() -> None:
    violations: list[str] = []
    for path in _iter_current_authority_text_files():
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        for legacy in LEGACY_PARENT_IDENTITIES:
            if legacy in text:
                violations.append(f"{relative}: contains legacy parent identity {legacy!r}")
        if LEGACY_REPOSITORY_SLUG in text:
            violations.append(
                f"{relative}: hard-codes legacy repository slug; use a relative link or an explicit historical exception"
            )

    assert not violations, "Project Enki identity violations:\n" + "\n".join(violations)


def test_identity_policy_declares_media_blitz_as_downstream_product() -> None:
    policy = (ROOT / "docs/governance/project-enki-identity-policy.md").read_text(
        encoding="utf-8"
    )
    assert "The parent system implemented by this repository is **Project Enki**" in policy
    assert "Media Blitz is a governed downstream" in policy
