"""Tools for the document phase.

Actions:
  check            — verify git repo, return current hash + metadata status
  init             — create .auggd/document-metadata.json skeleton
  update-metadata  — write new commit hash + summary into metadata
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from open_auggd.tools.base import ToolResult, read_json, write_json
from open_auggd.workspace.models import DocumentMetadata


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def _get_git_commit_hash(project_root: Path) -> str | None:
    """Return the current HEAD commit hash, or None if not a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _is_git_repo(project_root: Path) -> bool:
    """Return True if *project_root* is inside a git repository."""
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=project_root,
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


def check(project_root: Path, metadata_file: Path) -> ToolResult:
    """Verify git repo status and return current hash + metadata state.

    Args:
        project_root: Project root directory.
        metadata_file: Path to .auggd/document-metadata.json.

    Returns:
        ToolResult with git hash and metadata info.
    """
    if not _is_git_repo(project_root):
        return ToolResult.failure(
            "NOT_GIT_REPO",
            "The project is not a git repository. Initialize git before using the document phase.",
        )

    commit_hash = _get_git_commit_hash(project_root)
    metadata_exists = metadata_file.exists()
    metadata_current = False
    last_hash = None

    if metadata_exists:
        data, _ = read_json(metadata_file)
        if data:
            last_hash = data.get("last_commit_hash")
            metadata_current = last_hash == commit_hash

    return ToolResult.success(
        data={
            "is_git_repo": True,
            "commit_hash": commit_hash,
            "metadata_exists": metadata_exists,
            "metadata_current": metadata_current,
            "last_documented_hash": last_hash,
        }
    )


def init(project_root: Path, metadata_file: Path) -> ToolResult:
    """Create the document-metadata.json skeleton.

    Args:
        project_root: Project root directory.
        metadata_file: Path to .auggd/document-metadata.json.

    Returns:
        ToolResult confirming creation.
    """
    if not _is_git_repo(project_root):
        return ToolResult.failure(
            "NOT_GIT_REPO",
            "The project is not a git repository.",
        )

    commit_hash = _get_git_commit_hash(project_root) or ""
    metadata = DocumentMetadata(last_commit_hash=commit_hash)
    err = write_json(metadata_file, metadata.to_dict())
    if err:
        return err

    return ToolResult.success(data=metadata.to_dict())


def update_metadata(metadata_file: Path, patch: dict) -> ToolResult:
    """Write new commit hash + summary into document-metadata.json.

    Args:
        metadata_file: Path to .auggd/document-metadata.json.
        patch: Fields to update (last_commit_hash, last_commit_summary,
               documents_updated, known_gaps, etc.).

    Returns:
        ToolResult with updated metadata.
    """
    if not metadata_file.exists():
        return ToolResult.failure(
            "MISSING_METADATA",
            ".auggd/document-metadata.json does not exist. Run 'document init' first.",
            missing=[str(metadata_file)],
        )

    data, err = read_json(metadata_file)
    if err:
        return err
    assert data is not None

    list_fields = {"documents_updated", "known_gaps"}
    for key, value in patch.items():
        if key in list_fields and isinstance(value, list):
            existing = data.get(key, [])
            data[key] = list(set(existing) | set(value))
        elif key != "generated_at":
            data[key] = value

    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    err = write_json(metadata_file, data)
    if err:
        return err

    return ToolResult.success(data=data)
