"""Model frontmatter updater for managed agent and command files.

``auggd update`` patches only the ``model:`` frontmatter line in managed
``.opencode/agents/oag-*.md`` and ``.opencode/commands/oag-*.md`` files
without touching content or other frontmatter fields.
"""

from __future__ import annotations

import re
from pathlib import Path

from open_auggd.config.settings import Settings

_FRONTMATTER_DELIM = "---"
_MODEL_RE = re.compile(r"^model:\s*.+$", re.MULTILINE)


def _patch_model_frontmatter(content: str, new_model: str) -> str:
    """Replace or insert the ``model:`` line in the YAML frontmatter.

    If there is no existing ``model:`` line in the frontmatter block it is
    inserted after the opening ``---``.

    Args:
        content: Full file content.
        new_model: Model string to set.

    Returns:
        Updated file content.
    """
    lines = content.split("\n")
    if not lines or lines[0].strip() != _FRONTMATTER_DELIM:
        # No frontmatter — prepend a minimal block
        return f"---\nmodel: {new_model}\n---\n{content}"

    # Find closing ---
    end_idx: int | None = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == _FRONTMATTER_DELIM:
            end_idx = i
            break

    if end_idx is None:
        # Malformed frontmatter — don't touch it
        return content

    # Search for an existing model: line within frontmatter
    model_idx: int | None = None
    for i in range(1, end_idx):
        if re.match(r"^model:\s*", lines[i]):
            model_idx = i
            break

    if model_idx is not None:
        lines[model_idx] = f"model: {new_model}"
    else:
        # Insert after opening ---
        lines.insert(1, f"model: {new_model}")

    return "\n".join(lines)


def update_models(settings: Settings) -> list[str]:
    """Patch the ``model:`` frontmatter in all managed agent and command files.

    Only files whose names start with ``oag-`` are touched.

    Args:
        settings: Resolved settings (provides model values and paths).

    Returns:
        List of relative path strings for every file updated.
    """
    project_root = settings.project_root
    updated: list[str] = []

    # Agents
    agents_dir = settings.opencode_dir / "agents"
    if agents_dir.exists():
        # Special case: auggd.md has no oag- prefix
        auggd_file = agents_dir / "auggd.md"
        if auggd_file.exists():
            model = settings.model_for_agent("auggd")
            _update_file(auggd_file, model)
            updated.append(str(auggd_file.relative_to(project_root)))
        for md_file in sorted(agents_dir.glob("oag-*.md")):
            agent_name = md_file.stem[4:]  # strip "oag-"
            model = settings.model_for_agent(agent_name)
            _update_file(md_file, model)
            updated.append(str(md_file.relative_to(project_root)))

    # Commands
    commands_dir = settings.opencode_dir / "commands"
    if commands_dir.exists():
        for md_file in sorted(commands_dir.glob("oag-*.md")):
            cmd_name = md_file.stem[4:]  # strip "oag-"
            model = settings.model_for_command(cmd_name)
            _update_file(md_file, model)
            updated.append(str(md_file.relative_to(project_root)))

    return updated


def _update_file(path: Path, model: str) -> None:
    """Read *path*, patch the model frontmatter, and write it back."""
    content = path.read_text(encoding="utf-8")
    patched = _patch_model_frontmatter(content, model)
    if patched != content:
        path.write_text(patched, encoding="utf-8")
