"""Base types and helpers for the auggd tools layer.

All tool actions return JSON to stdout and exit 0. Errors are in the payload,
not exit codes, so OpenCode captures the full message.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# ToolResult
# ---------------------------------------------------------------------------


@dataclass
class ToolResult:
    """Structured response from a tool action."""

    ok: bool
    data: dict = field(default_factory=dict)
    error: Optional[str] = None
    message: Optional[str] = None
    missing: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict."""
        d: dict[str, Any] = {"ok": self.ok}
        if self.ok:
            d["data"] = self.data
        else:
            d["error"] = self.error
            d["message"] = self.message
            if self.missing:
                d["missing"] = self.missing
        if self.warnings:
            d["warnings"] = self.warnings
        return d

    def emit(self) -> None:
        """Print this result as JSON to stdout and exit 0."""
        print(json.dumps(self.to_dict(), indent=2))
        sys.exit(0)

    # Convenience constructors -------------------------------------------

    @classmethod
    def success(
        cls, data: Optional[dict] = None, warnings: Optional[list[str]] = None
    ) -> "ToolResult":
        """Return a successful ToolResult."""
        return cls(ok=True, data=data or {}, warnings=warnings or [])

    @classmethod
    def failure(
        cls,
        error: str,
        message: str,
        missing: Optional[list[str]] = None,
        warnings: Optional[list[str]] = None,
    ) -> "ToolResult":
        """Return a failed ToolResult."""
        return cls(
            ok=False,
            error=error,
            message=message,
            missing=missing or [],
            warnings=warnings or [],
        )


# ---------------------------------------------------------------------------
# Enforcement helpers
# ---------------------------------------------------------------------------


def require_files(*paths: Path, error_code: str, message_template: str) -> Optional[ToolResult]:
    """Return a failure ToolResult if any of *paths* do not exist.

    Args:
        *paths: Paths that must exist.
        error_code: Short error identifier string.
        message_template: Human-readable message. Use ``{missing}`` as a
            placeholder for the list of missing paths.

    Returns:
        None if all files exist, otherwise a failure ToolResult.
    """
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        msg = message_template.format(missing=", ".join(missing))
        return ToolResult.failure(error_code, msg, missing=missing)
    return None


def require_json_field(
    path: Path,
    field_name: str,
    *,
    non_empty: bool = False,
    allowed_values: Optional[list[str]] = None,
    error_code: str,
    message: str,
) -> Optional[ToolResult]:
    """Validate a field in a JSON file.

    Args:
        path: Path to the JSON file (assumed to exist).
        field_name: Top-level key to check.
        non_empty: If True, the value must be a non-empty list.
        allowed_values: If provided, the value must be one of these strings.
        error_code: Short error identifier string.
        message: Human-readable failure message.

    Returns:
        None if the field is valid, otherwise a failure ToolResult.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return ToolResult.failure(
            "JSON_READ_ERROR",
            f"Could not read {path}: {e}",
            missing=[str(path)],
        )

    value = data.get(field_name)
    if non_empty and not value:
        return ToolResult.failure(error_code, message)
    if allowed_values is not None and value not in allowed_values:
        return ToolResult.failure(
            error_code,
            f"{message} (got {value!r}, expected one of: {allowed_values})",
        )
    return None


def read_json(path: Path) -> tuple[Optional[dict], Optional[ToolResult]]:
    """Read and parse a JSON file.

    Returns:
        (data, None) on success, (None, ToolResult failure) on error.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data, None
    except (json.JSONDecodeError, OSError) as e:
        return None, ToolResult.failure(
            "JSON_READ_ERROR",
            f"Could not read {path}: {e}",
            missing=[str(path)],
        )


def write_json(path: Path, data: dict) -> Optional[ToolResult]:
    """Write *data* as JSON to *path*.

    Returns:
        None on success, ToolResult failure on error.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return None
    except OSError as e:
        return ToolResult.failure("WRITE_ERROR", f"Could not write {path}: {e}")
