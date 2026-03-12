"""Unit tests for workspace/models.py."""

import importlib
from datetime import datetime, timezone

_mod = importlib.import_module("open_auggd.workspace.models")
Phase = _mod.Phase
WorkspaceMetadata = _mod.WorkspaceMetadata
WorkspaceListItem = _mod.WorkspaceListItem
WsInfoIteration = _mod.WsInfoIteration
WsInfoOutput = _mod.WsInfoOutput


# ---------------------------------------------------------------------------
# Phase enum
# ---------------------------------------------------------------------------


def test_phase_values():
    assert Phase.EXPLORE.value == "explore"
    assert Phase.PLAN.value == "plan"
    assert Phase.DEVELOP.value == "develop"
    assert Phase.REVIEW.value == "review"
    assert Phase.FINALIZE.value == "finalize"
    assert Phase.DONE.value == "done"


def test_phase_from_string():
    assert Phase("explore") is Phase.EXPLORE
    assert Phase("done") is Phase.DONE


# ---------------------------------------------------------------------------
# WorkspaceMetadata
# ---------------------------------------------------------------------------


def test_workspace_metadata_fields():
    now = datetime.now(timezone.utc)
    m = WorkspaceMetadata(
        id="AZXyo7HEfomfPS0bTF1uf",
        slug="add-user-auth",
        created_at=now,
        updated_at=now,
        current_phase=Phase.EXPLORE,
        current_iteration=0,
        title="",
        description="",
        scope=[],
        non_goals=[],
    )
    assert m.id == "AZXyo7HEfomfPS0bTF1uf"
    assert m.slug == "add-user-auth"
    assert m.current_phase is Phase.EXPLORE
    assert m.current_iteration == 0


def test_workspace_metadata_to_dict_round_trip():
    now = datetime.now(timezone.utc)
    m = WorkspaceMetadata(
        id="testid123",
        slug="my-slug",
        created_at=now,
        updated_at=now,
        current_phase=Phase.DEVELOP,
        current_iteration=1,
        title="My title",
        description="desc",
        scope=["a", "b"],
        non_goals=["c"],
    )
    d = m.to_dict()
    assert d["id"] == "testid123"
    assert d["slug"] == "my-slug"
    assert d["current_phase"] == "develop"
    assert d["current_iteration"] == 1
    assert d["title"] == "My title"
    assert d["scope"] == ["a", "b"]
    assert d["non_goals"] == ["c"]


def test_workspace_metadata_from_dict_round_trip():
    now = datetime.now(timezone.utc)
    m = WorkspaceMetadata(
        id="testid123",
        slug="my-slug",
        created_at=now,
        updated_at=now,
        current_phase=Phase.PLAN,
        current_iteration=2,
        title="T",
        description="D",
        scope=[],
        non_goals=[],
    )
    restored = WorkspaceMetadata.from_dict(m.to_dict())
    assert restored.id == m.id
    assert restored.slug == m.slug
    assert restored.current_phase is Phase.PLAN
    assert restored.current_iteration == 2


def test_workspace_metadata_timestamps_are_iso_strings_in_dict():
    now = datetime.now(timezone.utc)
    m = WorkspaceMetadata(
        id="x",
        slug="s",
        created_at=now,
        updated_at=now,
        current_phase=Phase.EXPLORE,
        current_iteration=0,
        title="",
        description="",
        scope=[],
        non_goals=[],
    )
    d = m.to_dict()
    assert isinstance(d["created_at"], str)
    assert "T" in d["created_at"]  # ISO 8601 format


# ---------------------------------------------------------------------------
# WorkspaceListItem
# ---------------------------------------------------------------------------


def test_workspace_list_item_fields():
    now = datetime.now(timezone.utc)
    meta = WorkspaceMetadata(
        id="x",
        slug="my-ws",
        created_at=now,
        updated_at=now,
        current_phase=Phase.DEVELOP,
        current_iteration=1,
        title="",
        description="",
        scope=[],
        non_goals=[],
    )
    item = WorkspaceListItem(metadata=meta, title="My Feature", interrupted=False, started=True)
    assert item.metadata is meta
    assert item.title == "My Feature"
    assert item.interrupted is False
    assert item.started is True


def test_workspace_list_item_interrupted_true():
    now = datetime.now(timezone.utc)
    meta = WorkspaceMetadata(
        id="x",
        slug="my-ws",
        created_at=now,
        updated_at=now,
        current_phase=Phase.DEVELOP,
        current_iteration=1,
        title="",
        description="",
        scope=[],
        non_goals=[],
    )
    item = WorkspaceListItem(metadata=meta, title="", interrupted=True, started=True)
    assert item.interrupted is True


def test_workspace_list_item_started_false():
    now = datetime.now(timezone.utc)
    meta = WorkspaceMetadata(
        id="x",
        slug="my-ws",
        created_at=now,
        updated_at=now,
        current_phase=Phase.EXPLORE,
        current_iteration=0,
        title="",
        description="",
        scope=[],
        non_goals=[],
    )
    item = WorkspaceListItem(metadata=meta, title="", interrupted=False, started=False)
    assert item.started is False


# ---------------------------------------------------------------------------
# WsInfoOutput
# ---------------------------------------------------------------------------


def test_ws_info_output_fields():
    out = WsInfoOutput(
        id="abc",
        slug="my-ws",
        title="",
        last_n_iterations=[],
        spec_path=None,
        attachments=[],
        workspace_path="/path/to/ws",
    )
    assert out.id == "abc"
    assert out.slug == "my-ws"
    assert out.spec_path is None
    assert out.attachments == []


def test_ws_info_output_to_dict_null_spec_path():
    out = WsInfoOutput(
        id="abc",
        slug="my-ws",
        title="",
        last_n_iterations=[],
        spec_path=None,
        attachments=[],
        workspace_path="/ws",
    )
    d = out.to_dict()
    assert d["spec_path"] is None
    assert d["attachments"] == []
    assert "current_phase" not in d


def test_ws_info_output_to_dict_with_spec_path():
    out = WsInfoOutput(
        id="abc",
        slug="my-ws",
        title="",
        last_n_iterations=[],
        spec_path="/ws/spec.md",
        attachments=["/ws/attachments/topic.md"],
        workspace_path="/ws",
    )
    d = out.to_dict()
    assert d["spec_path"] == "/ws/spec.md"
    assert d["attachments"] == ["/ws/attachments/topic.md"]
