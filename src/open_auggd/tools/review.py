"""Tools for the review phase.

Actions:
  start <N>         — create review files; prerequisite: dev_complete
  update <N> --data — merge findings into review JSON
  done <N>          — set review status (blocked/changes_requested/approved)
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from open_auggd.tools.base import ToolResult, read_json, require_files, write_json
from open_auggd.workspace.models import DevStatus, IterReview, ReviewStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _review_json(ws_path: Path, n: int) -> Path:
    return ws_path / "review" / f"iter-{n}-review.json"


def _review_md(ws_path: Path, n: int) -> Path:
    return ws_path / "review" / f"iter-{n}-review.md"


def _devlog_json(ws_path: Path, n: int) -> Path:
    return ws_path / "develop" / f"iter-{n}-devlog.json"


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


def start(ws_path: Path, n: int) -> ToolResult:
    """Start the review for iteration *n*.

    Prerequisite: iter-N-devlog.json must exist and status must be dev_complete.

    Args:
        ws_path: Resolved workspace directory path.
        n: Iteration number.

    Returns:
        ToolResult with review file paths.
    """
    devlog_json = _devlog_json(ws_path, n)
    guard = require_files(
        devlog_json,
        error_code="MISSING_DEVLOG",
        message_template=f"iter-{n}-devlog.json not found ({{missing}}). Complete development first.",
    )
    if guard:
        return guard

    data, err = read_json(devlog_json)
    if err:
        return err
    assert data is not None

    if data.get("status") != DevStatus.DEV_COMPLETE.value:
        return ToolResult.failure(
            "DEV_NOT_COMPLETE",
            f"iter-{n}-devlog.json status is '{data.get('status')}'. "
            "Mark development done first with 'develop done <N>'.",
        )

    # Create review directory
    review_dir = ws_path / "review"
    review_dir.mkdir(parents=True, exist_ok=True)

    review_json = _review_json(ws_path, n)
    review_md = _review_md(ws_path, n)

    review = IterReview(n=n, status=ReviewStatus.BLOCKED)
    err = write_json(review_json, review.to_dict())
    if err:
        return err

    review_md.write_text(
        f"# Iteration {n} Review\n\n<!-- Agent: document review findings here -->\n",
        encoding="utf-8",
    )

    return ToolResult.success(
        data={"n": n, "review_json": str(review_json), "review_md": str(review_md)}
    )


def update(ws_path: Path, n: int, patch: dict) -> ToolResult:
    """Merge *patch* fields into the review JSON for iteration *n*.

    When *patch* contains a ``findings`` list, new findings are appended to
    the existing list.

    Args:
        ws_path: Resolved workspace directory path.
        n: Iteration number.
        patch: Dict of fields to merge.

    Returns:
        ToolResult with updated review data.
    """
    review_json = _review_json(ws_path, n)
    guard = require_files(
        review_json,
        error_code="MISSING_REVIEW",
        message_template=f"iter-{n}-review.json not found ({{missing}}). Run 'review start {n}' first.",
    )
    if guard:
        return guard

    data, err = read_json(review_json)
    if err:
        return err
    assert data is not None

    for key, value in patch.items():
        if key == "findings" and isinstance(value, list):
            existing = data.get("findings", [])
            data["findings"] = existing + value
        elif key not in ("n", "updated_at"):
            data[key] = value

    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    err = write_json(review_json, data)
    if err:
        return err

    return ToolResult.success(data=data)


def done(ws_path: Path, n: int, review_status: str) -> ToolResult:
    """Set the review outcome for iteration *n*.

    Args:
        ws_path: Resolved workspace directory path.
        n: Iteration number.
        review_status: One of 'blocked', 'changes_requested', 'approved'.

    Returns:
        ToolResult confirming the status update.
    """
    valid = [s.value for s in ReviewStatus]
    if review_status not in valid:
        return ToolResult.failure(
            "INVALID_STATUS",
            f"Invalid review status '{review_status}'. Must be one of: {valid}.",
        )

    review_json = _review_json(ws_path, n)
    guard = require_files(
        review_json,
        error_code="MISSING_REVIEW",
        message_template=f"iter-{n}-review.json not found ({{missing}}).",
    )
    if guard:
        return guard

    data, err = read_json(review_json)
    if err:
        return err
    assert data is not None

    # "findings" key must exist (even if empty list) to confirm the review was conducted
    if "findings" not in data and review_status == ReviewStatus.APPROVED.value:
        return ToolResult.failure(
            "NO_FINDINGS",
            "Cannot approve a review with no findings key. "
            "Run 'review update' first to record findings (can be an empty list).",
        )

    data["status"] = review_status
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    err = write_json(review_json, data)
    if err:
        return err

    return ToolResult.success(data=data)
