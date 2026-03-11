"""Configuration loading: TOML + OAG_* env vars, path expansion."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]

_DEFAULTS = {
    "workspace_dir": ".auggd/workspace",
    "docs_dir": "docs",
    "default_model": "opencode/gpt-5-nano",
}


def _expand(value: str) -> str:
    """Expand ~ and $VAR references in a path string."""
    return os.path.expandvars(os.path.expanduser(value))


@dataclass
class Settings:
    """Resolved configuration for an auggd project."""

    workspace_dir: str
    docs_dir: str
    default_model: str
    agent_models: dict[str, str] = field(default_factory=dict)
    command_models: dict[str, str] = field(default_factory=dict)

    def effective_agent_model(self, agent: str) -> str:
        """Return the model to use for the given agent name."""
        return self.agent_models.get(agent, self.default_model)

    def effective_command_model(self, command: str) -> str:
        """Return the model to use for the given command name."""
        return self.command_models.get(command, self.default_model)


def load_settings(project_root: Path) -> Settings:
    """Load settings from .auggd/auggd.toml and OAG_* env vars.

    Hierarchy (lowest to highest precedence):
      1. Built-in defaults
      2. .auggd/auggd.toml
      3. OAG_* environment variables
    """
    toml_path = project_root / ".auggd" / "auggd.toml"
    toml: dict = {}
    if toml_path.exists():
        with open(toml_path, "rb") as f:
            toml = tomllib.load(f)

    # --- scalar values ---
    workspace_dir = toml.get("workspace", {}).get("dir", _DEFAULTS["workspace_dir"])
    docs_dir = toml.get("docs", {}).get("dir", _DEFAULTS["docs_dir"])
    default_model = toml.get("defaults", {}).get("model", _DEFAULTS["default_model"])

    # --- per-agent/command model maps from TOML ---
    agent_models: dict[str, str] = dict(toml.get("agents", {}).get("models", {}))
    command_models: dict[str, str] = dict(toml.get("commands", {}).get("models", {}))

    # --- env var overrides ---
    if env_model := os.environ.get("OAG_DEFAULT_MODEL"):
        default_model = env_model
    if env_ws := os.environ.get("OAG_WORKSPACE_DIR"):
        workspace_dir = env_ws
    if env_docs := os.environ.get("OAG_DOCS_DIR"):
        docs_dir = env_docs

    # Scan for OAG_<AGENT>_MODEL and OAG_<COMMAND>_MODEL patterns.
    # We discover them by scanning os.environ for the prefix/suffix pattern.
    for key, val in os.environ.items():
        if key.startswith("OAG_") and key.endswith("_MODEL") and key != "OAG_DEFAULT_MODEL":
            # Strip OAG_ prefix and _MODEL suffix → agent or command name (lowercase)
            inner = key[4:-6].lower()  # e.g. "DEVELOPER" → "developer"
            # Heuristic: commands match known command names; everything else is an agent.
            # We store in both and let callers use the right lookup method.
            # To distinguish agents from commands we rely on naming conventions from spec:
            # agent env names: OAG_<AGENT>_MODEL where agent matches an agent name
            # command env names: OAG_<COMMAND>_MODEL where command matches a command name
            # Since there's overlap (e.g. "develop" is both a command and a concept),
            # we populate agent_models for anything not in the known command set,
            # and command_models for known commands. Both can coexist.
            _KNOWN_COMMANDS = {
                "explore",
                "plan",
                "develop",
                "review",
                "finalize",
                "document",
                "status",
                "resume",
            }
            _KNOWN_AGENTS = {
                "explorer",
                "planner",
                "developer",
                "reviewer",
                "finalizer",
                "documenter",
                "auggd",
            }
            if inner in _KNOWN_COMMANDS:
                command_models[inner] = val
            if inner in _KNOWN_AGENTS:
                agent_models[inner] = val

    # --- path expansion ---
    workspace_dir = _expand(workspace_dir)
    docs_dir = _expand(docs_dir)

    return Settings(
        workspace_dir=workspace_dir,
        docs_dir=docs_dir,
        default_model=default_model,
        agent_models=agent_models,
        command_models=command_models,
    )
