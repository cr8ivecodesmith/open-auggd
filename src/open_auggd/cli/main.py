"""Entry point for the auggd CLI."""

from __future__ import annotations

import click

from open_auggd.cli.install import install_cmd, uninstall_cmd, update_cmd, reset_cmd
from open_auggd.cli.workspace import ws_group
from open_auggd.cli.tools import tools_group


@click.group()
@click.version_option()
def cli() -> None:
    """auggd — agentic development workflow manager for OpenCode."""


cli.add_command(install_cmd)
cli.add_command(uninstall_cmd)
cli.add_command(update_cmd)
cli.add_command(reset_cmd)
cli.add_command(ws_group)
cli.add_command(tools_group)
