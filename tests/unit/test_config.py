"""Unit tests for config loading."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from open_auggd.config.settings import Settings, generate_toml, load_settings


class TestLoadSettings:
    """Tests for load_settings()."""

    def test_defaults_no_config_file(self, tmp_path: Path):
        settings = load_settings(project_root=tmp_path)
        assert settings.project_root == tmp_path
        assert settings.workspace_dir == tmp_path / ".auggd" / "workspace"
        assert settings.docs_dir == tmp_path / "docs"
        assert settings.default_model == "opencode/gpt-5-nano"

    def test_cli_overrides(self, tmp_path: Path):
        ws = tmp_path / "custom-ws"
        settings = load_settings(
            project_root=tmp_path,
            workspace_dir=ws,
            default_model="anthropic/claude-opus-4",
        )
        assert settings.workspace_dir == ws
        assert settings.default_model == "anthropic/claude-opus-4"

    def test_env_override_workspace(self, tmp_path: Path, monkeypatch):
        custom_ws = str(tmp_path / "env-ws")
        monkeypatch.setenv("OAG_WORKSPACE_DIR", custom_ws)
        settings = load_settings(project_root=tmp_path)
        assert settings.workspace_dir == Path(custom_ws)

    def test_env_override_model(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("OAG_DEFAULT_MODEL", "openai/gpt-4o")
        settings = load_settings(project_root=tmp_path)
        assert settings.default_model == "openai/gpt-4o"

    def test_env_agent_model(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("OAG_EXPLORER_MODEL", "anthropic/claude-haiku-4-5")
        settings = load_settings(project_root=tmp_path)
        assert settings.agent_models.explorer == "anthropic/claude-haiku-4-5"
        assert settings.model_for_agent("explorer") == "anthropic/claude-haiku-4-5"

    def test_model_for_agent_fallback(self, tmp_path: Path):
        settings = load_settings(project_root=tmp_path)
        assert settings.model_for_agent("explorer") == settings.default_model

    def test_toml_config(self, tmp_path: Path):
        auggd_dir = tmp_path / ".auggd"
        auggd_dir.mkdir()
        toml_content = """
[workspace]
dir = "/tmp/myworkspace"

[models]
default = "anthropic/claude-sonnet-4"
"""
        (auggd_dir / "auggd.toml").write_text(toml_content)
        settings = load_settings(project_root=tmp_path)
        assert settings.workspace_dir == Path("/tmp/myworkspace")
        assert settings.default_model == "anthropic/claude-sonnet-4"

    def test_tilde_expansion(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("OAG_WORKSPACE_DIR", "~/auggd-ws")
        settings = load_settings(project_root=tmp_path)
        assert not str(settings.workspace_dir).startswith("~")


class TestSettings:
    """Tests for the Settings dataclass."""

    def test_auggd_dir(self, tmp_path: Path):
        settings = load_settings(project_root=tmp_path)
        assert settings.auggd_dir == tmp_path / ".auggd"

    def test_opencode_dir(self, tmp_path: Path):
        settings = load_settings(project_root=tmp_path)
        assert settings.opencode_dir == tmp_path / ".opencode"

    def test_manifest_file(self, tmp_path: Path):
        settings = load_settings(project_root=tmp_path)
        assert settings.manifest_file == tmp_path / ".auggd" / "install-manifest.json"


class TestGenerateToml:
    """Tests for generate_toml()."""

    def test_roundtrip(self, tmp_path: Path):
        settings = load_settings(project_root=tmp_path)
        toml_str = generate_toml(settings)
        assert "[workspace]" in toml_str
        assert "[models]" in toml_str
        assert "opencode/gpt-5-nano" in toml_str
