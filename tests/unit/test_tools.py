"""Unit tests for the tools layer (explore, plan, develop, review, finalize, document)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from open_auggd.tools import explore as _explore
from open_auggd.tools import plan as _plan
from open_auggd.tools import develop as _develop
from open_auggd.tools import review as _review
from open_auggd.tools import finalize as _finalize
from open_auggd.workspace.models import (
    DevStatus,
    ExploreStatus,
    PlanStatus,
    ReviewStatus,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ws(tmp_path: Path) -> Path:
    """A blank workspace directory with all phase subdirectories."""
    for subdir in ["explore", "plan", "develop", "review", "tmp"]:
        (tmp_path / subdir).mkdir(parents=True)
    return tmp_path


@pytest.fixture
def ws_explored(ws: Path) -> Path:
    """A workspace with explore done."""
    result = _explore.start(ws)
    assert result.ok
    _set_json(ws / "explore" / "attachments.json", {"explore_status": "done"})
    return ws


@pytest.fixture
def ws_planned(ws_explored: Path) -> Path:
    """A workspace with explore done and plan started."""
    result = _plan.start(ws_explored)
    assert result.ok
    return ws_explored


@pytest.fixture
def ws_iter1_ready(ws_planned: Path) -> Path:
    """A workspace with one ready iteration plan."""
    _plan.iter_create(ws_planned)
    _set_json(
        ws_planned / "plan" / "iter-1-plan.json",
        {"n": 1, "status": "pending", "title": "Iter 1", "acceptance_criteria": ["AC1"]},
    )
    return ws_planned


@pytest.fixture
def ws_dev_complete(ws_iter1_ready: Path) -> Path:
    """A workspace with dev_complete on iter 1."""
    _develop.start(ws_iter1_ready, 1)
    _set_json(
        ws_iter1_ready / "develop" / "iter-1-devlog.json",
        {"n": 1, "status": "dev_complete"},
    )
    return ws_iter1_ready


@pytest.fixture
def ws_review_approved(ws_dev_complete: Path) -> Path:
    """A workspace with an approved review on iter 1."""
    _review.start(ws_dev_complete, 1)
    _set_json(
        ws_dev_complete / "review" / "iter-1-review.json",
        {"n": 1, "status": "approved", "findings": []},
    )
    return ws_dev_complete


def _set_json(path: Path, updates: dict) -> None:
    """Merge *updates* into an existing JSON file (or create it)."""
    if path.exists():
        data = json.loads(path.read_text())
        data.update(updates)
    else:
        data = updates
    path.write_text(json.dumps(data))


# ---------------------------------------------------------------------------
# Explore
# ---------------------------------------------------------------------------


class TestExploreTools:
    def test_start_creates_attachments(self, ws: Path):
        result = _explore.start(ws)
        assert result.ok
        assert (ws / "explore" / "attachments.json").exists()

    def test_start_idempotent(self, ws: Path):
        _explore.start(ws)
        result = _explore.start(ws)
        assert result.ok

    def test_status_before_start(self, ws: Path):
        result = _explore.status(ws)
        assert result.ok
        assert result.warnings  # warns about missing file

    def test_status_after_start(self, ws: Path):
        _explore.start(ws)
        result = _explore.status(ws)
        assert result.ok
        assert result.data["explore_status"] == ExploreStatus.IN_PROGRESS.value

    def test_done_requires_attachments(self, ws: Path):
        result = _explore.done(ws)
        assert not result.ok
        assert result.error == "MISSING_ATTACHMENTS"

    def test_done_sets_status(self, ws: Path):
        _explore.start(ws)
        result = _explore.done(ws)
        assert result.ok
        assert result.data["explore_status"] == ExploreStatus.DONE.value


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------


class TestPlanTools:
    def test_start_requires_explore_done(self, ws: Path):
        _explore.start(ws)
        # Explore is in_progress, not done
        result = _plan.start(ws)
        assert not result.ok
        assert result.error == "EXPLORE_NOT_DONE"

    def test_start_succeeds_after_explore_done(self, ws_explored: Path):
        result = _plan.start(ws_explored)
        assert result.ok
        assert (ws_explored / "plan" / "progress-log.json").exists()

    def test_iter_create(self, ws_planned: Path):
        result = _plan.iter_create(ws_planned)
        assert result.ok
        assert result.data["n"] == 1
        assert (ws_planned / "plan" / "iter-1-plan.json").exists()
        assert (ws_planned / "plan" / "iter-1-plan.md").exists()

    def test_iter_create_increments(self, ws_planned: Path):
        _plan.iter_create(ws_planned)
        result = _plan.iter_create(ws_planned)
        assert result.ok
        assert result.data["n"] == 2

    def test_iter_status(self, ws_planned: Path):
        _plan.iter_create(ws_planned)
        result = _plan.iter_status(ws_planned, 1)
        assert result.ok
        assert result.data["n"] == 1

    def test_iter_done_requires_ac(self, ws_planned: Path):
        _plan.iter_create(ws_planned)
        result = _plan.iter_done(ws_planned, 1)
        assert not result.ok
        assert result.error == "MISSING_AC"

    def test_iter_done_succeeds_with_ac(self, ws_iter1_ready: Path):
        result = _plan.iter_done(ws_iter1_ready, 1)
        assert result.ok
        assert result.data["status"] == PlanStatus.PENDING.value


# ---------------------------------------------------------------------------
# Develop
# ---------------------------------------------------------------------------


class TestDevelopTools:
    def test_start_requires_plan(self, ws: Path):
        result = _develop.start(ws, 1)
        assert not result.ok
        assert result.error == "MISSING_PLAN"

    def test_start_creates_devlog(self, ws_iter1_ready: Path):
        result = _develop.start(ws_iter1_ready, 1)
        assert result.ok
        assert (ws_iter1_ready / "develop" / "iter-1-devlog.json").exists()
        assert (ws_iter1_ready / "develop" / "iter-1-devlog.md").exists()

    def test_status_before_start(self, ws: Path):
        result = _develop.status(ws, 1)
        assert result.ok
        assert result.warnings

    def test_update_merges_files_touched(self, ws_iter1_ready: Path):
        _develop.start(ws_iter1_ready, 1)
        result = _develop.update(ws_iter1_ready, 1, {"files_touched": ["foo.py"]})
        assert result.ok
        assert "foo.py" in result.data["files_touched"]

    def test_update_appends_tests(self, ws_iter1_ready: Path):
        _develop.start(ws_iter1_ready, 1)
        _develop.update(ws_iter1_ready, 1, {"tests_run": [{"command": "pytest", "result": "pass"}]})
        result = _develop.update(
            ws_iter1_ready, 1, {"tests_run": [{"command": "mypy", "result": "pass"}]}
        )
        assert result.ok
        assert len(result.data["tests_run"]) == 2

    def test_done_sets_dev_complete(self, ws_iter1_ready: Path):
        _develop.start(ws_iter1_ready, 1)
        result = _develop.done(ws_iter1_ready, 1)
        assert result.ok
        assert result.data["status"] == DevStatus.DEV_COMPLETE.value


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------


class TestReviewTools:
    def test_start_requires_dev_complete(self, ws_iter1_ready: Path):
        _develop.start(ws_iter1_ready, 1)
        # Dev is in_progress, not dev_complete
        result = _review.start(ws_iter1_ready, 1)
        assert not result.ok
        assert result.error == "DEV_NOT_COMPLETE"

    def test_start_creates_review(self, ws_dev_complete: Path):
        result = _review.start(ws_dev_complete, 1)
        assert result.ok
        assert (ws_dev_complete / "review" / "iter-1-review.json").exists()

    def test_update_appends_findings(self, ws_dev_complete: Path):
        _review.start(ws_dev_complete, 1)
        finding = {
            "severity": "MUST-FIX",
            "file": "foo.py",
            "description": "Bad",
            "suggestion": "Fix",
        }
        result = _review.update(ws_dev_complete, 1, {"findings": [finding]})
        assert result.ok
        assert len(result.data["findings"]) == 1

    def test_done_approved(self, ws_dev_complete: Path):
        _review.start(ws_dev_complete, 1)
        _review.update(ws_dev_complete, 1, {"findings": []})
        result = _review.done(ws_dev_complete, 1, "approved")
        assert result.ok
        assert result.data["status"] == ReviewStatus.APPROVED.value

    def test_done_invalid_status(self, ws_dev_complete: Path):
        _review.start(ws_dev_complete, 1)
        result = _review.done(ws_dev_complete, 1, "garbage")
        assert not result.ok
        assert result.error == "INVALID_STATUS"


# ---------------------------------------------------------------------------
# Finalize
# ---------------------------------------------------------------------------


class TestFinalizeTools:
    def test_finalize_requires_approved_review(self, ws_dev_complete: Path):
        _review.start(ws_dev_complete, 1)
        # Review is blocked, not approved
        result = _finalize.iter_finalize(ws_dev_complete, 1)
        assert not result.ok
        assert result.error == "REVIEW_NOT_APPROVED"

    def test_finalize_succeeds(self, ws_review_approved: Path):
        result = _finalize.iter_finalize(ws_review_approved, 1)
        assert result.ok
        assert result.data["n"] == 1
        assert result.data["finalized_at"] is not None

    def test_finalize_updates_plan_status(self, ws_review_approved: Path):
        _finalize.iter_finalize(ws_review_approved, 1)
        plan_data = json.loads((ws_review_approved / "plan" / "iter-1-plan.json").read_text())
        assert plan_data["status"] == PlanStatus.FINALIZED.value

    def test_finalize_updates_progress_log(self, ws_review_approved: Path):
        _finalize.iter_finalize(ws_review_approved, 1)
        log_data = json.loads((ws_review_approved / "plan" / "progress-log.json").read_text())
        entry = next(e for e in log_data["iterations"] if e["n"] == 1)
        assert entry["finalized"] is True
