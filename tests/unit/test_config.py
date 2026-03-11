"""Unit tests for config/settings.py."""

from pathlib import Path

import pytest

from open_auggd.config.settings import Settings, load_settings


@pytest.fixture()
def tmp_project(tmp_path):
    """Return a tmp dir with no auggd.toml (bare project)."""
    return tmp_path


@pytest.fixture()
def project_with_toml(tmp_path):
    """Return a tmp dir with a minimal .auggd/auggd.toml."""
    auggd_dir = tmp_path / ".auggd"
    auggd_dir.mkdir()
    (auggd_dir / "auggd.toml").write_text(
        "[workspace]\n"
        'dir = ".auggd/workspace"\n'
        "\n"
        "[docs]\n"
        'dir = "docs"\n'
        "\n"
        "[defaults]\n"
        'model = "anthropic/claude-opus-4"\n'
        "\n"
        "[agents.models]\n"
        'developer = "anthropic/claude-sonnet-4-6"\n'
        "\n"
        "[commands.models]\n"
        'develop = "anthropic/claude-sonnet-4-6"\n'
    )
    return tmp_path


# --- defaults when no TOML ---


class TestDefaultSettings:
    def test_default_model(self, tmp_project):
        s = load_settings(tmp_project)
        assert s.default_model == "opencode/gpt-5-nano"

    def test_default_workspace_dir(self, tmp_project):
        s = load_settings(tmp_project)
        assert s.workspace_dir == ".auggd/workspace"

    def test_default_docs_dir(self, tmp_project):
        s = load_settings(tmp_project)
        assert s.docs_dir == "docs"

    def test_empty_agent_models(self, tmp_project):
        s = load_settings(tmp_project)
        assert s.agent_models == {}

    def test_empty_command_models(self, tmp_project):
        s = load_settings(tmp_project)
        assert s.command_models == {}


# --- TOML values override defaults ---


class TestTomlSettings:
    def test_model_from_toml(self, project_with_toml):
        s = load_settings(project_with_toml)
        assert s.default_model == "anthropic/claude-opus-4"

    def test_workspace_dir_from_toml(self, project_with_toml):
        s = load_settings(project_with_toml)
        assert s.workspace_dir == ".auggd/workspace"

    def test_docs_dir_from_toml(self, project_with_toml):
        s = load_settings(project_with_toml)
        assert s.docs_dir == "docs"

    def test_agent_models_from_toml(self, project_with_toml):
        s = load_settings(project_with_toml)
        assert s.agent_models["developer"] == "anthropic/claude-sonnet-4-6"

    def test_command_models_from_toml(self, project_with_toml):
        s = load_settings(project_with_toml)
        assert s.command_models["develop"] == "anthropic/claude-sonnet-4-6"


# --- env vars override TOML ---


class TestEnvOverrides:
    def test_oag_default_model_overrides_toml(self, project_with_toml, monkeypatch):
        monkeypatch.setenv("OAG_DEFAULT_MODEL", "openai/gpt-4o")
        s = load_settings(project_with_toml)
        assert s.default_model == "openai/gpt-4o"

    def test_oag_default_model_overrides_defaults(self, tmp_project, monkeypatch):
        monkeypatch.setenv("OAG_DEFAULT_MODEL", "openai/gpt-4o")
        s = load_settings(tmp_project)
        assert s.default_model == "openai/gpt-4o"

    def test_oag_agent_model_env(self, tmp_project, monkeypatch):
        monkeypatch.setenv("OAG_DEVELOPER_MODEL", "openai/gpt-4o")
        s = load_settings(tmp_project)
        assert s.agent_models["developer"] == "openai/gpt-4o"

    def test_oag_agent_model_env_overrides_toml(self, project_with_toml, monkeypatch):
        monkeypatch.setenv("OAG_DEVELOPER_MODEL", "openai/gpt-4o")
        s = load_settings(project_with_toml)
        assert s.agent_models["developer"] == "openai/gpt-4o"

    def test_oag_command_model_env(self, tmp_project, monkeypatch):
        monkeypatch.setenv("OAG_DEVELOP_MODEL", "openai/gpt-4o")
        s = load_settings(tmp_project)
        assert s.command_models["develop"] == "openai/gpt-4o"

    def test_oag_workspace_dir_env(self, tmp_project, monkeypatch):
        monkeypatch.setenv("OAG_WORKSPACE_DIR", "/tmp/custom-ws")
        s = load_settings(tmp_project)
        assert s.workspace_dir == "/tmp/custom-ws"

    def test_oag_docs_dir_env(self, tmp_project, monkeypatch):
        monkeypatch.setenv("OAG_DOCS_DIR", "/tmp/custom-docs")
        s = load_settings(tmp_project)
        assert s.docs_dir == "/tmp/custom-docs"


# --- path expansion ---


class TestPathExpansion:
    def test_tilde_expansion_workspace(self, tmp_path, monkeypatch):
        auggd_dir = tmp_path / ".auggd"
        auggd_dir.mkdir()
        (auggd_dir / "auggd.toml").write_text("[workspace]\ndir = '~/myworkspace'\n")
        s = load_settings(tmp_path)
        assert "~" not in s.workspace_dir
        assert s.workspace_dir.startswith(str(Path.home()))

    def test_env_var_expansion_workspace(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MY_WS", "/tmp/expanded-ws")
        auggd_dir = tmp_path / ".auggd"
        auggd_dir.mkdir()
        (auggd_dir / "auggd.toml").write_text("[workspace]\ndir = '$MY_WS'\n")
        s = load_settings(tmp_path)
        assert s.workspace_dir == "/tmp/expanded-ws"


# --- Settings dataclass ---


class TestSettingsDataclass:
    def test_settings_is_dataclass(self):
        s = Settings(
            workspace_dir=".auggd/workspace",
            docs_dir="docs",
            default_model="opencode/gpt-5-nano",
            agent_models={},
            command_models={},
        )
        assert s.default_model == "opencode/gpt-5-nano"

    def test_effective_model_for_agent_uses_specific(self):
        s = Settings(
            workspace_dir=".auggd/workspace",
            docs_dir="docs",
            default_model="opencode/gpt-5-nano",
            agent_models={"developer": "anthropic/claude-sonnet-4-6"},
            command_models={},
        )
        assert s.effective_agent_model("developer") == "anthropic/claude-sonnet-4-6"

    def test_effective_model_for_agent_falls_back_to_default(self):
        s = Settings(
            workspace_dir=".auggd/workspace",
            docs_dir="docs",
            default_model="opencode/gpt-5-nano",
            agent_models={},
            command_models={},
        )
        assert s.effective_agent_model("explorer") == "opencode/gpt-5-nano"

    def test_effective_model_for_command_uses_specific(self):
        s = Settings(
            workspace_dir=".auggd/workspace",
            docs_dir="docs",
            default_model="opencode/gpt-5-nano",
            agent_models={},
            command_models={"develop": "anthropic/claude-sonnet-4-6"},
        )
        assert s.effective_command_model("develop") == "anthropic/claude-sonnet-4-6"

    def test_effective_model_for_command_falls_back_to_default(self):
        s = Settings(
            workspace_dir=".auggd/workspace",
            docs_dir="docs",
            default_model="opencode/gpt-5-nano",
            agent_models={},
            command_models={},
        )
        assert s.effective_command_model("explore") == "opencode/gpt-5-nano"
