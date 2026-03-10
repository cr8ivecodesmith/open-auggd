"""Tools for the develop phase.

Actions:
  start <N>         — verify plan ready, create devlog files, set in_progress
  update <N> --data — merge JSON fields into devlog
  status <N>        — read iter-N-devlog.json
  done <N>          — set dev_complete
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from open_auggd.tools.base import ToolResult, read_json, require_files, write_json
from open_auggd.workspace.models import DevStatus, IterDevlog, PlanStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _devlog_json(ws_path: Path, n: int) -> Path:
    return ws_path / "develop" / f"iter-{n}-devlog.json"


def _devlog_md(ws_path: Path, n: int) -> Path:
    return ws_path / "develop" / f"iter-{n}-devlog.md"


def _plan_json(ws_path: Path, n: int) -> Path:
    return ws_path / "plan" / f"iter-{n}-plan.json"


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


def start(ws_path: Path, n: int) -> ToolResult:
    """Start development of iteration *n*.

    Prerequisite: iter-N-plan.json must exist.

    Args:
        ws_path: Resolved workspace directory path.
        n: Iteration number.

    Returns:
        ToolResult with devlog file paths.
    """
    plan_json = _plan_json(ws_path, n)
    guard = require_files(
        plan_json,
        error_code="MISSING_PLAN",
        message_template=f"iter-{n}-plan.json not found ({{missing}}). Create the plan first.",
    )
    if guard:
        return guard

    # Check plan is in a ready state (pending or in_progress are both OK for dev start)
    data, err = read_json(plan_json)
    if err:
        return err
    assert data is not None
    plan_status = data.get("status")
    ready_statuses = [PlanStatus.PENDING.value, PlanStatus.IN_PROGRESS.value]
    if plan_status not in ready_statuses:
        return ToolResult.failure(
            "PLAN_NOT_READY",
            f"iter-{n}-plan.json status is '{plan_status}'. "
            "Mark the plan done first with 'plan iter done <N>'.",
        )

    # Create develop directory
    develop_dir = ws_path / "develop"
    develop_dir.mkdir(parents=True, exist_ok=True)

    devlog_json = _devlog_json(ws_path, n)
    devlog_md = _devlog_md(ws_path, n)

    devlog = IterDevlog(n=n, status=DevStatus.IN_PROGRESS)
    err = write_json(devlog_json, devlog.to_dict())
    if err:
        return err

    devlog_md.write_text(
        f"# Iteration {n} Devlog\n\n<!-- Agent: document development progress here -->\n",
        encoding="utf-8",
    )

    return ToolResult.success(
        data={"n": n, "devlog_json": str(devlog_json), "devlog_md": str(devlog_md)}
    )


def update(ws_path: Path, n: int, patch: dict) -> ToolResult:
    """Merge *patch* fields into the devlog for iteration *n*.

    Args:
        ws_path: Resolved workspace directory path.
        n: Iteration number.
        patch: Dict of fields to merge (must match IterDevlog schema keys).

    Returns:
        ToolResult with updated devlog data.
    """
    devlog_json = _devlog_json(ws_path, n)
    guard = require_files(
        devlog_json,
        error_code="MISSING_DEVLOG",
        message_template=f"iter-{n}-devlog.json not found ({{missing}}). Run 'develop start {n}' first.",
    )
    if guard:
        return guard

    data, err = read_json(devlog_json)
    if err:
        return err
    assert data is not None

    # Merge: for list fields, extend; for scalars, replace
    list_fields = {"files_touched", "tests_run", "blockers"}
    for key, value in patch.items():
        if key in list_fields and isinstance(value, list):
            existing = data.get(key, [])
            data[key] = existing + value
        elif key not in ("n", "status", "updated_at"):
            data[key] = value

    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    err = write_json(devlog_json, data)
    if err:
        return err

    return ToolResult.success(data=data)


def status(ws_path: Path, n: int) -> ToolResult:
    """Return the devlog status for iteration *n*.

    Args:
        ws_path: Resolved workspace directory path.
        n: Iteration number.

    Returns:
        ToolResult with devlog data or a warning if absent.
    """
    devlog_json = _devlog_json(ws_path, n)
    if not devlog_json.exists():
        return ToolResult.success(
            data={"status": None},
            warnings=[f"iter-{n}-devlog.json does not exist."],
        )
    data, err = read_json(devlog_json)
    if err:
        return err
    return ToolResult.success(data=data or {})


def done(ws_path: Path, n: int) -> ToolResult:
    """Mark iteration *n* development as complete.

    Args:
        ws_path: Resolved workspace directory path.
        n: Iteration number.

    Returns:
        ToolResult confirming the status update.
    """
    devlog_json = _devlog_json(ws_path, n)
    guard = require_files(
        devlog_json,
        error_code="MISSING_DEVLOG",
        message_template=f"iter-{n}-devlog.json not found ({{missing}}).",
    )
    if guard:
        return guard

    data, err = read_json(devlog_json)
    if err:
        return err
    assert data is not None

    data["status"] = DevStatus.DEV_COMPLETE.value
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    err = write_json(devlog_json, data)
    if err:
        return err

    return ToolResult.success(data=data)
