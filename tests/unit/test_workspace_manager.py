"""Unit tests for WorkspaceManager."""

from __future__ import annotations

from pathlib import Path

import pytest

from open_auggd.workspace.manager import WorkspaceManager, _slug_from_id


class TestWorkspaceManager:
    """Tests for WorkspaceManager CRUD operations."""

    @pytest.fixture
    def mgr(self, tmp_path: Path) -> WorkspaceManager:
        return WorkspaceManager(tmp_path / "workspace")

    def test_create_returns_workspace_info(self, mgr: WorkspaceManager):
        ws = mgr.create("add user authentication")
        assert ws.slug == "add-user-authentication"
        assert ws.path.exists()
        assert ws.path.is_dir()

    def test_create_makes_phase_dirs(self, mgr: WorkspaceManager):
        ws = mgr.create("fix bug")
        for subdir in ["explore", "plan", "develop", "review", "tmp"]:
            assert (ws.path / subdir).is_dir()

    def test_list_empty(self, mgr: WorkspaceManager):
        assert mgr.list_workspaces() == []

    def test_list_sorted_by_creation(self, mgr: WorkspaceManager):
        ws1 = mgr.create("first task")
        ws2 = mgr.create("second task")
        ws3 = mgr.create("third task")
        listed = mgr.list_workspaces()
        assert len(listed) == 3
        slugs = [w.slug for w in listed]
        assert slugs == ["first-task", "second-task", "third-task"]

    def test_resolve_by_number(self, mgr: WorkspaceManager):
        ws = mgr.create("my task")
        resolved = mgr.resolve("1")
        assert resolved is not None
        assert resolved.id == ws.id

    def test_resolve_by_slug_substring(self, mgr: WorkspaceManager):
        ws = mgr.create("fix authentication bug")
        resolved = mgr.resolve("auth")
        assert resolved is not None
        assert resolved.id == ws.id

    def test_resolve_ambiguous_raises(self, mgr: WorkspaceManager):
        mgr.create("fix auth bug")
        mgr.create("fix authorization issue")
        with pytest.raises(ValueError, match="ambiguous"):
            mgr.resolve("auth")

    def test_resolve_out_of_range_raises(self, mgr: WorkspaceManager):
        mgr.create("task")
        with pytest.raises(ValueError, match="out of range"):
            mgr.resolve("5")

    def test_resolve_not_found_returns_none(self, mgr: WorkspaceManager):
        mgr.create("task")
        result = mgr.resolve("nonexistent-xyz")
        assert result is None

    def test_delete_removes_directory(self, mgr: WorkspaceManager):
        ws = mgr.create("task to delete")
        ws_path = ws.path
        assert ws_path.exists()
        mgr.delete("1")
        assert not ws_path.exists()

    def test_delete_nonexistent_raises(self, mgr: WorkspaceManager):
        with pytest.raises(ValueError):
            mgr.delete("nonexistent")

    def test_list_reindexes_after_delete(self, mgr: WorkspaceManager):
        mgr.create("first")
        mgr.create("second")
        mgr.create("third")
        mgr.delete("2")  # delete "second"
        listed = mgr.list_workspaces()
        assert len(listed) == 2
        # After delete, "1" is now "first", "2" is "third"
        r1 = mgr.resolve("1")
        r2 = mgr.resolve("2")
        assert r1 is not None and r1.slug == "first"
        assert r2 is not None and r2.slug == "third"

    def test_info_returns_dict(self, mgr: WorkspaceManager):
        mgr.create("auth feature")
        info = mgr.info("1")
        assert info["slug"] == "auth-feature"
        assert info["phase"] == "new"
        assert info["planned"] == 0

    def test_iter_count_zero_initially(self, mgr: WorkspaceManager):
        ws = mgr.create("task")
        assert ws.planned_count == 0
        assert ws.dev_count == 0
        assert ws.reviewed_count == 0

    def test_next_iter_n_starts_at_1(self, mgr: WorkspaceManager):
        ws = mgr.create("task")
        assert ws.next_iter_n() == 1

    def test_slug_from_id(self):
        ws_id = "BpsAOM-QceKAADMlOfK5Qg-add-user-auth"
        # 22 chars uuid + '-' = 23 chars prefix
        assert _slug_from_id(ws_id) == "add-user-auth"
