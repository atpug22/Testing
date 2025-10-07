"""
Pydantic schemas for PR analysis responses with structured output.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class RiskFlagDetail(BaseModel):
    """Detailed risk flag with explanation."""

    tag: str = Field(..., description="Risk tag name")
    reason: str = Field(...,
                        description="Detailed explanation of why this risk applies")
    evidence: Optional[str] = Field(
        None, description="Specific evidence (file names, metrics, etc.)")


class BlockerFlagDetail(BaseModel):
    """Detailed blocker flag with explanation."""

    tag: str = Field(..., description="Blocker tag name")
    reason: str = Field(...,
                        description="Detailed explanation of why this blocker applies")
    evidence: Optional[str] = Field(
        None, description="Specific evidence (reviewers, metrics, etc.)")


class PRRiskFlagsResponse(BaseModel):
    """Response schema for PR Risk Flags analysis."""

    risks: List[RiskFlagDetail] = Field(
        ...,
        description="List of risk flags with detailed explanations",
    )


class PRBlockerFlagsResponse(BaseModel):
    """Response schema for PR Blocker Flags analysis."""

    blockers: List[BlockerFlagDetail] = Field(
        ...,
        description="List of blocker flags with detailed explanations",
    )


class CopilotInsightsResponse(BaseModel):
    """Response schema for Copilot Insights analysis."""

    signal: str = Field(..., description="The input signal")
    recommendation: str = Field(...,
                                description="Manager-facing recommendation")


class NarrativeTimelineResponse(BaseModel):
    """Response schema for Narrative Timeline generation."""

    timeline: List[str] = Field(...,
                                description="Narrative timeline of daily events")


class AIROIResponse(BaseModel):
    """Response schema for AI ROI analysis."""

    insights: List[str] = Field(...,
                                description="List of insights from metrics")
    recommendation: str = Field(..., description="Overall recommendation")


class PRSummaryResponse(BaseModel):
    """Response schema for PR Summary analysis."""

    summary: str = Field(..., description="2-3 line summary of PR changes")
    confidence: str = Field(
        ..., description="Confidence level: high/medium/low based on available information")
    limitations: Optional[str] = Field(
        None, description="Any limitations in analysis (missing description, unclear changes, etc.)")
