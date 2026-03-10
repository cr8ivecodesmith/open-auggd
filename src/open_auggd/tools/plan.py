"""Tools for the plan phase.

Actions:
  start            — verify explore done, create plan/ subdirs and progress-log.json
  iter create      — create next iter-N-plan.{md,json}, update progress-log
  iter status <N>  — read iter-N-plan.json
  iter done <N>    — set status to pending (ready for dev) if AC non-empty
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from open_auggd.tools.base import ToolResult, read_json, require_files, write_json
from open_auggd.workspace.models import (
    ExploreStatus,
    IterPlan,
    PlanStatus,
    ProgressLog,
    ProgressLogEntry,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _plan_file(ws_path: Path, n: int) -> Path:
    return ws_path / "plan" / f"iter-{n}-plan.json"


def _plan_md(ws_path: Path, n: int) -> Path:
    return ws_path / "plan" / f"iter-{n}-plan.md"


def _progress_log_file(ws_path: Path) -> Path:
    return ws_path / "plan" / "progress-log.json"


def _next_n(ws_path: Path) -> int:
    """Return next iteration number (globally monotonic across plan/dev/review)."""
    existing = []
    for pattern, subdir in [
        ("iter-*-plan.json", "plan"),
        ("iter-*-devlog.json", "develop"),
        ("iter-*-review.json", "review"),
    ]:
        d = ws_path / subdir
        if d.exists():
            for f in d.glob(pattern):
                try:
                    existing.append(int(f.name.split("-")[1]))
                except (IndexError, ValueError):
                    pass
    return (max(existing) + 1) if existing else 1


def _load_progress_log(ws_path: Path) -> tuple[ProgressLog, list[str]]:
    """Load progress-log.json, deriving from iter files if absent/stale."""
    pf = _progress_log_file(ws_path)
    warnings: list[str] = []
    if not pf.exists():
        warnings.append("plan/progress-log.json absent — deriving from iter files.")
        return _derive_progress_log(ws_path), warnings
    data, err = read_json(pf)
    if err or data is None:
        warnings.append("plan/progress-log.json unreadable — deriving from iter files.")
        return _derive_progress_log(ws_path), warnings
    return ProgressLog.from_dict(data), warnings


def _derive_progress_log(ws_path: Path) -> ProgressLog:
    """Build a ProgressLog from individual iter-N-plan.json files."""
    plan_dir = ws_path / "plan"
    entries: list[ProgressLogEntry] = []
    if plan_dir.exists():
        for f in sorted(plan_dir.glob("iter-*-plan.json")):
            data, _ = read_json(f)
            if data:
                entries.append(ProgressLogEntry.from_dict(data))
    return ProgressLog(workspace_id=ws_path.name, iterations=entries)


def _save_progress_log(ws_path: Path, log: ProgressLog) -> None:
    log.updated_at = datetime.now(timezone.utc)
    write_json(_progress_log_file(ws_path), log.to_dict())


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


def start(ws_path: Path) -> ToolResult:
    """Start the plan phase.

    Prerequisite: explore phase must be done.

    Args:
        ws_path: Resolved workspace directory path.

    Returns:
        ToolResult confirming plan phase is open.
    """
    attachments_file = ws_path / "explore" / "attachments.json"
    guard = require_files(
        attachments_file,
        error_code="EXPLORE_NOT_DONE",
        message_template=(
            "explore/attachments.json not found ({missing}). Complete explore phase first."
        ),
    )
    if guard:
        return guard

    # Check explore is done
    data, err = read_json(attachments_file)
    if err:
        return err
    assert data is not None
    status = data.get("explore_status")
    if status != ExploreStatus.DONE.value:
        return ToolResult.failure(
            "EXPLORE_NOT_DONE",
            f"Explore phase status is '{status}', must be 'done' before planning.",
        )

    # Create plan directory
    plan_dir = ws_path / "plan"
    plan_dir.mkdir(parents=True, exist_ok=True)

    # Initialize progress log if absent
    pf = _progress_log_file(ws_path)
    if not pf.exists():
        log = ProgressLog(workspace_id=ws_path.name)
        _save_progress_log(ws_path, log)

    return ToolResult.success(data={"message": "Plan phase started.", "workspace": ws_path.name})


def iter_create(ws_path: Path) -> ToolResult:
    """Create the next iteration plan files.

    Args:
        ws_path: Resolved workspace directory path.

    Returns:
        ToolResult with the new iteration number and file paths.
    """
    plan_dir = ws_path / "plan"
    if not plan_dir.exists():
        return ToolResult.failure(
            "PLAN_NOT_STARTED",
            "Plan phase not started. Run 'plan start' first.",
        )

    n = _next_n(ws_path)
    plan_json = _plan_file(ws_path, n)
    plan_md = _plan_md(ws_path, n)

    # Write JSON skeleton
    iter_plan = IterPlan(n=n)
    err = write_json(plan_json, iter_plan.to_dict())
    if err:
        return err

    # Write markdown placeholder
    plan_md.write_text(
        f"# Iteration {n} Plan\n\n<!-- Agent: fill in the iteration plan narrative here -->\n",
        encoding="utf-8",
    )

    # Update progress log
    log, warnings = _load_progress_log(ws_path)
    log.iterations.append(ProgressLogEntry(n=n, plan_status=PlanStatus.PENDING.value))
    _save_progress_log(ws_path, log)

    return ToolResult.success(
        data={"n": n, "plan_json": str(plan_json), "plan_md": str(plan_md)},
        warnings=warnings,
    )


def iter_status(ws_path: Path, n: int) -> ToolResult:
    """Return the status of iteration *n*.

    Args:
        ws_path: Resolved workspace directory path.
        n: Iteration number.

    Returns:
        ToolResult with iter-N-plan.json contents.
    """
    plan_json = _plan_file(ws_path, n)
    guard = require_files(
        plan_json,
        error_code="MISSING_PLAN",
        message_template=f"iter-{n}-plan.json not found ({{missing}}).",
    )
    if guard:
        return guard
    data, err = read_json(plan_json)
    if err:
        return err
    return ToolResult.success(data=data or {})


def iter_done(ws_path: Path, n: int) -> ToolResult:
    """Mark iteration *n* ready for development.

    Prerequisite: acceptance_criteria must be non-empty.

    Args:
        ws_path: Resolved workspace directory path.
        n: Iteration number.

    Returns:
        ToolResult confirming the status update.
    """
    plan_json = _plan_file(ws_path, n)
    guard = require_files(
        plan_json,
        error_code="MISSING_PLAN",
        message_template=f"iter-{n}-plan.json not found ({{missing}}).",
    )
    if guard:
        return guard

    data, err = read_json(plan_json)
    if err:
        return err
    assert data is not None

    if not data.get("acceptance_criteria"):
        return ToolResult.failure(
            "MISSING_AC",
            f"iter-{n}-plan.json has no acceptance_criteria. Add at least one before marking done.",
        )

    data["status"] = PlanStatus.PENDING.value
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    err = write_json(plan_json, data)
    if err:
        return err

    # Update progress log
    log, warnings = _load_progress_log(ws_path)
    for entry in log.iterations:
        if entry.n == n:
            entry.plan_status = PlanStatus.PENDING.value
            break
    _save_progress_log(ws_path, log)

    return ToolResult.success(data=data, warnings=warnings)
