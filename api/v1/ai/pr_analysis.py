"""
Enhanced PR Analysis API endpoints with structured input/output.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.ai_controller import AIController
from app.schemas.requests.pr_analysis_requests import (
    AIROIRequest,
    CopilotInsightsRequest,
    NarrativeTimelineRequest,
    PRBlockerFlagsRequest,
    PRRiskFlagsRequest,
    PRSummaryRequest,
)
from app.schemas.responses.pr_analysis_responses import (
    AIROIResponse,
    CopilotInsightsResponse,
    NarrativeTimelineResponse,
    PRBlockerFlagsResponse,
    PRRiskFlagsResponse,
    PRSummaryResponse,
)
from core.database.session import get_session
from core.fastapi.dependencies.current_user import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pr-analysis", tags=["PR Analysis"])


@router.post("/risk-flags", response_model=PRRiskFlagsResponse)
async def analyze_pr_risk_flags(
    request: PRRiskFlagsRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Analyze PR for risk flags using structured output.

    Identifies risk tags like:
    - Critical File Change: touches sensitive modules
    - Large Blast Radius: affects many files/modules
    - Vulnerability Detected: security issues found
    - Missing Context: insufficient description
    - Rollback Risk: dangerous changes without rollback
    """
    try:
        controller = AIController(db_session)
        user_id = current_user.get("id") if current_user else None

        return await controller.analyze_pr_risk_flags(request=request, user_id=user_id)

    except Exception as e:
        logger.error(f"PR risk flags analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PR risk flags analysis failed: {str(e)}",
        )


@router.post("/blocker-flags", response_model=PRBlockerFlagsResponse)
async def analyze_pr_blocker_flags(
    request: PRBlockerFlagsRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Analyze PR for blocker flags using structured output.

    Identifies blocker tags like:
    - Awaiting Review: needs review attention
    - Review Stalemate: stuck in review process
    - Broken Build: CI/CD failures
    - Scope Creep: growing beyond original scope
    - Idle PR: no recent activity
    - Missing Tests: lacks proper test coverage
    """
    try:
        controller = AIController(db_session)
        user_id = current_user.get("id") if current_user else None

        return await controller.analyze_pr_blocker_flags(
            request=request, user_id=user_id
        )

    except Exception as e:
        logger.error(f"PR blocker flags analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PR blocker flags analysis failed: {str(e)}",
        )


@router.post("/copilot-insights", response_model=CopilotInsightsResponse)
async def generate_copilot_insights(
    request: CopilotInsightsRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Generate copilot insights using structured output.

    Converts engineering signals into manager-facing recommendations:
    - cycle_time_increase → identify blockers
    - after_hours_spike → check workload/rest
    - review_load_high → rebalance assignments
    - velocity_drop → examine scope
    - collab_silo → cross-team pairing
    """
    try:
        controller = AIController(db_session)
        user_id = current_user.get("id") if current_user else None

        return await controller.generate_copilot_insights(
            request=request, user_id=user_id
        )

    except Exception as e:
        logger.error(f"Copilot insights generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Copilot insights generation failed: {str(e)}",
        )


@router.post("/narrative-timeline", response_model=NarrativeTimelineResponse)
async def generate_narrative_timeline(
    request: NarrativeTimelineRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Generate narrative timeline using structured output.

    Converts daily engineering events into concise narrative:
    - Focuses on meaningful events (merges, blockings)
    - Includes relevant tags and context
    - Removes low-significance items
    - Creates human-readable timeline
    """
    try:
        controller = AIController(db_session)
        user_id = current_user.get("id") if current_user else None

        return await controller.generate_narrative_timeline(
            request=request, user_id=user_id
        )

    except Exception as e:
        logger.error(f"Narrative timeline generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Narrative timeline generation failed: {str(e)}",
        )


@router.post("/ai-roi", response_model=AIROIResponse)
async def analyze_ai_roi(
    request: AIROIRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Analyze AI ROI metrics using structured output.

    Interprets AI tool usage metrics and provides insights:
    - adoption_rate: how many users are using the tool
    - suggestion_acceptance_rate: how often suggestions are accepted
    - velocity_gain_pct: improvement in development speed
    - churn_rate: rate of users stopping usage

    Returns actionable insights and recommendations.
    """
    try:
        controller = AIController(db_session)
        user_id = current_user.get("id") if current_user else None

        return await controller.analyze_ai_roi(request=request, user_id=user_id)

    except Exception as e:
        logger.error(f"AI ROI analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI ROI analysis failed: {str(e)}",
        )


@router.post("/summary-enhanced", response_model=PRSummaryResponse)
async def generate_pr_summary_enhanced(
    request: PRSummaryRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Generate enhanced PR summary using structured output.

    Creates a plain-English one-liner summary of what the PR does:
    - Analyzes title, description, and changed files
    - Focuses on the main purpose and impact
    - Uses clear, non-technical language
    - Perfect for engineering managers and stakeholders
    """
    try:
        controller = AIController(db_session)
        user_id = current_user.get("id") if current_user else None

        return await controller.generate_pr_summary_enhanced(
            request=request, user_id=user_id
        )

    except Exception as e:
        logger.error(f"Enhanced PR summary generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhanced PR summary generation failed: {str(e)}",
        )
