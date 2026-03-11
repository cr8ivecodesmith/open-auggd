"""Install/uninstall/reset logic and install-manifest management."""

from __future__ import annotations

import importlib.resources
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

# Relative import path within the package for templates
_TEMPLATES_PKG = "open_auggd.templates"

_AUGGD_TOML_TEMPLATE = """\
[workspace]
dir = ".auggd/workspace"

[docs]
dir = "docs"

[defaults]
model = "opencode/gpt-5-nano"

[agents.models]
# explorer = "anthropic/claude-sonnet-4-6"
# developer = "anthropic/claude-sonnet-4-6"

[commands.models]
# develop = "anthropic/claude-sonnet-4-6"
"""


class InstallError(Exception):
    """Raised when an install lifecycle operation cannot proceed."""


class Installer:
    """Manages the auggd install lifecycle for a project root."""

    def __init__(self, project_root: Path) -> None:
        """Initialise with the project root directory."""
        self._root = project_root

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def install(self) -> list[str]:
        """Install auggd into the project.

        Creates .auggd/ with auggd.toml and copies all bundled templates into
        .opencode/. Writes install-manifest.json recording every file path written.

        Returns:
            List of relative paths written (same as manifest["files"]).

        Raises:
            InstallError: If auggd is already installed. Use reset to restore files.
        """
        if self._manifest_path().exists():
            raise InstallError(
                "auggd is already installed in this project. "
                "Use 'auggd reset' to restore managed files to bundled defaults."
            )

        auggd_dir = self._root / ".auggd"
        auggd_dir.mkdir(exist_ok=True)

        toml_path = auggd_dir / "auggd.toml"
        if not toml_path.exists():
            toml_path.write_text(_AUGGD_TOML_TEMPLATE)

        written = self._copy_templates()

        manifest = {
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "files": sorted(written),
        }
        (auggd_dir / "install-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        return written

    def uninstall(self, confirmed: bool) -> None:
        """Remove all managed files and .auggd/ entirely.

        Pre-existing .opencode/ content not listed in the manifest is untouched.

        Args:
            confirmed: Must be True; False raises InstallError without touching anything.

        Raises:
            InstallError: If not confirmed, or if the project is not installed.
        """
        self._load_manifest()  # raises if not installed
        if not confirmed:
            raise InstallError(
                "uninstall requires confirmed=True. Prompt the user: Type 'yes' to confirm:"
            )

        manifest = self._load_manifest()
        _core_dirs = {
            self._root / ".opencode" / d for d in ("agents", "commands", "skills", "tools")
        }

        for rel in manifest["files"]:
            target = self._root / rel
            if target.exists():
                target.unlink()
            # Remove the immediate parent if it is now empty and is not one of
            # the four core .opencode/ subdirectories (agents, commands, skills, tools).
            parent = target.parent
            if parent not in _core_dirs and parent.exists() and not any(parent.iterdir()):
                parent.rmdir()

        # Remove .auggd/ entirely
        auggd_dir = self._root / ".auggd"
        if auggd_dir.exists():
            shutil.rmtree(auggd_dir)

    def reset(self, confirmed: bool) -> list[str]:
        """Restore all managed .opencode/ files to their bundled defaults.

        .auggd/ config and workspace data are not affected.
        The not-installed check runs before the confirmation check so the user
        does not have to confirm before learning the operation cannot proceed.

        Args:
            confirmed: Must be True; False raises InstallError after the
                not-installed guard passes.

        Returns:
            List of relative paths restored.

        Raises:
            InstallError: If the project is not installed, or if not confirmed.
        """
        self._load_manifest()  # raises if not installed — checked before confirmation
        if not confirmed:
            raise InstallError(
                "reset requires confirmed=True. Prompt the user: Type 'yes' to confirm:"
            )
        return self._copy_templates()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _manifest_path(self) -> Path:
        return self._root / ".auggd" / "install-manifest.json"

    def _load_manifest(self) -> dict:
        """Load and return the install manifest.

        Raises:
            InstallError: If the manifest does not exist.
        """
        p = self._manifest_path()
        if not p.exists():
            raise InstallError(
                "auggd is not installed in this project (no .auggd/install-manifest.json found)."
            )
        return json.loads(p.read_text())  # type: ignore[no-any-return]

    def _copy_templates(self) -> list[str]:
        """Copy all bundled templates into .opencode/; return relative paths."""
        written: list[str] = []
        opencode = self._root / ".opencode"

        # We traverse the templates package using importlib.resources.
        # Python 3.12 supports Traversable API cleanly.
        templates_ref = importlib.resources.files(_TEMPLATES_PKG)

        for category in ("agents", "commands", "skills", "tools"):
            src_category = templates_ref / category
            dst_category = opencode / category

            if category == "skills":
                # skills/<skill-name>/SKILL.md
                for skill_dir in _iter_subdirs(src_category):
                    skill_name = skill_dir.name
                    dst_skill_dir = dst_category / skill_name
                    dst_skill_dir.mkdir(parents=True, exist_ok=True)
                    skill_md = skill_dir / "SKILL.md"
                    dst_file = dst_skill_dir / "SKILL.md"
                    dst_file.write_text(skill_md.read_text())
                    written.append(f".opencode/skills/{skill_name}/SKILL.md")
            else:
                # agents/*.md, commands/*.md, tools/*.ts
                dst_category.mkdir(parents=True, exist_ok=True)
                for src_file in _iter_files(src_category):
                    dst_file = dst_category / src_file.name
                    dst_file.write_text(src_file.read_text())
                    written.append(f".opencode/{category}/{src_file.name}")

        return written


# ---------------------------------------------------------------------------
# importlib.resources helpers (Traversable API)
# ---------------------------------------------------------------------------


def _iter_subdirs(traversable):  # type: ignore[return]
    """Yield Traversable items that are directories."""
    for item in traversable.iterdir():
        if item.is_dir():
            yield item


def _iter_files(traversable):  # type: ignore[return]
    """Yield Traversable items that are files."""
    for item in traversable.iterdir():
        if item.is_file():
            yield item
