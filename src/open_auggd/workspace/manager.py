"""WorkspaceManager — create, list, resolve, delete, and inspect workspaces."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Optional

from uuid_extensions import uuid7 as _uuid7_gen  # type: ignore[import-untyped]

from open_auggd.workspace.slugify import slugify

# ---------------------------------------------------------------------------
# Workspace ID helpers
# ---------------------------------------------------------------------------


def _new_workspace_id(slug: str) -> str:
    """Generate a time-ordered workspace directory name.

    Format: ``<uuid7-base64url-22chars>-<normalized-slug>``
    """
    import base64

    raw = _uuid7_gen()
    # uuid7 returns a UUID object; encode to base64url (22 chars, no padding)
    b = raw.bytes  # type: ignore[union-attr]
    b64 = base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")
    return f"{b64}-{slug}"


def _slug_from_id(ws_id: str) -> str:
    """Extract the slug portion from a workspace directory name."""
    # Format: <22chars>-<slug>
    # UUID7 base64url is always 22 chars, then '-', then slug
    return ws_id[23:] if len(ws_id) > 23 else ws_id


# ---------------------------------------------------------------------------
# WorkspaceInfo
# ---------------------------------------------------------------------------


class WorkspaceInfo:
    """Lightweight descriptor for a single workspace."""

    def __init__(self, path: Path) -> None:
        """Initialize from the workspace directory path."""
        self.path = path
        self.id = path.name
        self.slug = _slug_from_id(self.id)

    # ------------------------------------------------------------------
    # Iteration counting helpers
    # ------------------------------------------------------------------

    def _iter_count(self, subdir: str, pattern: str) -> int:
        """Count JSON files matching *pattern* in *subdir*."""
        d = self.path / subdir
        if not d.exists():
            return 0
        return len(list(d.glob(pattern)))

    @property
    def planned_count(self) -> int:
        """Number of iteration plan JSON files."""
        return self._iter_count("plan", "iter-*-plan.json")

    @property
    def dev_count(self) -> int:
        """Number of iteration devlog JSON files."""
        return self._iter_count("develop", "iter-*-devlog.json")

    @property
    def reviewed_count(self) -> int:
        """Number of iteration review JSON files."""
        return self._iter_count("review", "iter-*-review.json")

    @property
    def current_phase(self) -> str:
        """Derive the active phase by checking which artifacts exist."""
        if self.reviewed_count > 0:
            return "review"
        if self.dev_count > 0:
            return "develop"
        if self.planned_count > 0:
            return "plan"
        attachments = self.path / "explore" / "attachments.json"
        if attachments.exists():
            return "explore"
        return "new"

    def next_iter_n(self) -> int:
        """Return the next iteration number (globally monotonic per workspace)."""
        existing = []
        for pattern, subdir in [
            ("iter-*-plan.json", "plan"),
            ("iter-*-devlog.json", "develop"),
            ("iter-*-review.json", "review"),
        ]:
            d = self.path / subdir
            if d.exists():
                for f in d.glob(pattern):
                    try:
                        n = int(f.name.split("-")[1])
                        existing.append(n)
                    except (IndexError, ValueError):
                        pass
        return (max(existing) + 1) if existing else 1

    def spec_description(self) -> Optional[str]:
        """Return the first non-empty line from plan/spec.md if it exists."""
        spec = self.path / "plan" / "spec.md"
        if not spec.exists():
            return None
        for line in spec.read_text(encoding="utf-8").splitlines():
            stripped = line.strip().lstrip("#").strip()
            if stripped:
                return stripped
        return None

    def __repr__(self) -> str:
        """Return a string representation."""
        return f"WorkspaceInfo(id={self.id!r}, slug={self.slug!r})"


# ---------------------------------------------------------------------------
# WorkspaceManager
# ---------------------------------------------------------------------------


class WorkspaceManager:
    """Manages workspace directories under *workspace_root*."""

    def __init__(self, workspace_root: Path) -> None:
        """Initialize the manager with the workspace root directory."""
        self.workspace_root = workspace_root

    def _ensure_root(self) -> None:
        """Create the workspace root directory if it doesn't exist."""
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # List / resolve
    # ------------------------------------------------------------------

    def list_workspaces(self) -> list[WorkspaceInfo]:
        """Return all workspaces sorted by creation time (UUID7 order).

        Returns:
            List of WorkspaceInfo objects, oldest first.
        """
        if not self.workspace_root.exists():
            return []
        entries = [d for d in self.workspace_root.iterdir() if d.is_dir()]
        # UUID7 base64url sorts lexicographically by creation time
        entries.sort(key=lambda d: d.name)
        return [WorkspaceInfo(e) for e in entries]

    def resolve(self, ref: str) -> Optional[WorkspaceInfo]:
        """Resolve *ref* to a WorkspaceInfo by list number or slug substring.

        Args:
            ref: Either a 1-based integer string (list number) or an
                 unambiguous slug substring.

        Returns:
            Matching WorkspaceInfo, or None if not found.

        Raises:
            ValueError: If *ref* is an integer out of range, or if the slug
                substring matches more than one workspace.
        """
        workspaces = self.list_workspaces()
        if not workspaces:
            return None

        # Try numeric reference first
        if ref.isdigit():
            idx = int(ref) - 1
            if idx < 0 or idx >= len(workspaces):
                raise ValueError(f"Workspace number {ref} is out of range (1–{len(workspaces)}).")
            return workspaces[idx]

        # Slug substring match
        matches = [ws for ws in workspaces if ref in ws.slug]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError(
                f"Slug substring {ref!r} is ambiguous — matches: "
                + ", ".join(ws.slug for ws in matches)
            )
        return None

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(self, task_slug: str) -> WorkspaceInfo:
        """Create a new workspace for *task_slug*.

        Creates the workspace directory with all phase subdirectories and
        a tmp/ scratch space.

        Args:
            task_slug: Raw task description (will be normalized).

        Returns:
            WorkspaceInfo for the newly created workspace.

        Raises:
            ValueError: If the slug normalizes to an empty string.
        """
        self._ensure_root()
        slug = slugify(task_slug)
        ws_id = _new_workspace_id(slug)
        ws_path = self.workspace_root / ws_id

        # Create phase subdirectories
        for subdir in ["explore", "plan", "develop", "review", "tmp"]:
            (ws_path / subdir).mkdir(parents=True, exist_ok=True)

        return WorkspaceInfo(ws_path)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, ref: str) -> WorkspaceInfo:
        """Hard-delete a workspace by list number or slug substring.

        Args:
            ref: Workspace number (1-based) or unambiguous slug substring.

        Returns:
            WorkspaceInfo of the deleted workspace.

        Raises:
            ValueError: If *ref* does not resolve to exactly one workspace.
        """
        ws = self.resolve(ref)
        if ws is None:
            raise ValueError(f"No workspace matching {ref!r}.")
        shutil.rmtree(ws.path)
        return ws

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    def info(self, ref: str) -> dict:
        """Return a summary dict for a workspace.

        Args:
            ref: Workspace number or slug substring.

        Returns:
            Dict with id, slug, phase, iters, and optional spec description.

        Raises:
            ValueError: If *ref* does not resolve.
        """
        ws = self.resolve(ref)
        if ws is None:
            raise ValueError(f"No workspace matching {ref!r}.")

        # Gather topic list from explore/attachments.json if present
        topics: list[str] = []
        attachments_file = ws.path / "explore" / "attachments.json"
        if attachments_file.exists():
            try:
                data = json.loads(attachments_file.read_text(encoding="utf-8"))
                topics = data.get("topics", [])
            except (json.JSONDecodeError, OSError):
                pass

        return {
            "id": ws.id,
            "slug": ws.slug,
            "phase": ws.current_phase,
            "planned": ws.planned_count,
            "dev": ws.dev_count,
            "reviewed": ws.reviewed_count,
            "topics": topics,
            "spec_description": ws.spec_description(),
        }
