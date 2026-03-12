"""Dataclasses and enums for all workspace artifact schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Phase(str, Enum):
    """Valid workspace phases."""

    EXPLORE = "explore"
    PLAN = "plan"
    DEVELOP = "develop"
    REVIEW = "review"
    FINALIZE = "finalize"
    DONE = "done"


def _now_iso() -> str:
    """Return current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _parse_dt(value: str) -> datetime:
    """Parse an ISO 8601 datetime string to a timezone-aware datetime."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# ---------------------------------------------------------------------------
# workspace-metadata.json
# ---------------------------------------------------------------------------


@dataclass
class WorkspaceMetadata:
    """Identity record for a workspace.

    Written by ``auggd ws create``. ``updated_at`` is touched on any mutation.
    Phase state, iteration, title, scope, and non-goals are derived on demand
    from ``iteration-log.json`` and ``spec.md`` — they are not stored here.
    """

    id: str
    slug: str
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {
            "id": self.id,
            "slug": self.slug,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkspaceMetadata:
        """Deserialise from a JSON-compatible dict."""
        return cls(
            id=data["id"],
            slug=data["slug"],
            created_at=_parse_dt(data["created_at"]),
            updated_at=_parse_dt(data["updated_at"]),
        )


# ---------------------------------------------------------------------------
# ws list item (enriched list entry)
# ---------------------------------------------------------------------------


@dataclass
class WorkspaceListItem:
    """Enriched workspace entry for ``auggd ws list`` output.

    Carries the raw metadata plus fields derived on demand from
    ``iteration-log.json`` and ``spec.md``.

    ``phase``, ``iteration``, and ``interrupted`` are all ``None`` when the
    iteration log is empty (workspace not yet started). The list renders them
    as ``not started`` / ``-`` / ``-`` in that case.
    """

    metadata: WorkspaceMetadata
    title: str
    phase: str | None
    iteration: int | None
    interrupted: bool | None


# ---------------------------------------------------------------------------
# ws info output schema (context prime)
# ---------------------------------------------------------------------------


@dataclass
class WsInfoIteration:
    """Summary of a single iteration for the ws info context prime."""

    n: int
    explore_status: str | None
    plan_status: str | None
    develop_status: str | None
    review_status: str | None
    finalize_status: str | None
    phases: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {
            "n": self.n,
            "explore_status": self.explore_status,
            "plan_status": self.plan_status,
            "develop_status": self.develop_status,
            "review_status": self.review_status,
            "finalize_status": self.finalize_status,
            "phases": self.phases,
        }


@dataclass
class WsInfoOutput:
    """Context prime output for ``auggd ws info``.

    This is the single orientation source for every subagent entry point.
    Agents derive current phase and status from the ``last_n_iterations`` entries.
    """

    id: str
    slug: str
    title: str
    last_n_iterations: list[WsInfoIteration]
    spec_path: str | None
    attachments: list[str]
    workspace_path: str

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "last_n_iterations": [it.to_dict() for it in self.last_n_iterations],
            "spec_path": self.spec_path,
            "attachments": list(self.attachments),
            "workspace_path": self.workspace_path,
        }
