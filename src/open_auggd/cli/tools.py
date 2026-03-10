"""CLI commands: auggd tools <phase> --ws=<ref> <action>.

All commands in this module emit JSON to stdout and exit 0.
Errors are in the JSON payload (never in exit codes) so OpenCode
captures the full structured response.
"""

from __future__ import annotations

import json
import sys

import click

from open_auggd.config.settings import load_settings
from open_auggd.workspace.manager import WorkspaceManager
import open_auggd.tools.explore as _explore
import open_auggd.tools.plan as _plan
import open_auggd.tools.develop as _develop
import open_auggd.tools.review as _review
import open_auggd.tools.finalize as _finalize
import open_auggd.tools.document as _document
from open_auggd.tools.base import ToolResult


def _emit(result: ToolResult) -> None:
    """Print result JSON and exit 0."""
    print(json.dumps(result.to_dict(), indent=2))
    sys.exit(0)


def _resolve_ws(ref: str) -> tuple:
    """Resolve workspace ref → (settings, ws_path).  Emits failure and exits on error."""
    settings = load_settings()
    mgr = WorkspaceManager(settings.workspace_dir)
    try:
        ws = mgr.resolve(ref)
    except ValueError as e:
        _emit(ToolResult.failure("INVALID_WS_REF", str(e)))
        raise SystemExit(0)  # _emit calls sys.exit; this satisfies type checker
    if ws is None:
        _emit(ToolResult.failure("WS_NOT_FOUND", f"No workspace matching {ref!r}."))
        raise SystemExit(0)
    return settings, ws.path


# ---------------------------------------------------------------------------
# tools group
# ---------------------------------------------------------------------------


@click.group(name="tools")
def tools_group() -> None:
    """Workflow enforcement tools (called by agents via OpenCode)."""


# ---------------------------------------------------------------------------
# explore
# ---------------------------------------------------------------------------


@tools_group.group(name="explore")
@click.option("--ws", "ws_ref", required=True, help="Workspace number or slug substring.")
@click.pass_context
def explore_group(ctx: click.Context, ws_ref: str) -> None:
    """Explore phase tools."""
    ctx.ensure_object(dict)
    ctx.obj["ws_ref"] = ws_ref


@explore_group.command(name="start")
@click.pass_context
def explore_start(ctx: click.Context) -> None:
    """Start explore phase."""
    _, ws_path = _resolve_ws(ctx.obj["ws_ref"])
    _emit(_explore.start(ws_path))


@explore_group.command(name="status")
@click.pass_context
def explore_status(ctx: click.Context) -> None:
    """Show explore phase status."""
    _, ws_path = _resolve_ws(ctx.obj["ws_ref"])
    _emit(_explore.status(ws_path))


@explore_group.command(name="done")
@click.pass_context
def explore_done(ctx: click.Context) -> None:
    """Mark explore phase done."""
    _, ws_path = _resolve_ws(ctx.obj["ws_ref"])
    _emit(_explore.done(ws_path))


# ---------------------------------------------------------------------------
# plan
# ---------------------------------------------------------------------------


@tools_group.group(name="plan")
@click.option("--ws", "ws_ref", required=True, help="Workspace number or slug substring.")
@click.pass_context
def plan_group(ctx: click.Context, ws_ref: str) -> None:
    """Plan phase tools."""
    ctx.ensure_object(dict)
    ctx.obj["ws_ref"] = ws_ref


@plan_group.command(name="start")
@click.pass_context
def plan_start(ctx: click.Context) -> None:
    """Start plan phase (requires explore done)."""
    _, ws_path = _resolve_ws(ctx.obj["ws_ref"])
    _emit(_plan.start(ws_path))


@plan_group.group(name="iter")
@click.pass_context
def plan_iter_group(ctx: click.Context) -> None:
    """Iteration sub-commands."""


@plan_iter_group.command(name="create")
@click.pass_context
def plan_iter_create(ctx: click.Context) -> None:
    """Create next iteration plan."""
    _, ws_path = _resolve_ws(ctx.obj["ws_ref"])
    _emit(_plan.iter_create(ws_path))


@plan_iter_group.command(name="status")
@click.argument("n", type=int)
@click.pass_context
def plan_iter_status(ctx: click.Context, n: int) -> None:
    """Show status of iteration N."""
    _, ws_path = _resolve_ws(ctx.obj["ws_ref"])
    _emit(_plan.iter_status(ws_path, n))


@plan_iter_group.command(name="done")
@click.argument("n", type=int)
@click.pass_context
def plan_iter_done(ctx: click.Context, n: int) -> None:
    """Mark iteration N plan done (ready for dev)."""
    _, ws_path = _resolve_ws(ctx.obj["ws_ref"])
    _emit(_plan.iter_done(ws_path, n))


# ---------------------------------------------------------------------------
# develop
# ---------------------------------------------------------------------------


@tools_group.group(name="develop")
@click.option("--ws", "ws_ref", required=True, help="Workspace number or slug substring.")
@click.pass_context
def develop_group(ctx: click.Context, ws_ref: str) -> None:
    """Develop phase tools."""
    ctx.ensure_object(dict)
    ctx.obj["ws_ref"] = ws_ref


@develop_group.command(name="start")
@click.argument("n", type=int)
@click.pass_context
def develop_start(ctx: click.Context, n: int) -> None:
    """Start development of iteration N."""
    _, ws_path = _resolve_ws(ctx.obj["ws_ref"])
    _emit(_develop.start(ws_path, n))


@develop_group.command(name="update")
@click.argument("n", type=int)
@click.option("--data", "json_data", required=True, help="JSON patch string.")
@click.pass_context
def develop_update(ctx: click.Context, n: int, json_data: str) -> None:
    """Update devlog for iteration N with JSON patch."""
    _, ws_path = _resolve_ws(ctx.obj["ws_ref"])
    try:
        patch = json.loads(json_data)
    except json.JSONDecodeError as e:
        _emit(ToolResult.failure("INVALID_JSON", f"--data is not valid JSON: {e}"))
        return
    _emit(_develop.update(ws_path, n, patch))


@develop_group.command(name="status")
@click.argument("n", type=int)
@click.pass_context
def develop_status(ctx: click.Context, n: int) -> None:
    """Show devlog status for iteration N."""
    _, ws_path = _resolve_ws(ctx.obj["ws_ref"])
    _emit(_develop.status(ws_path, n))


@develop_group.command(name="done")
@click.argument("n", type=int)
@click.pass_context
def develop_done(ctx: click.Context, n: int) -> None:
    """Mark development of iteration N complete."""
    _, ws_path = _resolve_ws(ctx.obj["ws_ref"])
    _emit(_develop.done(ws_path, n))


# ---------------------------------------------------------------------------
# review
# ---------------------------------------------------------------------------


@tools_group.group(name="review")
@click.option("--ws", "ws_ref", required=True, help="Workspace number or slug substring.")
@click.pass_context
def review_group(ctx: click.Context, ws_ref: str) -> None:
    """Review phase tools."""
    ctx.ensure_object(dict)
    ctx.obj["ws_ref"] = ws_ref


@review_group.command(name="start")
@click.argument("n", type=int)
@click.pass_context
def review_start(ctx: click.Context, n: int) -> None:
    """Start review for iteration N."""
    _, ws_path = _resolve_ws(ctx.obj["ws_ref"])
    _emit(_review.start(ws_path, n))


@review_group.command(name="update")
@click.argument("n", type=int)
@click.option("--data", "json_data", required=True, help="JSON patch string.")
@click.pass_context
def review_update(ctx: click.Context, n: int, json_data: str) -> None:
    """Update review findings for iteration N."""
    _, ws_path = _resolve_ws(ctx.obj["ws_ref"])
    try:
        patch = json.loads(json_data)
    except json.JSONDecodeError as e:
        _emit(ToolResult.failure("INVALID_JSON", f"--data is not valid JSON: {e}"))
        return
    _emit(_review.update(ws_path, n, patch))


@review_group.command(name="done")
@click.argument("n", type=int)
@click.argument("review_status")
@click.pass_context
def review_done(ctx: click.Context, n: int, review_status: str) -> None:
    """Set review outcome for iteration N (blocked/changes_requested/approved)."""
    _, ws_path = _resolve_ws(ctx.obj["ws_ref"])
    _emit(_review.done(ws_path, n, review_status))


# ---------------------------------------------------------------------------
# finalize
# ---------------------------------------------------------------------------


@tools_group.group(name="finalize")
@click.option("--ws", "ws_ref", required=True, help="Workspace number or slug substring.")
@click.pass_context
def finalize_group(ctx: click.Context, ws_ref: str) -> None:
    """Finalize phase tools."""
    ctx.ensure_object(dict)
    ctx.obj["ws_ref"] = ws_ref


@finalize_group.command(name="iter")
@click.argument("n", type=int)
@click.option("--commit", is_flag=True, default=False, help="Auto-commit after finalize.")
@click.pass_context
def finalize_iter(ctx: click.Context, n: int, commit: bool) -> None:
    """Finalize iteration N (requires approved review)."""
    _, ws_path = _resolve_ws(ctx.obj["ws_ref"])
    _emit(_finalize.iter_finalize(ws_path, n, commit=commit))


# ---------------------------------------------------------------------------
# document
# ---------------------------------------------------------------------------


@tools_group.group(name="document")
def document_group() -> None:
    """Document phase tools."""


@document_group.command(name="check")
def document_check() -> None:
    """Check git status and document metadata."""
    settings = load_settings()
    _emit(_document.check(settings.project_root, settings.document_metadata_file))


@document_group.command(name="init")
def document_init() -> None:
    """Initialize document-metadata.json."""
    settings = load_settings()
    _emit(_document.init(settings.project_root, settings.document_metadata_file))


@document_group.command(name="update-metadata")
@click.option("--data", "json_data", required=True, help="JSON patch string.")
def document_update_metadata(json_data: str) -> None:
    """Update document metadata with JSON patch."""
    settings = load_settings()
    try:
        patch = json.loads(json_data)
    except json.JSONDecodeError as e:
        _emit(ToolResult.failure("INVALID_JSON", f"--data is not valid JSON: {e}"))
        return
    _emit(_document.update_metadata(settings.document_metadata_file, patch))
