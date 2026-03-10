"""Install, uninstall, and reset lifecycle for open-auggd.

``auggd install``  — writes .auggd/ config + all .opencode/ managed files.
``auggd uninstall`` — removes everything tracked in install-manifest.json.
``auggd reset``    — restores .opencode/ managed files to bundled defaults.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from open_auggd.config.settings import Settings, generate_toml

# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------


def _read_manifest(settings: Settings) -> list[str]:
    """Read the install manifest, returning a list of relative path strings."""
    mf = settings.manifest_file
    if not mf.exists():
        return []
    try:
        data = json.loads(mf.read_text(encoding="utf-8"))
        return list(data.get("files", []))
    except (json.JSONDecodeError, OSError):
        return []


def _write_manifest(settings: Settings, files: list[str]) -> None:
    """Write *files* (relative path strings) to the install manifest."""
    data = {"files": sorted(set(files))}
    settings.manifest_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Template resolution
# ---------------------------------------------------------------------------


def _templates_dir() -> Path:
    """Return the path to the bundled templates directory."""
    return Path(__file__).parent.parent / "templates"


def _iter_template_files() -> list[tuple[Path, Path]]:
    """Yield (template_src, relative_dest) pairs for all managed templates.

    Relative dest is relative to the project root (e.g. ``.opencode/agents/oag-auggd.md``).
    """
    tdir = _templates_dir()
    pairs: list[tuple[Path, Path]] = []

    # agents → .opencode/agents/
    for f in sorted((tdir / "agents").glob("*.md")):
        pairs.append((f, Path(".opencode") / "agents" / f.name))

    # commands → .opencode/commands/
    for f in sorted((tdir / "commands").glob("*.md")):
        pairs.append((f, Path(".opencode") / "commands" / f.name))

    # skills → .opencode/skills/<dirname>/SKILL.md
    skills_dir = tdir / "skills"
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    dest = Path(".opencode") / "skills" / skill_dir.name / "SKILL.md"
                    pairs.append((skill_md, dest))

    # tools → .opencode/tools/
    for f in sorted((tdir / "tools").glob("*.ts")):
        pairs.append((f, Path(".opencode") / "tools" / f.name))

    return pairs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def install(settings: Settings, force: bool = False) -> list[str]:
    """Run the full install sequence.

    Creates .auggd/ with config + manifest, and copies all bundled templates
    into .opencode/.

    Args:
        settings: Resolved settings (used for paths and config generation).
        force: If True, overwrite existing .opencode/ files silently.

    Returns:
        List of relative path strings for every file written.

    Raises:
        FileExistsError: If any target file already exists and *force* is False.
    """
    project_root = settings.project_root
    written: list[str] = []

    # --- Pre-flight conflict check ---
    if not force:
        conflicts: list[str] = []
        for _, rel_dest in _iter_template_files():
            dest = project_root / rel_dest
            if dest.exists():
                conflicts.append(str(rel_dest))
        if conflicts:
            msg = "The following managed files already exist:\n"
            for path in sorted(conflicts):
                msg += f"  {path}\n"
            msg += "Use 'auggd install --force' to overwrite them."
            raise FileExistsError(msg)

    # --- .auggd/ skeleton ---
    settings.auggd_dir.mkdir(parents=True, exist_ok=True)
    settings.workspace_dir.mkdir(parents=True, exist_ok=True)

    # auggd.toml
    config_path = settings.config_file
    if not config_path.exists() or force:
        config_path.write_text(generate_toml(settings), encoding="utf-8")
        written.append(str(config_path.relative_to(project_root)))

    # ensure .gitignore covers .auggd/
    _ensure_gitignore(project_root)

    # --- .opencode/ managed files ---
    for src, rel_dest in _iter_template_files():
        dest = project_root / rel_dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        rel_str = str(rel_dest)
        shutil.copy2(src, dest)
        written.append(rel_str)

    # write manifest
    _write_manifest(settings, written)
    return written


def uninstall(settings: Settings) -> list[str]:
    """Remove all files listed in the install manifest and the .auggd/ dir.

    Args:
        settings: Resolved settings.

    Returns:
        List of relative path strings removed.
    """
    project_root = settings.project_root
    removed: list[str] = []

    manifest_files = _read_manifest(settings)
    for rel in manifest_files:
        target = project_root / rel
        if target.exists():
            target.unlink()
            removed.append(rel)
            # Remove empty parent dirs up to .opencode/
            _remove_empty_parents(target, project_root / ".opencode")

    # Remove .auggd/ entirely
    if settings.auggd_dir.exists():
        shutil.rmtree(settings.auggd_dir)
        removed.append(".auggd/")

    return removed


def reset(settings: Settings) -> list[str]:
    """Restore all .opencode/ managed files to bundled defaults.

    .auggd/ and workspace data are untouched.

    Args:
        settings: Resolved settings.

    Returns:
        List of relative path strings restored.
    """
    project_root = settings.project_root
    restored: list[str] = []

    for src, rel_dest in _iter_template_files():
        dest = project_root / rel_dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        restored.append(str(rel_dest))

    # Refresh manifest
    existing = _read_manifest(settings)
    all_files = list(set(existing) | set(restored))
    _write_manifest(settings, all_files)

    return restored


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _remove_empty_parents(path: Path, stop_at: Path) -> None:
    """Remove empty parent directories between *path* and *stop_at* (exclusive)."""
    parent = path.parent
    while parent != stop_at and parent != parent.parent:
        try:
            parent.rmdir()  # only removes if empty
        except OSError:
            break
        parent = parent.parent


def _ensure_gitignore(project_root: Path) -> None:
    """Add .auggd/ to .gitignore if not already present."""
    gitignore = project_root / ".gitignore"
    entry = ".auggd/"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if entry not in content.splitlines():
            with open(gitignore, "a", encoding="utf-8") as f:
                f.write(f"\n{entry}\n")
    else:
        gitignore.write_text(f"{entry}\n", encoding="utf-8")


def is_installed(settings: Settings) -> bool:
    """Return True if auggd appears to be installed in this project."""
    return settings.manifest_file.exists()
