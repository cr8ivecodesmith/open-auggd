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


def test_install_exits_zero(project):
    result = auggd(["install"], cwd=project)
    assert result.returncode == 0, result.stderr


def test_install_creates_auggd_dir(project):
    auggd(["install"], cwd=project)
    assert (project / ".auggd").is_dir()


def test_install_creates_auggd_toml(project):
    auggd(["install"], cwd=project)
    assert (project / ".auggd" / "auggd.toml").exists()


def test_install_creates_install_manifest(project):
    auggd(["install"], cwd=project)
    assert (project / ".auggd" / "install-manifest.json").exists()


def test_install_manifest_contains_all_files(project):
    auggd(["install"], cwd=project)
    manifest = json.loads((project / ".auggd" / "install-manifest.json").read_text())
    assert len(manifest["files"]) == 37


def test_install_creates_opencode_agents(project):
    auggd(["install"], cwd=project)
    assert (project / ".opencode" / "agents" / "auggd.md").exists()


def test_install_creates_opencode_skills(project):
    auggd(["install"], cwd=project)
    assert (project / ".opencode" / "skills" / "oag-spec-standards" / "SKILL.md").exists()


def test_install_creates_opencode_tools(project):
    auggd(["install"], cwd=project)
    assert (project / ".opencode" / "tools" / "oag-ws.ts").exists()


def test_install_prints_success_message(project):
    result = auggd(["install"], cwd=project)
    assert "install" in result.stdout.lower()


def test_install_fails_if_already_installed(project):
    auggd(["install"], cwd=project)
    result = auggd(["install"], cwd=project)
    assert result.returncode != 0


def test_install_already_installed_error_mentions_reset(project):
    auggd(["install"], cwd=project)
    result = auggd(["install"], cwd=project)
    assert "reset" in result.stderr.lower()


# ---------------------------------------------------------------------------
# auggd uninstall
# ---------------------------------------------------------------------------


def test_uninstall_exits_zero_with_yes(project):
    auggd(["install"], cwd=project)
    result = auggd(["uninstall"], cwd=project, input="yes\n")
    assert result.returncode == 0, result.stderr


def test_uninstall_removes_auggd_dir(project):
    auggd(["install"], cwd=project)
    auggd(["uninstall"], cwd=project, input="yes\n")
    assert not (project / ".auggd").exists()


def test_uninstall_removes_managed_files(project):
    auggd(["install"], cwd=project)
    auggd(["uninstall"], cwd=project, input="yes\n")
    assert not (project / ".opencode" / "agents" / "auggd.md").exists()


def test_uninstall_preserves_preexisting_opencode_files(project):
    custom = project / ".opencode" / "agents" / "my-agent.md"
    custom.parent.mkdir(parents=True, exist_ok=True)
    custom.write_text("custom agent")

    auggd(["install"], cwd=project)
    auggd(["uninstall"], cwd=project, input="yes\n")

    assert custom.exists()
    assert custom.read_text() == "custom agent"


def test_uninstall_aborts_without_yes(project):
    auggd(["install"], cwd=project)
    agent_path = project / ".opencode" / "agents" / "auggd.md"

    result = auggd(["uninstall"], cwd=project, input="no\n")

    assert result.returncode != 0
    assert agent_path.exists()


def test_uninstall_fails_gracefully_when_not_installed(project):
    result = auggd(["uninstall"], cwd=project, input="yes\n")
    assert result.returncode != 0


# ---------------------------------------------------------------------------
# auggd update
# ---------------------------------------------------------------------------


def test_update_exits_zero(project):
    auggd(["install"], cwd=project)
    result = auggd(["update"], cwd=project)
    assert result.returncode == 0, result.stderr


def test_update_rewrites_model_line_from_toml(project):
    auggd(["install"], cwd=project)
    toml_path = project / ".auggd" / "auggd.toml"
    content = toml_path.read_text()
    content = content.replace('model = "opencode/gpt-5-nano"', 'model = "anthropic/claude-opus-4"')
    toml_path.write_text(content)

    auggd(["update"], cwd=project)

    agent_content = (project / ".opencode" / "agents" / "auggd.md").read_text()
    assert "model: anthropic/claude-opus-4" in agent_content


def test_update_does_not_change_name_frontmatter(project):
    auggd(["install"], cwd=project)
    toml_path = project / ".auggd" / "auggd.toml"
    content = toml_path.read_text().replace(
        'model = "opencode/gpt-5-nano"', 'model = "anthropic/claude-opus-4"'
    )
    toml_path.write_text(content)

    auggd(["update"], cwd=project)

    agent_content = (project / ".opencode" / "agents" / "auggd.md").read_text()
    assert "name: auggd" in agent_content


def test_update_fails_gracefully_when_not_installed(project):
    result = auggd(["update"], cwd=project)
    assert result.returncode != 0


# ---------------------------------------------------------------------------
# auggd reset
# ---------------------------------------------------------------------------


def test_reset_exits_zero_with_yes(project):
    auggd(["install"], cwd=project)
    result = auggd(["reset"], cwd=project, input="yes\n")
    assert result.returncode == 0, result.stderr


def test_reset_restores_modified_file(project):
    auggd(["install"], cwd=project)
    agent_path = project / ".opencode" / "agents" / "auggd.md"
    original = agent_path.read_text()
    agent_path.write_text("corrupted")

    auggd(["reset"], cwd=project, input="yes\n")

    assert agent_path.read_text() == original


def test_reset_does_not_touch_auggd_dir(project):
    auggd(["install"], cwd=project)
    toml_path = project / ".auggd" / "auggd.toml"
    toml_path.write_text("[workspace]\ndir = 'custom'\n")

    auggd(["reset"], cwd=project, input="yes\n")

    assert "custom" in toml_path.read_text()


def test_reset_aborts_without_yes(project):
    auggd(["install"], cwd=project)
    agent_path = project / ".opencode" / "agents" / "auggd.md"
    agent_path.write_text("corrupted")

    result = auggd(["reset"], cwd=project, input="no\n")

    assert result.returncode != 0
    assert agent_path.read_text() == "corrupted"


def test_reset_fails_gracefully_when_not_installed_without_prompting(project):
    """Not-installed error should surface without waiting for confirmation input."""
    result = auggd(["reset"], cwd=project, input="")
    assert result.returncode != 0
    assert "not installed" in result.stderr.lower()
