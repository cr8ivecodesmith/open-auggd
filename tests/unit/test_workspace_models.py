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
# WorkspaceMetadata — slim identity-only schema
# ---------------------------------------------------------------------------


def test_workspace_metadata_slim_fields():
    now = datetime.now(timezone.utc)
    m = WorkspaceMetadata(
        id="AZXyo7HEfomfPS0bTF1uf",
        slug="add-user-auth",
        created_at=now,
        updated_at=now,
    )
    assert m.id == "AZXyo7HEfomfPS0bTF1uf"
    assert m.slug == "add-user-auth"
    assert m.created_at == now
    assert m.updated_at == now


def test_workspace_metadata_to_dict_slim():
    now = datetime.now(timezone.utc)
    m = WorkspaceMetadata(
        id="testid123",
        slug="my-slug",
        created_at=now,
        updated_at=now,
    )
    d = m.to_dict()
    assert d["id"] == "testid123"
    assert d["slug"] == "my-slug"
    assert "created_at" in d
    assert "updated_at" in d
    # Removed fields must not be present
    assert "current_phase" not in d
    assert "current_iteration" not in d
    assert "title" not in d
    assert "description" not in d
    assert "scope" not in d
    assert "non_goals" not in d


def test_workspace_metadata_to_dict_has_exactly_four_keys():
    now = datetime.now(timezone.utc)
    m = WorkspaceMetadata(id="x", slug="s", created_at=now, updated_at=now)
    assert set(m.to_dict().keys()) == {"id", "slug", "created_at", "updated_at"}


def test_workspace_metadata_from_dict_slim():
    now = datetime.now(timezone.utc)
    m = WorkspaceMetadata(id="testid123", slug="my-slug", created_at=now, updated_at=now)
    restored = WorkspaceMetadata.from_dict(m.to_dict())
    assert restored.id == m.id
    assert restored.slug == m.slug


def test_workspace_metadata_timestamps_are_iso_strings_in_dict():
    now = datetime.now(timezone.utc)
    m = WorkspaceMetadata(id="x", slug="s", created_at=now, updated_at=now)
    d = m.to_dict()
    assert isinstance(d["created_at"], str)
    assert "T" in d["created_at"]  # ISO 8601 format


# ---------------------------------------------------------------------------
# WorkspaceListItem — log-derived fields
# ---------------------------------------------------------------------------


def test_workspace_list_item_not_started():
    now = datetime.now(timezone.utc)
    meta = WorkspaceMetadata(id="x", slug="my-ws", created_at=now, updated_at=now)
    item = WorkspaceListItem(metadata=meta, title="", phase=None, iteration=None, interrupted=None)
    assert item.phase is None
    assert item.iteration is None
    assert item.interrupted is None


def test_workspace_list_item_in_progress():
    now = datetime.now(timezone.utc)
    meta = WorkspaceMetadata(id="x", slug="my-ws", created_at=now, updated_at=now)
    item = WorkspaceListItem(
        metadata=meta, title="My Feature", phase="explore", iteration=0, interrupted=False
    )
    assert item.phase == "explore"
    assert item.iteration == 0
    assert item.interrupted is False
    assert item.title == "My Feature"


def test_workspace_list_item_interrupted():
    now = datetime.now(timezone.utc)
    meta = WorkspaceMetadata(id="x", slug="my-ws", created_at=now, updated_at=now)
    item = WorkspaceListItem(
        metadata=meta, title="", phase="develop", iteration=1, interrupted=True
    )
    assert item.interrupted is True


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
