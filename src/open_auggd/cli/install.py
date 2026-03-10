"""CLI commands: install, uninstall, update, reset."""

from __future__ import annotations

import sys

import click

from open_auggd.config.settings import load_settings
from open_auggd.install.installer import install, is_installed, reset, uninstall
from open_auggd.install.updater import update_models

# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------


@click.command(name="install")
@click.option("--force", is_flag=True, default=False, help="Overwrite existing files.")
def install_cmd(force: bool) -> None:
    """Install auggd into the current project."""
    settings = load_settings()

    try:
        written = install(settings, force=force)
    except FileExistsError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    click.echo(f"auggd installed. {len(written)} file(s) written.")
    for path in written:
        click.echo(f"  {path}")


# ---------------------------------------------------------------------------
# uninstall
# ---------------------------------------------------------------------------


@click.command(name="uninstall")
def uninstall_cmd() -> None:
    """Remove auggd files from this project."""
    settings = load_settings()

    if not is_installed(settings):
        click.echo("auggd does not appear to be installed in this project.")
        sys.exit(1)

    removed = uninstall(settings)
    click.echo(f"auggd uninstalled. {len(removed)} item(s) removed.")
    for path in removed:
        click.echo(f"  {path}")


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


@click.command(name="update")
def update_cmd() -> None:
    """Update model frontmatter in managed agent and command files."""
    settings = load_settings()
    updated = update_models(settings)
    if not updated:
        click.echo("No managed agent/command files found.")
        return
    click.echo(f"Updated model frontmatter in {len(updated)} file(s).")
    for path in updated:
        click.echo(f"  {path}")


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------


@click.command(name="reset")
def reset_cmd() -> None:
    """Restore .opencode/ managed files to bundled defaults."""
    settings = load_settings()

    click.echo("This will overwrite all auggd-managed .opencode/ files with bundled defaults.")
    confirm = click.prompt("Type 'yes' to confirm", default="")
    if confirm.strip() != "yes":
        click.echo("Reset cancelled.")
        return

    restored = reset(settings)
    click.echo(f"Reset complete. {len(restored)} file(s) restored.")
    for path in restored:
        click.echo(f"  {path}")
