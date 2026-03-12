"""Unit tests for install/installer.py and install/updater.py."""

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

_installer_mod = importlib.import_module("open_auggd.install.installer")
Installer = _installer_mod.Installer
InstallError = _installer_mod.InstallError

_updater_mod = importlib.import_module("open_auggd.install.updater")
update_model_lines = _updater_mod.update_model_lines

_settings_mod = importlib.import_module("open_auggd.config.settings")
Settings = _settings_mod.Settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _installer(tmp_path: Path) -> Any:
    return Installer(tmp_path)


def _settings(
    default_model: str = "opencode/gpt-5-nano",
    agent_models: dict[str, str] | None = None,
    command_models: dict[str, str] | None = None,
) -> Any:
    return Settings(
        workspace_dir=".auggd/workspace",
        docs_dir="docs",
        default_model=default_model,
        agent_models=agent_models or {},
        command_models=command_models or {},
    )


def _manifest(tmp_path: Path) -> dict[str, Any]:
    p = tmp_path / ".auggd" / "install-manifest.json"
    return json.loads(p.read_text())  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Installer.install()
# ---------------------------------------------------------------------------


def test_install_creates_auggd_dir(tmp_path):
    _installer(tmp_path).install()
    assert (tmp_path / ".auggd").is_dir()


def test_install_creates_auggd_toml(tmp_path):
    _installer(tmp_path).install()
    assert (tmp_path / ".auggd" / "auggd.toml").exists()


def test_install_auggd_toml_has_required_sections(tmp_path):
    _installer(tmp_path).install()
    content = (tmp_path / ".auggd" / "auggd.toml").read_text()
    assert "[workspace]" in content
    assert "[docs]" in content
    assert "[defaults]" in content


def test_install_creates_opencode_agents_dir(tmp_path):
    _installer(tmp_path).install()
    assert (tmp_path / ".opencode" / "agents").is_dir()


def test_install_creates_opencode_commands_dir(tmp_path):
    _installer(tmp_path).install()
    assert (tmp_path / ".opencode" / "commands").is_dir()


def test_install_creates_opencode_skills_dir(tmp_path):
    _installer(tmp_path).install()
    assert (tmp_path / ".opencode" / "skills").is_dir()


def test_install_creates_opencode_tools_dir(tmp_path):
    _installer(tmp_path).install()
    assert (tmp_path / ".opencode" / "tools").is_dir()


def test_install_copies_all_agent_files(tmp_path):
    _installer(tmp_path).install()
    agents_dir = tmp_path / ".opencode" / "agents"
    names = {f.name for f in agents_dir.iterdir()}
    assert "auggd.md" in names
    assert "oag-explorer.md" in names
    assert "oag-planner.md" in names
    assert "oag-developer.md" in names
    assert "oag-reviewer.md" in names
    assert "oag-finalizer.md" in names
    assert "oag-documenter.md" in names


def test_install_copies_all_command_files(tmp_path):
    _installer(tmp_path).install()
    commands_dir = tmp_path / ".opencode" / "commands"
    names = {f.name for f in commands_dir.iterdir()}
    expected = {
        "oag-explore.md",
        "oag-plan.md",
        "oag-develop.md",
        "oag-review.md",
        "oag-finalize.md",
        "oag-document.md",
        "oag-status.md",
        "oag-resume.md",
    }
    assert expected.issubset(names)


def test_install_copies_all_skill_dirs(tmp_path):
    _installer(tmp_path).install()
    skills_dir = tmp_path / ".opencode" / "skills"
    skill_names = {d.name for d in skills_dir.iterdir() if d.is_dir()}
    assert "oag-spec-standards" in skill_names
    assert "oag-dev-standards" in skill_names
    assert "oag-exploration-model" in skill_names
    assert "oag-exploration-tactics" in skill_names


def test_install_skill_dirs_contain_skill_md(tmp_path):
    _installer(tmp_path).install()
    skills_dir = tmp_path / ".opencode" / "skills"
    for skill_dir in skills_dir.iterdir():
        assert (skill_dir / "SKILL.md").exists(), f"Missing SKILL.md in {skill_dir.name}"


def test_install_copies_all_tool_files(tmp_path):
    _installer(tmp_path).install()
    tools_dir = tmp_path / ".opencode" / "tools"
    names = {f.name for f in tools_dir.iterdir()}
    expected = {
        "oag-explore.ts",
        "oag-plan.ts",
        "oag-develop.ts",
        "oag-review.ts",
        "oag-finalize.ts",
        "oag-document.ts",
        "oag-files.ts",
        "oag-ws.ts",
    }
    assert expected.issubset(names)


def test_install_writes_install_manifest(tmp_path):
    _installer(tmp_path).install()
    manifest = _manifest(tmp_path)
    assert "installed_at" in manifest
    assert "files" in manifest
    assert isinstance(manifest["files"], list)


def test_install_manifest_records_all_written_paths(tmp_path):
    _installer(tmp_path).install()
    manifest = _manifest(tmp_path)
    files = set(manifest["files"])
    assert ".opencode/agents/auggd.md" in files
    assert ".opencode/commands/oag-explore.md" in files
    assert ".opencode/skills/oag-spec-standards/SKILL.md" in files
    assert ".opencode/tools/oag-ws.ts" in files


def test_install_manifest_has_37_files(tmp_path):
    """7 agents + 8 commands + 14 skills + 8 tools = 37 files."""
    _installer(tmp_path).install()
    manifest = _manifest(tmp_path)
    assert len(manifest["files"]) == 37


def test_install_raises_if_already_installed(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    with pytest.raises(InstallError, match="already installed"):
        inst.install()


def test_install_already_installed_error_mentions_reset(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    with pytest.raises(InstallError, match="reset"):
        inst.install()


# ---------------------------------------------------------------------------
# Installer.uninstall()
# ---------------------------------------------------------------------------


def test_uninstall_removes_auggd_dir(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    inst.uninstall(confirmed=True)
    assert not (tmp_path / ".auggd").exists()


def test_uninstall_removes_managed_opencode_files(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    inst.uninstall(confirmed=True)
    assert not (tmp_path / ".opencode" / "agents" / "auggd.md").exists()


def test_uninstall_leaves_preexisting_opencode_files(tmp_path):
    opencode_dir = tmp_path / ".opencode" / "agents"
    opencode_dir.mkdir(parents=True)
    preexisting = opencode_dir / "my-custom-agent.md"
    preexisting.write_text("custom content")

    inst = _installer(tmp_path)
    inst.install()
    inst.uninstall(confirmed=True)

    assert preexisting.exists()
    assert preexisting.read_text() == "custom content"


def test_uninstall_leaves_core_opencode_subdirs_intact(tmp_path):
    """Uninstall leaves the four core .opencode/ subdirs in place."""
    inst = _installer(tmp_path)
    inst.install()
    inst.uninstall(confirmed=True)

    assert (tmp_path / ".opencode" / "agents").is_dir()
    assert (tmp_path / ".opencode" / "commands").is_dir()
    assert (tmp_path / ".opencode" / "skills").is_dir()
    assert (tmp_path / ".opencode" / "tools").is_dir()


def test_uninstall_removes_empty_skill_subdirs(tmp_path):
    """Per-skill subdirs created by auggd are removed when empty after uninstall."""
    inst = _installer(tmp_path)
    inst.install()
    inst.uninstall(confirmed=True)

    skills_dir = tmp_path / ".opencode" / "skills"
    assert not any(skills_dir.iterdir())


def test_uninstall_leaves_skill_subdir_with_user_content(tmp_path):
    """A per-skill subdir that has extra user files is not removed."""
    inst = _installer(tmp_path)
    inst.install()
    user_file = tmp_path / ".opencode" / "skills" / "oag-spec-standards" / "notes.md"
    user_file.write_text("my notes")

    inst.uninstall(confirmed=True)

    assert user_file.exists()


def test_uninstall_without_confirmation_raises(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    with pytest.raises(InstallError, match="confirmed"):
        inst.uninstall(confirmed=False)


def test_uninstall_without_confirmation_does_not_remove_files(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    try:
        inst.uninstall(confirmed=False)
    except InstallError:
        pass
    assert (tmp_path / ".opencode" / "agents" / "auggd.md").exists()


def test_uninstall_without_manifest_raises(tmp_path):
    with pytest.raises(InstallError, match="not installed"):
        _installer(tmp_path).uninstall(confirmed=True)


# ---------------------------------------------------------------------------
# Installer.reset()
# ---------------------------------------------------------------------------


def test_reset_restores_file_to_bundled_content(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    agent_path = tmp_path / ".opencode" / "agents" / "auggd.md"
    original = agent_path.read_text()
    agent_path.write_text("corrupted content")

    inst.reset(confirmed=True)

    assert agent_path.read_text() == original


def test_reset_does_not_touch_auggd_dir(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    toml_path = tmp_path / ".auggd" / "auggd.toml"
    toml_path.write_text("[workspace]\ndir = 'custom'\n")

    inst.reset(confirmed=True)

    assert "custom" in toml_path.read_text()


def test_reset_without_confirmation_raises(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    with pytest.raises(InstallError, match="confirmed"):
        inst.reset(confirmed=False)


def test_reset_without_confirmation_does_not_change_files(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    agent_path = tmp_path / ".opencode" / "agents" / "auggd.md"
    agent_path.write_text("modified")

    try:
        inst.reset(confirmed=False)
    except InstallError:
        pass

    assert agent_path.read_text() == "modified"


def test_reset_without_install_raises_before_confirmation(tmp_path):
    """Not-installed check must fire even when confirmed=True."""
    with pytest.raises(InstallError, match="not installed"):
        _installer(tmp_path).reset(confirmed=True)


def test_reset_not_installed_raises_even_when_unconfirmed(tmp_path):
    """Not-installed is caught before the confirmation check."""
    with pytest.raises(InstallError, match="not installed"):
        _installer(tmp_path).reset(confirmed=False)


# ---------------------------------------------------------------------------
# update_model_lines()
# ---------------------------------------------------------------------------


def test_update_rewrites_model_line_in_agent_file(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    s = _settings(default_model="anthropic/claude-opus-4")
    update_model_lines(tmp_path, s)

    content = (tmp_path / ".opencode" / "agents" / "auggd.md").read_text()
    assert "model: anthropic/claude-opus-4" in content


def test_update_rewrites_model_line_in_command_file(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    s = _settings(default_model="anthropic/claude-opus-4")
    update_model_lines(tmp_path, s)

    content = (tmp_path / ".opencode" / "commands" / "oag-explore.md").read_text()
    assert "model: anthropic/claude-opus-4" in content


def test_update_does_not_change_other_frontmatter_fields(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    agent_path = tmp_path / ".opencode" / "agents" / "auggd.md"
    original_name_line = [
        line for line in agent_path.read_text().splitlines() if line.startswith("name:")
    ][0]

    s = _settings(default_model="anthropic/claude-opus-4")
    update_model_lines(tmp_path, s)

    content = agent_path.read_text()
    assert original_name_line in content


def test_update_uses_per_agent_model_when_configured(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    s = _settings(
        default_model="opencode/gpt-5-nano",
        agent_models={"developer": "anthropic/claude-sonnet-4-6"},
    )
    update_model_lines(tmp_path, s)

    developer_content = (tmp_path / ".opencode" / "agents" / "oag-developer.md").read_text()
    auggd_content = (tmp_path / ".opencode" / "agents" / "auggd.md").read_text()

    assert "model: anthropic/claude-sonnet-4-6" in developer_content
    assert "model: opencode/gpt-5-nano" in auggd_content


def test_update_uses_per_command_model_when_configured(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    s = _settings(
        default_model="opencode/gpt-5-nano",
        command_models={"develop": "anthropic/claude-sonnet-4-6"},
    )
    update_model_lines(tmp_path, s)

    develop_content = (tmp_path / ".opencode" / "commands" / "oag-develop.md").read_text()
    explore_content = (tmp_path / ".opencode" / "commands" / "oag-explore.md").read_text()

    assert "model: anthropic/claude-sonnet-4-6" in develop_content
    assert "model: opencode/gpt-5-nano" in explore_content


def test_update_does_not_modify_skill_files(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    skill_path = tmp_path / ".opencode" / "skills" / "oag-spec-standards" / "SKILL.md"
    original = skill_path.read_text()

    s = _settings(default_model="anthropic/claude-opus-4")
    update_model_lines(tmp_path, s)

    assert skill_path.read_text() == original


def test_update_does_not_modify_tool_files(tmp_path):
    inst = _installer(tmp_path)
    inst.install()
    tool_path = tmp_path / ".opencode" / "tools" / "oag-ws.ts"
    original = tool_path.read_text()

    s = _settings(default_model="anthropic/claude-opus-4")
    update_model_lines(tmp_path, s)

    assert tool_path.read_text() == original


def test_update_without_install_raises(tmp_path):
    s = _settings()
    with pytest.raises(InstallError, match="not installed"):
        update_model_lines(tmp_path, s)
