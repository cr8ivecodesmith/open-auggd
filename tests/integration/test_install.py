"""Integration tests for auggd install/uninstall lifecycle."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from open_auggd.config.settings import load_settings
from open_auggd.install.installer import (
    _iter_template_files,
    install,
    is_installed,
    reset,
    uninstall,
)


class TestInstallLifecycle:
    """End-to-end install → uninstall tests."""

    @pytest.fixture
    def project(self, tmp_path: Path) -> Path:
        """A bare project directory."""
        return tmp_path

    def test_templates_are_accessible(self):
        """Verify bundled templates are accessible (not lost in packaging)."""
        templates = _iter_template_files()
        assert len(templates) > 0, "No templates found - templates may be missing from wheel build"

        # Verify we have all expected template categories
        template_dests = [str(dest) for _, dest in templates]
        assert any("agents" in d for d in template_dests), "No agent templates found"
        assert any("commands" in d for d in template_dests), "No command templates found"
        assert any("skills" in d for d in template_dests), "No skill templates found"
        assert any("tools" in d for d in template_dests), "No tool templates found"

        # Verify each template file actually exists
        for src, _ in templates:
            assert src.exists(), f"Template source file missing: {src}"

    def test_install_creates_opencode_dirs(self, project: Path):
        settings = load_settings(project_root=project)
        install(settings)
        assert (project / ".opencode" / "agents").is_dir()
        assert (project / ".opencode" / "commands").is_dir()
        assert (project / ".opencode" / "skills").is_dir()
        assert (project / ".opencode" / "tools").is_dir()

    def test_install_creates_auggd_dir(self, project: Path):
        settings = load_settings(project_root=project)
        install(settings)
        assert (project / ".auggd").is_dir()
        assert (project / ".auggd" / "auggd.toml").exists()
        assert (project / ".auggd" / "install-manifest.json").exists()

    def test_install_writes_agent_files(self, project: Path):
        settings = load_settings(project_root=project)
        install(settings)
        expected_agents = [
            "oag-auggd.md",
            "oag-explorer.md",
            "oag-planner.md",
            "oag-developer.md",
            "oag-reviewer.md",
            "oag-finalizer.md",
            "oag-documenter.md",
        ]
        agents_dir = project / ".opencode" / "agents"
        for name in expected_agents:
            assert (agents_dir / name).exists(), f"Missing: {name}"

    def test_install_writes_command_files(self, project: Path):
        settings = load_settings(project_root=project)
        install(settings)
        expected_commands = [
            "oag-explore.md",
            "oag-plan.md",
            "oag-develop.md",
            "oag-review.md",
            "oag-finalize.md",
            "oag-document.md",
            "oag-status.md",
            "oag-resume.md",
        ]
        commands_dir = project / ".opencode" / "commands"
        for name in expected_commands:
            assert (commands_dir / name).exists(), f"Missing: {name}"

    def test_install_writes_tool_files(self, project: Path):
        settings = load_settings(project_root=project)
        install(settings)
        expected_tools = [
            "oag-explore.ts",
            "oag-plan.ts",
            "oag-develop.ts",
            "oag-review.ts",
            "oag-finalize.ts",
            "oag-document.ts",
        ]
        tools_dir = project / ".opencode" / "tools"
        for name in expected_tools:
            assert (tools_dir / name).exists(), f"Missing: {name}"

    def test_install_raises_if_already_installed(self, project: Path):
        settings = load_settings(project_root=project)
        install(settings)
        with pytest.raises(FileExistsError) as exc_info:
            install(settings)
        # Verify error message is informative
        assert "already exist" in str(exc_info.value)
        assert "--force" in str(exc_info.value)

    def test_install_force_overwrites(self, project: Path):
        settings = load_settings(project_root=project)
        install(settings)
        install(settings, force=True)  # Should not raise
        assert is_installed(settings)

    def test_is_installed_false_before_install(self, project: Path):
        settings = load_settings(project_root=project)
        assert not is_installed(settings)

    def test_is_installed_true_after_install(self, project: Path):
        settings = load_settings(project_root=project)
        install(settings)
        assert is_installed(settings)

    def test_uninstall_removes_opencode_files(self, project: Path):
        settings = load_settings(project_root=project)
        install(settings)
        uninstall(settings)
        # .opencode managed files should be gone
        assert not (project / ".opencode" / "agents" / "oag-auggd.md").exists()

    def test_uninstall_removes_auggd_dir(self, project: Path):
        settings = load_settings(project_root=project)
        install(settings)
        uninstall(settings)
        assert not (project / ".auggd").exists()

    def test_uninstall_does_not_remove_user_opencode_files(self, project: Path):
        settings = load_settings(project_root=project)
        # Create a user file in .opencode/ before install
        opencode_dir = project / ".opencode"
        opencode_dir.mkdir(parents=True)
        user_file = opencode_dir / "user-agent.md"
        user_file.write_text("# User file")

        install(settings)
        uninstall(settings)

        # User's file should survive
        assert user_file.exists()

    def test_reset_restores_files(self, project: Path):
        settings = load_settings(project_root=project)
        install(settings)

        # Corrupt an agent file
        agent_file = project / ".opencode" / "agents" / "oag-auggd.md"
        agent_file.write_text("# CORRUPTED")

        reset(settings)

        # Should be restored to bundled default content
        content = agent_file.read_text()
        assert "CORRUPTED" not in content

    def test_gitignore_updated(self, project: Path):
        settings = load_settings(project_root=project)
        install(settings)
        gitignore = project / ".gitignore"
        assert gitignore.exists()
        assert ".auggd/" in gitignore.read_text()

    def test_install_on_existing_opencode_dir_with_non_oag_files(self, project: Path):
        """Install should succeed when .opencode/ exists with only user files (no oag-* conflicts)."""
        settings = load_settings(project_root=project)
        # Create .opencode/ with a user-owned file (not prefixed oag-)
        opencode_dir = project / ".opencode"
        opencode_dir.mkdir(parents=True)
        user_file = opencode_dir / "user-agent.md"
        user_file.write_text("# User file")

        # Install should succeed
        install(settings)
        assert is_installed(settings)
        # User file should still exist
        assert user_file.exists()
        # Manifest should include all installed oag-* files
        assert (project / ".auggd" / "install-manifest.json").exists()

    def test_install_fails_with_full_conflict_list(self, project: Path):
        """Pre-existing oag-* files should cause error listing all conflicts."""
        settings = load_settings(project_root=project)
        # Create .opencode/ with some pre-existing oag-* files
        opencode_dir = project / ".opencode"
        agents_dir = opencode_dir / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "oag-auggd.md").write_text("# Old file 1")
        (agents_dir / "oag-explorer.md").write_text("# Old file 2")

        # Install should fail with all conflicts listed
        with pytest.raises(FileExistsError) as exc_info:
            install(settings)

        error_msg = str(exc_info.value)
        # Both conflicting files should be named in the error
        assert "oag-auggd.md" in error_msg or ".opencode/agents/oag-auggd.md" in error_msg
        assert "oag-explorer.md" in error_msg or ".opencode/agents/oag-explorer.md" in error_msg
        assert "--force" in error_msg

        # Verify no manifest was written (no partial install)
        assert not (project / ".auggd" / "install-manifest.json").exists()

    def test_install_force_on_existing_opencode_dir(self, project: Path):
        """--force should succeed even when oag-* files already exist."""
        settings = load_settings(project_root=project)
        # Create .opencode/ with pre-existing oag-* files
        opencode_dir = project / ".opencode"
        agents_dir = opencode_dir / "agents"
        agents_dir.mkdir(parents=True)
        old_file = agents_dir / "oag-auggd.md"
        old_file.write_text("# Old content")

        # Install with --force should succeed and update the file
        written = install(settings, force=True)
        assert is_installed(settings)
        # The file should be updated
        assert old_file.read_text() != "# Old content"
        # Manifest should include the file
        manifest_path = project / ".auggd" / "install-manifest.json"
        assert manifest_path.exists()
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert ".opencode/agents/oag-auggd.md" in manifest_data["files"]
        # written list should include all templates
        assert len(written) > 10  # Should include agents, commands, tools, skills
