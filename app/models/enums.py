"""
Shared enums for LogPose models.
"""

from enum import Enum


class PrimaryStatus(str, Enum):
    """Primary status of an engineer (LogPose domain)"""

    BALANCED = "balanced"
    OVERLOADED = "overloaded"
    BLOCKED = "blocked"
    ONBOARDING = "onboarding"
    FIREFIGHTING = "firefighting"
    MENTORING = "mentoring"


class FlowBlocker(str, Enum):
    """Flow blockers for PRs as defined in LogPose domain."""

    AWAITING_REVIEW = "awaiting_review"
    REVIEW_STALEMATE = "review_stalemate"
    BROKEN_BUILD = "broken_build"
    IDLE_PR = "idle_pr"
    MISSING_TESTS = "missing_tests"


class RiskFlag(str, Enum):
    """Risk flags for PRs as defined in LogPose domain."""

    CRITICAL_FILE_CHANGE = "critical_file_change"
    LARGE_BLAST_RADIUS = "large_blast_radius"
    SCOPE_CREEP_DETECTED = "scope_creep_detected"
    MISSING_CONTEXT = "missing_context"
    VULNERABILITY_DETECTED = "vulnerability_detected"
    ROLLBACK_RISK = "rollback_risk"


class WorkFocusType(str, Enum):
    """Type of work focus"""

    FEATURE = "feature"
    BUG = "bug"
    CHORE = "chore"
    REFACTOR = "refactor"


class EventType(str, Enum):
    """Types of events in the timeline"""

    PR_OPENED = "pr_opened"
    PR_MERGED = "pr_merged"
    PR_CLOSED = "pr_closed"
    COMMIT = "commit"
    REVIEW_SUBMITTED = "review_submitted"
    ISSUE_CLOSED = "issue_closed"
    COMMENT_ADDED = "comment_added"
