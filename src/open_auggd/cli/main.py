"""auggd CLI entry point."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from open_auggd.cli.workspace import ws
from open_auggd.config.settings import load_settings
from open_auggd.install.installer import Installer, InstallError
from open_auggd.install.updater import update_model_lines


def _project_root() -> Path:
    """Return the current working directory as the project root."""
    return Path.cwd()


@click.group()
def cli() -> None:
    """Auggd — orchestrated AI workflow engine."""


cli.add_command(ws)


@cli.command()
def install() -> None:
    """Install auggd into the current project."""
    root = _project_root()
    try:
        written = Installer(root).install()
    except Exception as exc:
        click.echo(f"Install failed: {exc}", err=True)
        sys.exit(1)

    click.echo(f"auggd installed: {len(written)} files written to .opencode/")
    click.echo("  .auggd/auggd.toml created (skipped if already present)")


@cli.command()
def uninstall() -> None:
    """Remove all auggd-managed files from the current project."""
    root = _project_root()
    inst = Installer(root)

    # Check installation state before asking for confirmation.
    try:
        inst.uninstall(confirmed=False)
    except InstallError as exc:
        if "not installed" in str(exc):
            click.echo(f"Uninstall failed: {exc}", err=True)
            sys.exit(1)
        # Otherwise it's the confirmation guard — proceed to prompt.

    click.echo("This will remove .auggd/ and all managed .opencode/ files.")
    answer = click.prompt("Type 'yes' to confirm")
    if answer.strip().lower() != "yes":
        click.echo("Aborted.", err=True)
        sys.exit(1)

    try:
        inst.uninstall(confirmed=True)
    except InstallError as exc:
        click.echo(f"Uninstall failed: {exc}", err=True)
        sys.exit(1)

    click.echo("auggd uninstalled. .auggd/ removed; pre-existing .opencode/ content preserved.")


@cli.command()
def update() -> None:
    """Update model: frontmatter in all managed agent and command files."""
    root = _project_root()
    try:
        settings = load_settings(root)
        updated = update_model_lines(root, settings)
    except InstallError as exc:
        click.echo(f"Update failed: {exc}", err=True)
        sys.exit(1)

    if updated:
        click.echo(f"auggd update: {len(updated)} file(s) updated.")
        for path in updated:
            click.echo(f"  {path}")
    else:
        click.echo("auggd update: all model lines already current, nothing changed.")


@cli.command()
def reset() -> None:
    """Restore all managed .opencode/ files to their bundled defaults."""
    root = _project_root()
    inst = Installer(root)

    # Check installation state before asking for confirmation.
    try:
        inst.reset(confirmed=False)
    except InstallError as exc:
        if "not installed" in str(exc):
            click.echo(f"Reset failed: {exc}", err=True)
            sys.exit(1)
        # Otherwise it's the confirmation guard — proceed to prompt.

    click.echo("This will overwrite all managed .opencode/ files with bundled defaults.")
    answer = click.prompt("Type 'yes' to confirm")
    if answer.strip().lower() != "yes":
        click.echo("Aborted.", err=True)
        sys.exit(1)

    try:
        restored = inst.reset(confirmed=True)
    except InstallError as exc:
        click.echo(f"Reset failed: {exc}", err=True)
        sys.exit(1)

    click.echo(f"auggd reset: {len(restored)} file(s) restored to bundled defaults.")


# Allow running as a module: python -m open_auggd.cli.main
if __name__ == "__main__":
    cli()
