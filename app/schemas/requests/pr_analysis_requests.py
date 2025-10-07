"""
Pydantic schemas for PR analysis requests with structured input/output.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class PRRiskFlagsRequest(BaseModel):
    """Request schema for PR Risk Flags analysis."""

    title: str = Field(..., description="PR title")
    description: str = Field(..., description="PR description")
    files_changed: List[str] = Field(...,
                                     description="List of file paths changed")
    lines_added: int = Field(..., description="Number of lines added")
    lines_deleted: int = Field(..., description="Number of lines deleted")
    diff_count: int = Field(..., description="Number of files modified")
    vulnerability_signals: Optional[List[str]] = Field(
        default=None,
        description="Detected vulnerability signals like sql_injection, unsafe_deserialization",
    )


class PRBlockerFlagsRequest(BaseModel):
    """Request schema for PR Blocker Flags analysis."""

    days_open: int = Field(..., description="Days since PR was opened")
    review_requests: int = Field(..., description="Number of review requests")
    comments_unresolved: int = Field(...,
                                     description="Number of unresolved comments")
    ci_status: Literal["passing", "failing", "pending"] = Field(
        ..., description="CI status"
    )
    last_update_days: int = Field(..., description="Days since last update")
    lines_changed: int = Field(..., description="Total lines changed")
    tests_modified: bool = Field(...,
                                 description="Whether tests were modified")


class CopilotInsightsRequest(BaseModel):
    """Request schema for Copilot Insights analysis."""

    signal: str = Field(
        ..., description="Signal type like cycle_time_increase, after_hours_spike"
    )
    context: Dict[str, Any] = Field(...,
                                    description="Context data for the signal")


class NarrativeTimelineRequest(BaseModel):
    """Request schema for Narrative Timeline generation."""

    daily_events: List[Dict[str, Any]] = Field(
        ..., description="Daily events with day and actions"
    )
    key_tags: Dict[str, str] = Field(...,
                                     description="Key tags for PRs or events")


class AIROIRequest(BaseModel):
    """Request schema for AI ROI analysis."""

    adoption_rate: float = Field(..., ge=0.0, le=1.0,
                                 description="Adoption rate (0-1)")
    suggestion_acceptance_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Acceptance rate (0-1)"
    )
    velocity_gain_pct: float = Field(...,
                                     description="Velocity gain percentage")
    churn_rate: float = Field(..., ge=0.0, le=1.0,
                              description="Churn rate (0-1)")


class PRSummaryRequest(BaseModel):
    """Request schema for PR Summary analysis."""

    title: str = Field(..., description="PR title")
    description: str = Field(..., description="PR description")
    files_changed: List[str] = Field(..., description="List of changed files")
