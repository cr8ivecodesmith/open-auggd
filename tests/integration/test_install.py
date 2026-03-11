"""Integration tests for the auggd install lifecycle CLI commands."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def auggd(args: list[str], cwd: Path, input: str | None = None) -> subprocess.CompletedProcess:
    """Invoke the auggd CLI and return the completed process."""
    return subprocess.run(
        [sys.executable, "-m", "open_auggd.cli.main"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        input=input,
    )


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    """Return a clean temp directory representing a fresh project."""
    return tmp_path


# ---------------------------------------------------------------------------
# auggd install
# ---------------------------------------------------------------------------


class TestInstallCommand:
    def test_exits_zero(self, project):
        result = auggd(["install"], cwd=project)
        assert result.returncode == 0, result.stderr

    def test_creates_auggd_dir(self, project):
        auggd(["install"], cwd=project)
        assert (project / ".auggd").is_dir()

    def test_creates_auggd_toml(self, project):
        auggd(["install"], cwd=project)
        assert (project / ".auggd" / "auggd.toml").exists()

    def test_creates_install_manifest(self, project):
        auggd(["install"], cwd=project)
        assert (project / ".auggd" / "install-manifest.json").exists()

    def test_manifest_contains_all_files(self, project):
        auggd(["install"], cwd=project)
        manifest = json.loads((project / ".auggd" / "install-manifest.json").read_text())
        assert len(manifest["files"]) == 37

    def test_creates_opencode_agents(self, project):
        auggd(["install"], cwd=project)
        assert (project / ".opencode" / "agents" / "auggd.md").exists()

    def test_creates_opencode_skills(self, project):
        auggd(["install"], cwd=project)
        assert (project / ".opencode" / "skills" / "oag-spec-standards" / "SKILL.md").exists()

    def test_creates_opencode_tools(self, project):
        auggd(["install"], cwd=project)
        assert (project / ".opencode" / "tools" / "oag-ws.ts").exists()

    def test_prints_success_message(self, project):
        result = auggd(["install"], cwd=project)
        assert "install" in result.stdout.lower()

    def test_fails_if_already_installed(self, project):
        auggd(["install"], cwd=project)
        result = auggd(["install"], cwd=project)
        assert result.returncode != 0

    def test_already_installed_error_mentions_reset(self, project):
        auggd(["install"], cwd=project)
        result = auggd(["install"], cwd=project)
        assert "reset" in result.stderr.lower()


# ---------------------------------------------------------------------------
# auggd uninstall
# ---------------------------------------------------------------------------


class TestUninstallCommand:
    def test_exits_zero_with_yes(self, project):
        auggd(["install"], cwd=project)
        result = auggd(["uninstall"], cwd=project, input="yes\n")
        assert result.returncode == 0, result.stderr

    def test_removes_auggd_dir(self, project):
        auggd(["install"], cwd=project)
        auggd(["uninstall"], cwd=project, input="yes\n")
        assert not (project / ".auggd").exists()

    def test_removes_managed_files(self, project):
        auggd(["install"], cwd=project)
        auggd(["uninstall"], cwd=project, input="yes\n")
        assert not (project / ".opencode" / "agents" / "auggd.md").exists()

    def test_preserves_preexisting_opencode_files(self, project):
        custom = project / ".opencode" / "agents" / "my-agent.md"
        custom.parent.mkdir(parents=True, exist_ok=True)
        custom.write_text("custom agent")

        auggd(["install"], cwd=project)
        auggd(["uninstall"], cwd=project, input="yes\n")

        assert custom.exists()
        assert custom.read_text() == "custom agent"

    def test_aborts_without_yes(self, project):
        auggd(["install"], cwd=project)
        agent_path = project / ".opencode" / "agents" / "auggd.md"

        result = auggd(["uninstall"], cwd=project, input="no\n")

        assert result.returncode != 0
        assert agent_path.exists()

    def test_fails_gracefully_when_not_installed(self, project):
        result = auggd(["uninstall"], cwd=project, input="yes\n")
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# auggd update
# ---------------------------------------------------------------------------


class TestUpdateCommand:
    def test_exits_zero(self, project):
        auggd(["install"], cwd=project)
        result = auggd(["update"], cwd=project)
        assert result.returncode == 0, result.stderr

    def test_rewrites_model_line_from_toml(self, project):
        auggd(["install"], cwd=project)
        # Write a custom model into auggd.toml
        toml_path = project / ".auggd" / "auggd.toml"
        content = toml_path.read_text()
        content = content.replace(
            'model = "opencode/gpt-5-nano"', 'model = "anthropic/claude-opus-4"'
        )
        toml_path.write_text(content)

        auggd(["update"], cwd=project)

        agent_content = (project / ".opencode" / "agents" / "auggd.md").read_text()
        assert "model: anthropic/claude-opus-4" in agent_content

    def test_does_not_change_name_frontmatter(self, project):
        auggd(["install"], cwd=project)
        toml_path = project / ".auggd" / "auggd.toml"
        content = toml_path.read_text().replace(
            'model = "opencode/gpt-5-nano"', 'model = "anthropic/claude-opus-4"'
        )
        toml_path.write_text(content)

        auggd(["update"], cwd=project)

        agent_content = (project / ".opencode" / "agents" / "auggd.md").read_text()
        assert "name: auggd" in agent_content

    def test_fails_gracefully_when_not_installed(self, project):
        result = auggd(["update"], cwd=project)
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# auggd reset
# ---------------------------------------------------------------------------


class TestResetCommand:
    def test_exits_zero_with_yes(self, project):
        auggd(["install"], cwd=project)
        result = auggd(["reset"], cwd=project, input="yes\n")
        assert result.returncode == 0, result.stderr

    def test_restores_modified_file(self, project):
        auggd(["install"], cwd=project)
        agent_path = project / ".opencode" / "agents" / "auggd.md"
        original = agent_path.read_text()
        agent_path.write_text("corrupted")

        auggd(["reset"], cwd=project, input="yes\n")

        assert agent_path.read_text() == original

    def test_does_not_touch_auggd_dir(self, project):
        auggd(["install"], cwd=project)
        toml_path = project / ".auggd" / "auggd.toml"
        toml_path.write_text("[workspace]\ndir = 'custom'\n")

        auggd(["reset"], cwd=project, input="yes\n")

        assert "custom" in toml_path.read_text()

    def test_aborts_without_yes(self, project):
        auggd(["install"], cwd=project)
        agent_path = project / ".opencode" / "agents" / "auggd.md"
        agent_path.write_text("corrupted")

        result = auggd(["reset"], cwd=project, input="no\n")

        assert result.returncode != 0
        assert agent_path.read_text() == "corrupted"

    def test_fails_gracefully_when_not_installed_without_prompting(self, project):
        """Not-installed error should surface without waiting for confirmation input."""
        result = auggd(["reset"], cwd=project, input="")
        assert result.returncode != 0
        assert "not installed" in result.stderr.lower()
