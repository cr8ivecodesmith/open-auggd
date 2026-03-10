"""Tools for the explore phase.

Actions:
  start   — create explore/ structure and attachments.json if absent
  status  — read and return current attachments.json
  done    — mark explore_status = done
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from open_auggd.tools.base import ToolResult, read_json, require_files, write_json
from open_auggd.workspace.models import ExploreAttachments, ExploreStatus


def start(ws_path: Path) -> ToolResult:
    """Start the explore phase.

    Creates explore/ subdirectory and attachments.json if not already present.

    Args:
        ws_path: Resolved workspace directory path.

    Returns:
        ToolResult with current attachments data.
    """
    explore_dir = ws_path / "explore"
    explore_dir.mkdir(parents=True, exist_ok=True)

    attachments_file = explore_dir / "attachments.json"
    if not attachments_file.exists():
        attachments = ExploreAttachments(explore_status=ExploreStatus.IN_PROGRESS)
        err = write_json(attachments_file, attachments.to_dict())
        if err:
            return err

    data, err = read_json(attachments_file)
    if err:
        return err

    return ToolResult.success(data=data or {})


def status(ws_path: Path) -> ToolResult:
    """Return the current explore phase status.

    Args:
        ws_path: Resolved workspace directory path.

    Returns:
        ToolResult with attachments data, or a warning if file is absent.
    """
    attachments_file = ws_path / "explore" / "attachments.json"
    if not attachments_file.exists():
        return ToolResult.success(
            data={"explore_status": "pending"},
            warnings=["explore/attachments.json does not exist. Run 'explore start' first."],
        )
    data, err = read_json(attachments_file)
    if err:
        return err
    return ToolResult.success(data=data or {})


def done(ws_path: Path) -> ToolResult:
    """Mark the explore phase as done.

    Args:
        ws_path: Resolved workspace directory path.

    Returns:
        ToolResult confirming the status update.
    """
    attachments_file = ws_path / "explore" / "attachments.json"
    guard = require_files(
        attachments_file,
        error_code="MISSING_ATTACHMENTS",
        message_template=(
            "No explore/attachments.json found ({missing}). Run 'explore start' first."
        ),
    )
    if guard:
        return guard

    data, err = read_json(attachments_file)
    if err:
        return err

    assert data is not None
    data["explore_status"] = ExploreStatus.DONE.value
    data["updated_at"] = datetime.now(timezone.utc).isoformat()

    err = write_json(attachments_file, data)
    if err:
        return err

    return ToolResult.success(data=data)
