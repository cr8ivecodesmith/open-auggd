"""Tools for the finalize phase.

Actions:
  iter <N> — mark iteration finalized; updates progress-log; optionally commits.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from open_auggd.tools.base import ToolResult, read_json, require_files, write_json
from open_auggd.workspace.models import PlanStatus, ProgressLog, ProgressLogEntry, ReviewStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _plan_json(ws_path: Path, n: int) -> Path:
    return ws_path / "plan" / f"iter-{n}-plan.json"


def _review_json(ws_path: Path, n: int) -> Path:
    return ws_path / "review" / f"iter-{n}-review.json"


def _progress_log_file(ws_path: Path) -> Path:
    return ws_path / "plan" / "progress-log.json"


def _load_progress_log(ws_path: Path) -> tuple[ProgressLog, list[str]]:
    """Load progress-log.json, deriving from iter files if absent."""
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
    """Build a ProgressLog by scanning iter-N-plan.json files."""
    plan_dir = ws_path / "plan"
    entries: list[ProgressLogEntry] = []
    if plan_dir.exists():
        for f in sorted(plan_dir.glob("iter-*-plan.json")):
            data, _ = read_json(f)
            if data:
                entries.append(ProgressLogEntry.from_dict(data))
    return ProgressLog(workspace_id=ws_path.name, iterations=entries)


def _mark_plan_finalized(ws_path: Path, n: int) -> None:
    """Set iter-N-plan.json status to finalized if the file exists."""
    plan_json = _plan_json(ws_path, n)
    if not plan_json.exists():
        return
    pl_data, err = read_json(plan_json)
    if not err and pl_data is not None:
        pl_data["status"] = PlanStatus.FINALIZED.value
        pl_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        write_json(plan_json, pl_data)


def _update_progress_log(ws_path: Path, n: int, finalized_at: str) -> list[str]:
    """Mark iteration *n* as finalized in progress-log.json.

    Returns any warning strings generated while loading the log.
    """
    log, warnings = _load_progress_log(ws_path)
    updated = False
    for entry in log.iterations:
        if entry.n == n:
            entry.plan_status = PlanStatus.FINALIZED.value
            entry.finalized = True
            entry.finalized_at = finalized_at
            updated = True
            break
    if not updated:
        log.iterations.append(
            ProgressLogEntry(
                n=n,
                plan_status=PlanStatus.FINALIZED.value,
                finalized=True,
                finalized_at=finalized_at,
            )
        )
    log.updated_at = datetime.now(timezone.utc)
    write_json(_progress_log_file(ws_path), log.to_dict())
    return warnings


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


def iter_finalize(ws_path: Path, n: int, commit: bool = False) -> ToolResult:
    """Finalize iteration *n*.

    Prerequisite: review must be approved.

    Marks plan status as finalized, updates progress-log, and optionally
    creates a git commit.

    Args:
        ws_path: Resolved workspace directory path.
        n: Iteration number.
        commit: If True, run ``git add -A && git commit`` with an auto message.

    Returns:
        ToolResult with finalized iteration data.
    """
    review_json = _review_json(ws_path, n)
    guard = require_files(
        review_json,
        error_code="MISSING_REVIEW",
        message_template=f"iter-{n}-review.json not found ({{missing}}). Complete review first.",
    )
    if guard:
        return guard

    rv_data, err = read_json(review_json)
    if err:
        return err
    assert rv_data is not None

    if rv_data.get("status") != ReviewStatus.APPROVED.value:
        return ToolResult.failure(
            "REVIEW_NOT_APPROVED",
            f"iter-{n}-review.json status is '{rv_data.get('status')}'. "
            "Must be 'approved' before finalizing.",
        )

    finalized_at = datetime.now(timezone.utc).isoformat()
    _mark_plan_finalized(ws_path, n)
    warnings = _update_progress_log(ws_path, n, finalized_at)

    commit_sha: str | None = None
    if commit:
        commit_result = _git_commit(n, ws_path)
        if commit_result.get("ok"):
            commit_sha = commit_result.get("sha")
        else:
            warnings.append(f"Git commit failed: {commit_result.get('error')}")

    return ToolResult.success(
        data={"n": n, "finalized_at": finalized_at, "commit_sha": commit_sha},
        warnings=warnings,
    )


def _git_commit(n: int, ws_path: Path) -> dict:
    """Attempt a git add + commit for the finalized iteration."""
    msg = f"chore(auggd): finalize iteration {n} [{ws_path.name[:20]}]"
    try:
        subprocess.run(["git", "add", "-A"], check=True, capture_output=True)
        result = subprocess.run(
            ["git", "commit", "-m", msg],
            check=True,
            capture_output=True,
            text=True,
        )
        # Extract SHA from commit output
        sha_line = result.stdout.splitlines()[0] if result.stdout else ""
        return {"ok": True, "sha": sha_line}
    except subprocess.CalledProcessError as e:
        return {"ok": False, "error": e.stderr or str(e)}
