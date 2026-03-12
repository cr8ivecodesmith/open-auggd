"""WorkspaceManager: create, list, resolve, delete, and info for workspaces."""

from __future__ import annotations

import base64
import json
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from uuid_extensions import uuid7  # type: ignore[import-untyped]

from open_auggd.workspace.models import (
    WorkspaceListItem,
    WorkspaceMetadata,
    WsInfoIteration,
    WsInfoOutput,
)
from open_auggd.workspace.slugify import slugify


class WorkspaceError(Exception):
    """Raised when a workspace operation cannot proceed."""


def _generate_id() -> str:
    """Generate a base64url-encoded UUID7 identifier (22 chars, no padding)."""
    uid: uuid.UUID = uuid7()  # type: ignore[assignment]
    raw: bytes = uid.bytes
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _read_spec_title(ws_path: Path) -> str:
    """Extract the title from spec.md YAML frontmatter, or return empty string.

    Scans lines between the opening and closing ``---`` delimiters for a
    ``title: <value>`` entry. Does not parse full YAML — only the title key.

    Args:
        ws_path: Workspace directory path.

    Returns:
        Title string, or ``""`` if spec.md is absent or title key not found.
    """
    spec_file = ws_path / "spec.md"
    if not spec_file.exists():
        return ""
    text = spec_file.read_text()
    lines = text.splitlines()
    # Must start with --- on the first line.
    if not lines or lines[0].strip() != "---":
        return ""
    in_frontmatter = False
    for line in lines:
        if line.strip() == "---":
            if not in_frontmatter:
                in_frontmatter = True
                continue
            else:
                break  # closing delimiter reached
        if in_frontmatter:
            m = re.match(r"^title\s*:\s*(.+)$", line)
            if m:
                return m.group(1).strip()
    return ""


def _derive_current_state(
    iter_log: dict[str, Any],
) -> tuple[str | None, int | None, bool | None]:
    """Derive current phase, iteration, and interrupted state from the iteration log.

    All three values are ``None`` when the log is empty (workspace not yet started).

    The current iteration is the highest integer key in the log. The current phase
    is the last phase entry in that iteration whose status is not ``"done"``; if all
    phases are done, the last phase key is used. Interrupted reflects whether the
    current phase's status is ``"interrupted"``.

    Args:
        iter_log: The parsed ``iteration-log.json`` dict.

    Returns:
        Tuple of ``(phase, iteration, interrupted)``, all ``None`` when log is empty.
    """
    if not iter_log:
        return None, None, None

    iteration = max(int(k) for k in iter_log.keys())
    current_entry: dict[str, Any] = iter_log[str(iteration)]

    # Find the current phase: last phase whose status is not "done".
    phase: str | None = None
    for p, data in current_entry.items():
        if isinstance(data, dict):
            if data.get("status") != "done":
                phase = p
            else:
                phase = p  # track last seen even if done
    # If every phase was done, phase is the last key — that's correct.
    # If no phases at all, phase stays None.

    if phase is None:
        return None, iteration, None

    phase_status = (
        current_entry[phase].get("status") if isinstance(current_entry.get(phase), dict) else None
    )
    interrupted = phase_status == "interrupted"

    return phase, iteration, interrupted


class WorkspaceManager:
    """Manages workspaces under a given workspace root directory."""

    def __init__(self, workspace_dir: Path) -> None:
        """Initialise with the workspace root directory.

        Args:
            workspace_dir: Root directory under which all workspace dirs live.
        """
        self._root = workspace_dir

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def create(self, slug_input: str) -> WorkspaceMetadata:
        """Create a new workspace.

        Generates a UUID7 ID, normalises the slug, creates the workspace
        directory structure, and writes ``workspace-metadata.json`` (identity
        only), ``iteration-log.json``, ``files-manifest.json``, ``attachments/``
        and ``tmp/`` subdirectories.

        Args:
            slug_input: User-provided slug (will be normalised).

        Returns:
            The newly created ``WorkspaceMetadata``.
        """
        slug = slugify(slug_input)
        ws_id = _generate_id()
        now = _now()

        ws_dir = self._root / f"{ws_id}-{slug}"
        ws_dir.mkdir(parents=True, exist_ok=False)

        (ws_dir / "attachments").mkdir()
        (ws_dir / "tmp").mkdir()

        metadata = WorkspaceMetadata(
            id=ws_id,
            slug=slug,
            created_at=now,
            updated_at=now,
        )
        (ws_dir / "workspace-metadata.json").write_text(
            json.dumps(metadata.to_dict(), indent=2) + "\n"
        )
        (ws_dir / "iteration-log.json").write_text("{}\n")
        (ws_dir / "files-manifest.json").write_text("{}\n")

        return metadata

    def list(self) -> list[WorkspaceListItem]:
        """Return all workspaces sorted lexicographically by directory name.

        UUID7 IDs are time-ordered, so lexicographic sort on ``<id>-<slug>``
        is equivalent to chronological creation order.

        Each item is enriched with the title from ``spec.md`` frontmatter
        (if present) and phase/iteration/interrupted derived from the
        iteration log on demand.

        Returns:
            List of ``WorkspaceListItem`` objects.
        """
        items: list[tuple[str, WorkspaceListItem]] = []
        if not self._root.exists():
            return []
        for ws_dir in self._root.iterdir():
            if not ws_dir.is_dir():
                continue
            meta_path = ws_dir / "workspace-metadata.json"
            if not meta_path.exists():
                continue
            data: dict[str, Any] = json.loads(meta_path.read_text())
            metadata = WorkspaceMetadata.from_dict(data)

            title = _read_spec_title(ws_dir)

            iter_log: dict[str, Any] = {}
            iter_log_path = ws_dir / "iteration-log.json"
            if iter_log_path.exists():
                iter_log = json.loads(iter_log_path.read_text())

            phase, iteration, interrupted = _derive_current_state(iter_log)

            items.append(
                (
                    ws_dir.name,
                    WorkspaceListItem(
                        metadata=metadata,
                        title=title,
                        phase=phase,
                        iteration=iteration,
                        interrupted=interrupted,
                    ),
                )
            )

        items.sort(key=lambda t: t[0])
        return [item for _, item in items]

    def resolve(self, ref: str) -> Path:
        """Resolve a workspace reference to its directory path.

        A reference can be:
        - A 1-based integer index (as a string) into the sorted list.
        - An exact slug string.

        Args:
            ref: Integer index (e.g. ``"1"``) or slug string.

        Returns:
            Absolute path to the workspace directory.

        Raises:
            WorkspaceError: If no matching workspace is found.
        """
        workspaces = self.list()

        # Try 1-based integer index first.
        try:
            idx = int(ref)
            if 1 <= idx <= len(workspaces):
                meta = workspaces[idx - 1].metadata
                return self._root / f"{meta.id}-{meta.slug}"
            raise WorkspaceError(f"Workspace not found: index {ref!r}")
        except ValueError:
            pass

        # Try exact slug match.
        for item in workspaces:
            if item.metadata.slug == ref:
                return self._root / f"{item.metadata.id}-{item.metadata.slug}"

        raise WorkspaceError(f"Workspace not found: {ref!r}")

    def delete(self, ref: str) -> None:
        """Delete a workspace by index or slug.

        Args:
            ref: Integer index or slug.

        Raises:
            WorkspaceError: If no matching workspace is found.
        """
        ws_path = self.resolve(ref)
        shutil.rmtree(ws_path)

    def info(self, ref: str, last: int = 3) -> WsInfoOutput:
        """Return the context prime output for a workspace.

        Args:
            ref: Integer index or slug.
            last: Number of most recent iterations to include (default 3).

        Returns:
            ``WsInfoOutput`` with all fields populated.

        Raises:
            WorkspaceError: If no matching workspace is found.
        """
        ws_path = self.resolve(ref)

        meta_data: dict[str, Any] = json.loads((ws_path / "workspace-metadata.json").read_text())
        metadata = WorkspaceMetadata.from_dict(meta_data)

        iteration_log: dict[str, Any] = json.loads((ws_path / "iteration-log.json").read_text())

        # Build last_n_iterations from iteration-log, most recent `last` entries.
        iter_keys = sorted(iteration_log.keys(), key=lambda k: int(k))
        recent_keys = iter_keys[-last:] if last > 0 else iter_keys

        last_n: list[WsInfoIteration] = []
        for key in recent_keys:
            entry: dict[str, Any] = iteration_log[key]
            last_n.append(
                WsInfoIteration(
                    n=int(key),
                    explore_status=entry.get("explore", {}).get("status")
                    if "explore" in entry
                    else None,
                    plan_status=entry.get("plan", {}).get("status") if "plan" in entry else None,
                    develop_status=entry.get("develop", {}).get("status")
                    if "develop" in entry
                    else None,
                    review_status=entry.get("review", {}).get("status")
                    if "review" in entry
                    else None,
                    finalize_status=entry.get("finalize", {}).get("status")
                    if "finalize" in entry
                    else None,
                    phases={
                        phase: {k: v for k, v in data.items() if k != "status"}
                        for phase, data in entry.items()
                        if isinstance(data, dict)
                    },
                )
            )

        # Title from spec.md frontmatter.
        title = _read_spec_title(ws_path)

        # spec.md path.
        spec_file = ws_path / "spec.md"
        spec_path: str | None = str(spec_file) if spec_file.exists() else None

        # attachments/*.md — all explore-phase outputs across all iterations.
        attachments_dir = ws_path / "attachments"
        attachments: list[str] = []
        if attachments_dir.exists():
            attachments = sorted(str(p) for p in attachments_dir.glob("*.md"))

        return WsInfoOutput(
            id=metadata.id,
            slug=metadata.slug,
            title=title,
            last_n_iterations=last_n,
            spec_path=spec_path,
            attachments=attachments,
            workspace_path=str(ws_path),
        )
