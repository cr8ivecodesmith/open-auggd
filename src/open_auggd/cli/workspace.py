"""CLI commands: ws create, list, delete, info."""

from __future__ import annotations

import sys

import click

from open_auggd.config.settings import load_settings
from open_auggd.workspace.manager import WorkspaceManager


@click.group(name="ws")
def ws_group() -> None:
    """Manage auggd workspaces."""


# ---------------------------------------------------------------------------
# ws create
# ---------------------------------------------------------------------------


@ws_group.command(name="create")
@click.argument("task_slug")
def ws_create(task_slug: str) -> None:
    """Create a new workspace for TASK_SLUG."""
    settings = load_settings()
    mgr = WorkspaceManager(settings.workspace_dir)
    try:
        ws = mgr.create(task_slug)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    click.echo(f"Workspace created: {ws.id}")
    click.echo(f"  slug : {ws.slug}")
    click.echo(f"  path : {ws.path}")


# ---------------------------------------------------------------------------
# ws list
# ---------------------------------------------------------------------------


@ws_group.command(name="list")
def ws_list() -> None:
    """List all workspaces."""
    settings = load_settings()
    mgr = WorkspaceManager(settings.workspace_dir)
    workspaces = mgr.list_workspaces()

    if not workspaces:
        click.echo("No workspaces found.")
        return

    # Table header
    header = f" {'#':>3}  {'Name':<40} {'Phase':<12} {'Iters'}"
    click.echo(header)
    click.echo("-" * len(header))

    for i, ws in enumerate(workspaces, start=1):
        iters = []
        if ws.planned_count:
            iters.append(f"{ws.planned_count} planned")
        if ws.dev_count:
            iters.append(f"{ws.dev_count} dev")
        if ws.reviewed_count:
            iters.append(f"{ws.reviewed_count} reviewed")
        iters_str = ", ".join(iters) if iters else "—"

        click.echo(f" {i:>3}  {ws.slug:<40} {ws.current_phase:<12} {iters_str}")


# ---------------------------------------------------------------------------
# ws delete
# ---------------------------------------------------------------------------


@ws_group.command(name="delete")
@click.argument("ref")
def ws_delete(ref: str) -> None:
    """Delete workspace REF (number or slug substring)."""
    settings = load_settings()
    mgr = WorkspaceManager(settings.workspace_dir)

    try:
        ws = mgr.resolve(ref)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if ws is None:
        click.echo(f"No workspace matching {ref!r}.", err=True)
        sys.exit(1)

    click.echo(f"About to delete workspace: {ws.slug} ({ws.id})")
    confirm = click.prompt("Confirm? [y/N]", default="N")
    if confirm.strip().lower() != "y":
        click.echo("Delete cancelled.")
        return

    try:
        mgr.delete(ref)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    click.echo(f"Deleted workspace: {ws.slug}")


# ---------------------------------------------------------------------------
# ws info
# ---------------------------------------------------------------------------


@ws_group.command(name="info")
@click.argument("ref")
def ws_info(ref: str) -> None:
    """Show info for workspace REF (number or slug substring)."""
    settings = load_settings()
    mgr = WorkspaceManager(settings.workspace_dir)

    try:
        info = mgr.info(ref)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    click.echo(f"ID    : {info['id']}")
    click.echo(f"Slug  : {info['slug']}")
    click.echo(f"Phase : {info['phase']}")
    click.echo(f"Iters : planned={info['planned']}, dev={info['dev']}, reviewed={info['reviewed']}")

    if info.get("spec_description"):
        click.echo(f"Spec  : {info['spec_description']}")

    if info.get("topics"):
        click.echo("Topics:")
        for topic in info["topics"]:
            click.echo(f"  - {topic}")
