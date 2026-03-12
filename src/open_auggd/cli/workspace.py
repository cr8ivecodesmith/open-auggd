"""CLI commands for workspace management: ws create, list, info, delete."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from open_auggd.config.settings import load_settings
from open_auggd.workspace.manager import WorkspaceError, WorkspaceManager


def _manager(project_root: Path) -> WorkspaceManager:
    """Return a WorkspaceManager configured from project settings."""
    settings = load_settings(project_root)
    ws_dir = Path(settings.workspace_dir)
    if not ws_dir.is_absolute():
        ws_dir = project_root / ws_dir
    ws_dir.mkdir(parents=True, exist_ok=True)
    return WorkspaceManager(ws_dir)


@click.group()
def ws() -> None:
    """Manage auggd workspaces."""


@ws.command()
@click.argument("slug")
def create(slug: str) -> None:
    """Create a new workspace with the given SLUG."""
    root = Path.cwd()
    try:
        mgr = _manager(root)
        meta = mgr.create(slug)
    except (ValueError, WorkspaceError) as exc:
        click.echo(f"ws create failed: {exc}", err=True)
        sys.exit(1)

    click.echo(f"{meta.id}-{meta.slug}")


@ws.command("list")
def list_workspaces() -> None:
    """List all workspaces sorted by ID."""
    root = Path.cwd()
    try:
        mgr = _manager(root)
        items = mgr.list()
    except Exception as exc:
        click.echo(f"ws list failed: {exc}", err=True)
        sys.exit(1)

    if not items:
        click.echo("No workspaces found.")
        return

    # Column widths.
    slug_w = max(len(item.metadata.slug) for item in items)
    slug_w = max(slug_w, 4)  # min width for header "Slug"
    title_w = max((len(item.title) for item in items), default=0)
    title_w = max(title_w, 5)  # min width for header "Title"
    phase_w = max(len("not started"), 5)  # fixed: "not started" is the longest value

    header = (
        f"{'#':<3}  "
        f"{'Slug':<{slug_w}}  "
        f"{'Title':<{title_w}}  "
        f"{'Phase':<{phase_w}}  "
        f"{'Iter':<4}  "
        f"Interrupted"
    )
    click.echo(header)
    click.echo("-" * len(header))

    for i, item in enumerate(items, start=1):
        meta = item.metadata
        if item.iteration is None:
            phase = "not started"
            iteration = "-"
            interrupted = "-"
        else:
            phase = item.phase or ""
            iteration = str(item.iteration)
            interrupted = "Y" if item.interrupted else "N"
        click.echo(
            f"{i:<3}  "
            f"{meta.slug:<{slug_w}}  "
            f"{item.title:<{title_w}}  "
            f"{phase:<{phase_w}}  "
            f"{iteration:<4}  "
            f"{interrupted}"
        )


@ws.command()
@click.argument("ref")
@click.option(
    "--last", default=3, show_default=True, help="Number of recent iterations to include."
)
def info(ref: str, last: int) -> None:
    """Print context prime JSON for workspace REF (index or slug)."""
    root = Path.cwd()
    try:
        mgr = _manager(root)
        output = mgr.info(ref, last=last)
    except WorkspaceError as exc:
        click.echo(f"ws info failed: {exc}", err=True)
        sys.exit(1)

    click.echo(json.dumps(output.to_dict(), indent=2))


@ws.command()
@click.argument("ref")
def delete(ref: str) -> None:
    """Delete workspace REF (index or slug)."""
    root = Path.cwd()
    try:
        mgr = _manager(root)
        ws_path = mgr.resolve(ref)
        ws_name = ws_path.name
    except WorkspaceError as exc:
        click.echo(f"ws delete failed: {exc}", err=True)
        sys.exit(1)

    answer = click.prompt(f"Type 'yes' to confirm deletion of workspace {ws_name}")
    if answer.strip().lower() != "yes":
        click.echo("Aborted.", err=True)
        sys.exit(1)

    try:
        mgr.delete(ref)
    except WorkspaceError as exc:
        click.echo(f"ws delete failed: {exc}", err=True)
        sys.exit(1)

    click.echo(f"Deleted workspace: {ws_name}")
