"""Model frontmatter update logic for managed agent and command files."""

from __future__ import annotations

import re
from pathlib import Path

from open_auggd.config.settings import Settings
from open_auggd.install.installer import InstallError

_MODEL_LINE_RE = re.compile(r"^(model:\s*)(.+)$", re.MULTILINE)


def update_model_lines(project_root: Path, settings: Settings) -> list[str]:
    """Rewrite the `model:` frontmatter line in all managed agent and command files.

    Only agent (.opencode/agents/*.md) and command (.opencode/commands/*.md) files
    are touched. Skills and tools are not modified.

    Uses per-agent/per-command model from settings when configured; falls back to
    settings.default_model.

    Args:
        project_root: Root of the project (where .auggd/ lives).
        settings: Resolved settings providing model values.

    Returns:
        List of relative paths that were updated.

    Raises:
        InstallError: If the project is not installed.
    """
    manifest_path = project_root / ".auggd" / "install-manifest.json"
    if not manifest_path.exists():
        raise InstallError(
            "auggd is not installed in this project (no .auggd/install-manifest.json found)."
        )

    updated: list[str] = []

    for category, model_fn in (
        ("agents", _agent_model),
        ("commands", _command_model),
    ):
        target_dir = project_root / ".opencode" / category
        if not target_dir.exists():
            continue
        for md_file in sorted(target_dir.glob("*.md")):
            name = _stem_name(md_file.name, category)
            model_value = model_fn(name, settings)
            new_content = _replace_model_line(md_file.read_text(), model_value)
            if new_content != md_file.read_text():
                md_file.write_text(new_content)
                updated.append(f".opencode/{category}/{md_file.name}")

    return updated


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stem_name(filename: str, category: str) -> str:
    """Derive the bare agent/command name from a filename.

    Examples:
        oag-developer.md  → developer   (agents)
        auggd.md          → auggd       (agents)
        oag-develop.md    → develop     (commands)
    """
    stem = filename.removesuffix(".md")
    if stem.startswith("oag-"):
        stem = stem[4:]
    return stem


def _agent_model(name: str, settings: Settings) -> str:
    return settings.effective_agent_model(name)


def _command_model(name: str, settings: Settings) -> str:
    return settings.effective_command_model(name)


def _replace_model_line(content: str, model_value: str) -> str:
    """Replace the value on the `model:` frontmatter line."""
    return _MODEL_LINE_RE.sub(rf"\g<1>{model_value}", content)
