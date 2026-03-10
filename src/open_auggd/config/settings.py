"""Configuration loading for open-auggd.

Priority (later overrides earlier):
  .auggd/auggd.toml  <  OAG_* env vars  <  CLI flags
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_DEFAULT_MODEL = "opencode/gpt-5-nano"


def _expand(path: str) -> Path:
    """Expand ~ and $VAR references in a path string."""
    return Path(os.path.expandvars(os.path.expanduser(path)))


@dataclass
class AgentModels:
    """Per-agent model overrides."""

    auggd: Optional[str] = None
    explorer: Optional[str] = None
    planner: Optional[str] = None
    developer: Optional[str] = None
    reviewer: Optional[str] = None
    finalizer: Optional[str] = None
    documenter: Optional[str] = None

    def get(self, agent_name: str) -> Optional[str]:
        """Return model override for *agent_name* (without 'oag-' prefix)."""
        return getattr(self, agent_name, None)


@dataclass
class CommandModels:
    """Per-command model overrides."""

    explore: Optional[str] = None
    plan: Optional[str] = None
    develop: Optional[str] = None
    review: Optional[str] = None
    finalize: Optional[str] = None
    document: Optional[str] = None
    status: Optional[str] = None
    resume: Optional[str] = None

    def get(self, command_name: str) -> Optional[str]:
        """Return model override for *command_name* (without 'oag-' prefix)."""
        return getattr(self, command_name, None)


@dataclass
class Settings:
    """Resolved configuration for open-auggd."""

    project_root: Path
    workspace_dir: Path
    docs_dir: Path
    default_model: str
    agent_models: AgentModels = field(default_factory=AgentModels)
    command_models: CommandModels = field(default_factory=CommandModels)

    @property
    def auggd_dir(self) -> Path:
        """Return the .auggd/ directory inside the project root."""
        return self.project_root / ".auggd"

    @property
    def opencode_dir(self) -> Path:
        """Return the .opencode/ directory inside the project root."""
        return self.project_root / ".opencode"

    @property
    def config_file(self) -> Path:
        """Return path to .auggd/auggd.toml."""
        return self.auggd_dir / "auggd.toml"

    @property
    def manifest_file(self) -> Path:
        """Return path to .auggd/install-manifest.json."""
        return self.auggd_dir / "install-manifest.json"

    @property
    def document_metadata_file(self) -> Path:
        """Return path to .auggd/document-metadata.json."""
        return self.auggd_dir / "document-metadata.json"

    def model_for_agent(self, agent_name: str) -> str:
        """Return the resolved model for an agent (falls back to default)."""
        return self.agent_models.get(agent_name) or self.default_model

    def model_for_command(self, command_name: str) -> str:
        """Return the resolved model for a command (falls back to default)."""
        return self.command_models.get(command_name) or self.default_model


def _load_toml(config_file: Path) -> dict:
    """Load a TOML file; return empty dict if it doesn't exist."""
    if not config_file.exists():
        return {}
    with open(config_file, "rb") as f:
        return tomllib.load(f)


def _agent_models_from_env(base: AgentModels) -> AgentModels:
    """Apply OAG_<AGENT>_MODEL env vars on top of *base*."""
    agents = ["auggd", "explorer", "planner", "developer", "reviewer", "finalizer", "documenter"]
    updates: dict[str, str] = {}
    for agent in agents:
        env_key = f"OAG_{agent.upper()}_MODEL"
        val = os.environ.get(env_key)
        if val:
            updates[agent] = val
    if not updates:
        return base
    import dataclasses

    return dataclasses.replace(base, **updates)


def _command_models_from_env(base: CommandModels) -> CommandModels:
    """Apply OAG_<COMMAND>_MODEL env vars on top of *base*."""
    commands = ["explore", "plan", "develop", "review", "finalize", "document", "status", "resume"]
    updates: dict[str, str] = {}
    for cmd in commands:
        env_key = f"OAG_{cmd.upper()}_MODEL"
        val = os.environ.get(env_key)
        if val:
            updates[cmd] = val
    if not updates:
        return base
    import dataclasses

    return dataclasses.replace(base, **updates)


def load_settings(
    project_root: Optional[Path] = None,
    workspace_dir: Optional[Path] = None,
    docs_dir: Optional[Path] = None,
    default_model: Optional[str] = None,
) -> Settings:
    """Load and merge settings from TOML, env vars, and explicit overrides.

    Args:
        project_root: Override project root (defaults to cwd).
        workspace_dir: CLI-level override for workspace root.
        docs_dir: CLI-level override for docs directory.
        default_model: CLI-level override for default model.

    Returns:
        Fully resolved Settings instance.
    """
    root = project_root or Path.cwd()
    config_file = root / ".auggd" / "auggd.toml"
    toml = _load_toml(config_file)

    # --- workspace dir ---
    ws_str = toml.get("workspace", {}).get("dir") or f"{root / '.auggd' / 'workspace'}"
    resolved_ws = _expand(os.environ.get("OAG_WORKSPACE_DIR", ws_str))
    if workspace_dir is not None:
        resolved_ws = workspace_dir

    # --- docs dir ---
    docs_str = toml.get("docs", {}).get("dir") or str(root / "docs")
    resolved_docs = _expand(os.environ.get("OAG_DOCS_DIR", docs_str))
    if docs_dir is not None:
        resolved_docs = docs_dir

    # --- default model ---
    model_str = toml.get("models", {}).get("default", _DEFAULT_MODEL)
    resolved_model = os.environ.get("OAG_DEFAULT_MODEL", model_str)
    if default_model is not None:
        resolved_model = default_model

    # --- per-agent models from TOML ---
    toml_agent_models = toml.get("models", {}).get("agents", {})
    agent_models = AgentModels(
        auggd=toml_agent_models.get("auggd"),
        explorer=toml_agent_models.get("explorer"),
        planner=toml_agent_models.get("planner"),
        developer=toml_agent_models.get("developer"),
        reviewer=toml_agent_models.get("reviewer"),
        finalizer=toml_agent_models.get("finalizer"),
        documenter=toml_agent_models.get("documenter"),
    )
    agent_models = _agent_models_from_env(agent_models)

    # --- per-command models from TOML ---
    toml_cmd_models = toml.get("models", {}).get("commands", {})
    command_models = CommandModels(
        explore=toml_cmd_models.get("explore"),
        plan=toml_cmd_models.get("plan"),
        develop=toml_cmd_models.get("develop"),
        review=toml_cmd_models.get("review"),
        finalize=toml_cmd_models.get("finalize"),
        document=toml_cmd_models.get("document"),
        status=toml_cmd_models.get("status"),
        resume=toml_cmd_models.get("resume"),
    )
    command_models = _command_models_from_env(command_models)

    return Settings(
        project_root=root,
        workspace_dir=resolved_ws,
        docs_dir=resolved_docs,
        default_model=resolved_model or _DEFAULT_MODEL,
        agent_models=agent_models,
        command_models=command_models,
    )


def generate_toml(settings: Settings) -> str:
    """Generate the content of auggd.toml from *settings*.

    Returns:
        A TOML-formatted string ready to write to disk.
    """
    lines = [
        "[workspace]",
        f'dir = "{settings.workspace_dir}"',
        "",
        "[docs]",
        f'dir = "{settings.docs_dir}"',
        "",
        "[models]",
        f'default = "{settings.default_model}"',
        "",
        "[models.agents]",
        "# Per-agent model overrides. Key is agent name without 'oag-' prefix.",
        '# auggd = "anthropic/claude-haiku-4-5"',
        '# explorer = "anthropic/claude-haiku-4-5"',
        '# developer = "anthropic/claude-haiku-4-5"',
        "",
        "[models.commands]",
        "# Per-command model overrides. Key is command name without 'oag-' prefix.",
        '# explore = "anthropic/claude-haiku-4-5"',
        "",
    ]
    return "\n".join(lines)
