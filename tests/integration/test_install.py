"""Integration tests for auggd install/uninstall lifecycle."""

from __future__ import annotations

from pathlib import Path

import pytest

from open_auggd.config.settings import load_settings
from open_auggd.install.installer import install, is_installed, reset, uninstall


class TestInstallLifecycle:
    """End-to-end install → uninstall tests."""

    @pytest.fixture
    def project(self, tmp_path: Path) -> Path:
        """A bare project directory."""
        return tmp_path

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
        with pytest.raises(FileExistsError):
            install(settings)

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
