"""ToolResult — response data model for all phase tool actions.

All tool actions return JSON to stdout and exit 0. Errors are carried in the
payload, never via non-zero exit codes. This module defines the canonical
response shape.

Success::

    {"ok": true, "data": {...}}

Failure::

    {"ok": false, "error": "MISSING_PLAN", "message": "...", "missing": [...]}

The ``missing`` field is always present on failure (as ``[]`` when empty).
``data`` is never emitted on failure. ``error``/``message``/``missing`` are
never emitted on success.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Canonical response for every phase tool action.

    Args:
        ok: ``True`` for success, ``False`` for failure.
        data: Success payload. Only emitted when ``ok=True``.
        error: Short machine-readable error code. Only emitted when ``ok=False``.
        message: Human-readable explanation. Only emitted when ``ok=False``.
        missing: List of missing artifact references. Only emitted when
            ``ok=False``; defaults to ``[]`` when not provided.
    """

    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    message: str | None = None
    missing: list[str] | None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict.

        Returns:
            Dict matching the tool response contract — success keys only on
            success, failure keys only on failure.
        """
        if self.ok:
            return {"ok": True, "data": self.data}
        return {
            "ok": False,
            "error": self.error,
            "message": self.message,
            "missing": self.missing if self.missing is not None else [],
        }

    def to_json(self) -> str:
        """Serialise to a JSON string.

        Returns:
            Compact JSON string suitable for writing to stdout.
        """
        return json.dumps(self.to_dict())
