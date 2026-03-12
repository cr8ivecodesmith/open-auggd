"""Unit tests for workspace/manager.py."""

import importlib
import json
from pathlib import Path

import pytest

_mod = importlib.import_module("open_auggd.workspace.manager")
WorkspaceManager = _mod.WorkspaceManager
WorkspaceError = _mod.WorkspaceError

_models_mod = importlib.import_module("open_auggd.workspace.models")
Phase = _models_mod.Phase
WorkspaceListItem = _models_mod.WorkspaceListItem


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def ws_dir(tmp_path: Path) -> Path:
    """Return an empty workspace root directory."""
    d = tmp_path / "workspace"
    d.mkdir()
    return d


@pytest.fixture()
def manager(ws_dir: Path):  # type: ignore[return]
    """Return a WorkspaceManager pointing at a fresh workspace root."""
    return WorkspaceManager(ws_dir)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


def test_create_returns_metadata_with_correct_slug(manager):
    meta = manager.create("add-user-auth")
    assert meta.slug == "add-user-auth"


def test_create_slugifies_input(manager):
    meta = manager.create("Add User Auth")
    assert meta.slug == "add-user-auth"


def test_create_assigns_non_empty_id(manager):
    meta = manager.create("my-feature")
    assert meta.id
    assert len(meta.id) > 8


def test_create_makes_workspace_dir(manager, ws_dir):
    meta = manager.create("my-feature")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    assert ws_path.is_dir()


def test_create_writes_workspace_metadata_json(manager, ws_dir):
    meta = manager.create("my-feature")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    assert (ws_path / "workspace-metadata.json").exists()


def test_create_writes_iteration_log_json(manager, ws_dir):
    meta = manager.create("my-feature")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    assert (ws_path / "iteration-log.json").exists()


def test_create_writes_files_manifest_json(manager, ws_dir):
    meta = manager.create("my-feature")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    assert (ws_path / "files-manifest.json").exists()


def test_create_makes_attachments_dir(manager, ws_dir):
    meta = manager.create("my-feature")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    assert (ws_path / "attachments").is_dir()


def test_create_makes_tmp_dir(manager, ws_dir):
    meta = manager.create("my-feature")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    assert (ws_path / "tmp").is_dir()


def test_create_iteration_log_is_empty_dict(manager, ws_dir):
    meta = manager.create("my-feature")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    data = json.loads((ws_path / "iteration-log.json").read_text())
    assert data == {}


def test_create_files_manifest_is_empty_dict(manager, ws_dir):
    meta = manager.create("my-feature")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    data = json.loads((ws_path / "files-manifest.json").read_text())
    assert data == {}


def test_create_initial_phase_is_explore(manager):
    meta = manager.create("my-feature")
    assert meta.current_phase is Phase.EXPLORE


def test_create_initial_iteration_is_zero(manager):
    meta = manager.create("my-feature")
    assert meta.current_iteration == 0


def test_create_metadata_json_round_trips(manager, ws_dir):
    meta = manager.create("my-feature")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    data = json.loads((ws_path / "workspace-metadata.json").read_text())
    assert data["id"] == meta.id
    assert data["slug"] == meta.slug
    assert data["current_phase"] == "explore"


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


def test_list_empty_when_no_workspaces(manager):
    assert manager.list() == []


def test_list_returns_workspace_list_items(manager):
    manager.create("feature-one")
    result = manager.list()
    assert isinstance(result[0], WorkspaceListItem)


def test_list_returns_created_workspace(manager):
    manager.create("feature-one")
    result = manager.list()
    assert len(result) == 1
    assert result[0].metadata.slug == "feature-one"


def test_list_returns_multiple_workspaces(manager):
    manager.create("alpha")
    manager.create("beta")
    result = manager.list()
    assert len(result) == 2
    slugs = {item.metadata.slug for item in result}
    assert slugs == {"alpha", "beta"}


def test_list_sorted_lexicographically_by_dir_name(manager):
    # UUID7 is time-ordered so lexicographic sort == creation order.
    manager.create("first")
    manager.create("second")
    result = manager.list()
    assert result[0].metadata.slug == "first"
    assert result[1].metadata.slug == "second"


def test_list_title_empty_when_no_spec(manager):
    manager.create("my-ws")
    result = manager.list()
    assert result[0].title == ""


def test_list_title_from_spec_md(manager, ws_dir):
    meta = manager.create("my-ws")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    (ws_path / "spec.md").write_text("---\ntitle: My Great Feature\nstatus: draft\n---\n\n# Body\n")
    result = manager.list()
    assert result[0].title == "My Great Feature"


def test_list_started_false_when_iteration_log_empty(manager):
    manager.create("my-ws")
    result = manager.list()
    assert result[0].started is False


def test_list_started_true_when_iteration_log_has_entries(manager, ws_dir):
    meta = manager.create("my-ws")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    (ws_path / "iteration-log.json").write_text(
        json.dumps({"0": {"explore": {"status": "in-progress"}}})
    )
    result = manager.list()
    assert result[0].started is True


def test_list_interrupted_false_when_no_interruption(manager):
    manager.create("my-ws")
    result = manager.list()
    assert result[0].interrupted is False


def test_list_interrupted_true_when_current_iteration_has_interrupted_phase(manager, ws_dir):
    meta = manager.create("my-ws")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    # Write iteration-log with current_iteration=0, explore status=interrupted.
    (ws_path / "iteration-log.json").write_text(
        json.dumps({"0": {"explore": {"status": "interrupted"}}})
    )
    result = manager.list()
    assert result[0].interrupted is True


def test_list_interrupted_false_when_other_iteration_interrupted(manager, ws_dir):
    meta = manager.create("my-ws")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    # current_iteration=0 in metadata, but interruption is in iteration 1.
    (ws_path / "iteration-log.json").write_text(
        json.dumps({"1": {"develop": {"status": "interrupted"}}})
    )
    result = manager.list()
    assert result[0].interrupted is False


# ---------------------------------------------------------------------------
# resolve
# ---------------------------------------------------------------------------


def test_resolve_by_index_one_based(manager):
    manager.create("only-one")
    path = manager.resolve("1")
    assert "only-one" in path.name


def test_resolve_by_slug(manager):
    manager.create("my-feature")
    path = manager.resolve("my-feature")
    assert "my-feature" in path.name


def test_resolve_nonexistent_index_raises(manager):
    manager.create("only-one")
    with pytest.raises(WorkspaceError, match="not found"):
        manager.resolve("99")


def test_resolve_nonexistent_slug_raises(manager):
    with pytest.raises(WorkspaceError, match="not found"):
        manager.resolve("no-such-slug")


def test_resolve_index_zero_raises(manager):
    manager.create("one")
    with pytest.raises(WorkspaceError, match="not found"):
        manager.resolve("0")


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete_removes_workspace_dir(manager, ws_dir):
    meta = manager.create("to-delete")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    manager.delete("1")
    assert not ws_path.exists()


def test_delete_by_slug(manager, ws_dir):
    meta = manager.create("to-delete")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    manager.delete("to-delete")
    assert not ws_path.exists()


def test_delete_nonexistent_raises(manager):
    with pytest.raises(WorkspaceError, match="not found"):
        manager.delete("ghost")


def test_delete_does_not_affect_other_workspaces(manager, ws_dir):
    manager.create("keep-me")
    manager.create("delete-me")
    manager.delete("2")
    remaining = manager.list()
    assert len(remaining) == 1
    assert remaining[0].metadata.slug == "keep-me"


# ---------------------------------------------------------------------------
# info
# ---------------------------------------------------------------------------


def test_info_returns_ws_info_output(manager):
    manager.create("my-ws")
    out = manager.info("1")
    assert out.slug == "my-ws"


def test_info_id_matches_metadata(manager):
    meta = manager.create("my-ws")
    out = manager.info("1")
    assert out.id == meta.id


def test_info_empty_iteration_log_gives_empty_list(manager):
    manager.create("my-ws")
    out = manager.info("1")
    assert out.last_n_iterations == []


def test_info_spec_path_null_when_no_spec(manager):
    manager.create("my-ws")
    out = manager.info("1")
    assert out.spec_path is None


def test_info_attachments_empty_when_no_files(manager):
    manager.create("my-ws")
    out = manager.info("1")
    assert out.attachments == []


def test_info_attachments_lists_md_files(manager, ws_dir):
    meta = manager.create("my-ws")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    (ws_path / "attachments" / "topic.md").write_text("# Topic")
    out = manager.info("1")
    assert len(out.attachments) == 1
    assert out.attachments[0].endswith("topic.md")


def test_info_spec_path_set_when_spec_exists(manager, ws_dir):
    meta = manager.create("my-ws")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    (ws_path / "spec.md").write_text("# Spec")
    out = manager.info("1")
    assert out.spec_path is not None
    assert out.spec_path.endswith("spec.md")


def test_info_last_n_default_is_three(manager, ws_dir):
    """--last defaults to 3; with an empty log we still get empty list."""
    manager.create("my-ws")
    out = manager.info("1")
    assert out.last_n_iterations == []


def test_info_workspace_path_is_string(manager):
    manager.create("my-ws")
    out = manager.info("1")
    assert isinstance(out.workspace_path, str)


def test_info_to_dict_is_json_serialisable(manager):
    manager.create("my-ws")
    out = manager.info("1")
    d = out.to_dict()
    import json as _json

    serialised = _json.dumps(d)
    assert "my-ws" in serialised


def test_info_title_empty_when_no_spec(manager):
    manager.create("my-ws")
    out = manager.info("1")
    assert out.title == ""


def test_info_title_from_spec_md(manager, ws_dir):
    meta = manager.create("my-ws")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    (ws_path / "spec.md").write_text("---\ntitle: My Great Feature\nstatus: draft\n---\n\n# Body\n")
    out = manager.info("1")
    assert out.title == "My Great Feature"


def test_info_title_ignores_body_title_line(manager, ws_dir):
    meta = manager.create("my-ws")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    # title in frontmatter only — body heading should not bleed in
    (ws_path / "spec.md").write_text("---\ntitle: Frontmatter Title\n---\n\n# Body Heading\n")
    out = manager.info("1")
    assert out.title == "Frontmatter Title"


def test_info_title_empty_when_frontmatter_has_no_title_key(manager, ws_dir):
    meta = manager.create("my-ws")
    ws_path = ws_dir / f"{meta.id}-{meta.slug}"
    (ws_path / "spec.md").write_text("---\nstatus: draft\n---\n\n# Body\n")
    out = manager.info("1")
    assert out.title == ""
