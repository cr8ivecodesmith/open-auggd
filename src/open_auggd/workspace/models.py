"""Dataclasses and status enums for all workspace artifact schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ExploreStatus(str, Enum):
    """Status of the explore phase for a workspace."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class PlanStatus(str, Enum):
    """Status of a single iteration plan."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DEV_COMPLETE = "dev_complete"
    REVIEW_COMPLETE = "review_complete"
    FINALIZED = "finalized"


class DevStatus(str, Enum):
    """Status of a single iteration devlog."""

    IN_PROGRESS = "in_progress"
    DEV_COMPLETE = "dev_complete"


class ReviewStatus(str, Enum):
    """Status of a single iteration review."""

    BLOCKED = "blocked"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"


class FindingSeverity(str, Enum):
    """Severity level for a review finding."""

    MUST_FIX = "MUST-FIX"
    SHOULD_FIX = "SHOULD-FIX"
    NICE_TO_HAVE = "NICE-TO-HAVE"


# ---------------------------------------------------------------------------
# Explore
# ---------------------------------------------------------------------------


@dataclass
class SourceEntry:
    """A referenced source in the exploration phase."""

    url: str = ""
    title: str = ""
    relevance: str = ""


@dataclass
class AttachmentEntry:
    """A file attachment referenced in the exploration phase."""

    filename: str = ""
    description: str = ""


@dataclass
class ExploreAttachments:
    """Schema for explore/attachments.json."""

    explore_status: ExploreStatus = ExploreStatus.PENDING
    topics: list[str] = field(default_factory=list)
    sources: list[SourceEntry] = field(default_factory=list)
    attachments: list[AttachmentEntry] = field(default_factory=list)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict."""
        return {
            "explore_status": self.explore_status.value,
            "topics": list(self.topics),
            "sources": [
                {"url": s.url, "title": s.title, "relevance": s.relevance} for s in self.sources
            ],
            "attachments": [
                {"filename": a.filename, "description": a.description} for a in self.attachments
            ],
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExploreAttachments":
        """Deserialize from a dict."""
        return cls(
            explore_status=ExploreStatus(data.get("explore_status", "pending")),
            topics=list(data.get("topics", [])),
            sources=[SourceEntry(**s) for s in data.get("sources", [])],
            attachments=[AttachmentEntry(**a) for a in data.get("attachments", [])],
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data
            else datetime.now(timezone.utc),
        )


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------


@dataclass
class IterPlan:
    """Schema for plan/iter-N-plan.json."""

    n: int = 1
    status: PlanStatus = PlanStatus.PENDING
    title: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    scope: list[str] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict."""
        return {
            "n": self.n,
            "status": self.status.value,
            "title": self.title,
            "acceptance_criteria": list(self.acceptance_criteria),
            "scope": list(self.scope),
            "non_goals": list(self.non_goals),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IterPlan":
        """Deserialize from a dict."""
        return cls(
            n=data.get("n", 1),
            status=PlanStatus(data.get("status", "pending")),
            title=data.get("title", ""),
            acceptance_criteria=list(data.get("acceptance_criteria", [])),
            scope=list(data.get("scope", [])),
            non_goals=list(data.get("non_goals", [])),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data
            else datetime.now(timezone.utc),
        )


@dataclass
class ProgressLogEntry:
    """A single iteration entry in progress-log.json."""

    n: int = 1
    plan_status: str = "pending"
    dev_status: Optional[str] = None
    review_status: Optional[str] = None
    finalized: bool = False
    finalized_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict."""
        return {
            "n": self.n,
            "plan_status": self.plan_status,
            "dev_status": self.dev_status,
            "review_status": self.review_status,
            "finalized": self.finalized,
            "finalized_at": self.finalized_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProgressLogEntry":
        """Deserialize from a dict."""
        return cls(
            n=data.get("n", 1),
            plan_status=data.get("plan_status", "pending"),
            dev_status=data.get("dev_status"),
            review_status=data.get("review_status"),
            finalized=data.get("finalized", False),
            finalized_at=data.get("finalized_at"),
        )


@dataclass
class ProgressLog:
    """Schema for plan/progress-log.json."""

    workspace_id: str = ""
    iterations: list[ProgressLogEntry] = field(default_factory=list)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict."""
        return {
            "workspace_id": self.workspace_id,
            "iterations": [e.to_dict() for e in self.iterations],
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProgressLog":
        """Deserialize from a dict."""
        return cls(
            workspace_id=data.get("workspace_id", ""),
            iterations=[ProgressLogEntry.from_dict(e) for e in data.get("iterations", [])],
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data
            else datetime.now(timezone.utc),
        )


# ---------------------------------------------------------------------------
# Develop
# ---------------------------------------------------------------------------


@dataclass
class TestRunEntry:
    """A test run record in a devlog."""

    command: str = ""
    result: str = ""


@dataclass
class IterDevlog:
    """Schema for develop/iter-N-devlog.json."""

    n: int = 1
    status: DevStatus = DevStatus.IN_PROGRESS
    files_touched: list[str] = field(default_factory=list)
    tests_run: list[TestRunEntry] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    next_red_step: str = ""
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict."""
        return {
            "n": self.n,
            "status": self.status.value,
            "files_touched": list(self.files_touched),
            "tests_run": [{"command": t.command, "result": t.result} for t in self.tests_run],
            "blockers": list(self.blockers),
            "next_red_step": self.next_red_step,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IterDevlog":
        """Deserialize from a dict."""
        return cls(
            n=data.get("n", 1),
            status=DevStatus(data.get("status", "in_progress")),
            files_touched=list(data.get("files_touched", [])),
            tests_run=[TestRunEntry(**t) for t in data.get("tests_run", [])],
            blockers=list(data.get("blockers", [])),
            next_red_step=data.get("next_red_step", ""),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data
            else datetime.now(timezone.utc),
        )


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------


@dataclass
class ReviewFinding:
    """A single finding in a review."""

    severity: FindingSeverity = FindingSeverity.SHOULD_FIX
    file: str = ""
    description: str = ""
    suggestion: str = ""

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict."""
        return {
            "severity": self.severity.value,
            "file": self.file,
            "description": self.description,
            "suggestion": self.suggestion,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReviewFinding":
        """Deserialize from a dict."""
        return cls(
            severity=FindingSeverity(data.get("severity", "SHOULD-FIX")),
            file=data.get("file", ""),
            description=data.get("description", ""),
            suggestion=data.get("suggestion", ""),
        )


@dataclass
class IterReview:
    """Schema for review/iter-N-review.json."""

    n: int = 1
    status: ReviewStatus = ReviewStatus.BLOCKED
    findings: list[ReviewFinding] = field(default_factory=list)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict."""
        return {
            "n": self.n,
            "status": self.status.value,
            "findings": [f.to_dict() for f in self.findings],
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IterReview":
        """Deserialize from a dict."""
        return cls(
            n=data.get("n", 1),
            status=ReviewStatus(data.get("status", "blocked")),
            findings=[ReviewFinding.from_dict(f) for f in data.get("findings", [])],
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data
            else datetime.now(timezone.utc),
        )


# ---------------------------------------------------------------------------
# Document metadata
# ---------------------------------------------------------------------------


@dataclass
class DocumentMetadata:
    """Schema for .auggd/document-metadata.json."""

    last_commit_hash: str = ""
    last_commit_summary: str = ""
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    documents_updated: list[str] = field(default_factory=list)
    known_gaps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict."""
        return {
            "last_commit_hash": self.last_commit_hash,
            "last_commit_summary": self.last_commit_summary,
            "generated_at": self.generated_at.isoformat(),
            "documents_updated": list(self.documents_updated),
            "known_gaps": list(self.known_gaps),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentMetadata":
        """Deserialize from a dict."""
        return cls(
            last_commit_hash=data.get("last_commit_hash", ""),
            last_commit_summary=data.get("last_commit_summary", ""),
            generated_at=datetime.fromisoformat(data["generated_at"])
            if "generated_at" in data
            else datetime.now(timezone.utc),
            documents_updated=list(data.get("documents_updated", [])),
            known_gaps=list(data.get("known_gaps", [])),
        )
