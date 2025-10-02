"""
Team Member Page API endpoints.
Implements all endpoints specified for the Team Member Page MVP.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.controllers.team_member import TeamMemberController
from app.models import TeamMember, User
from app.schemas.responses.team_member import (
    TeamMemberSummaryResponse,
    CopilotInsightsResponse,
    CopilotInsight,
    MetricsResponse,
    PRsResponse,
    TimelineResponse,
    TimelineEvent,
    UserBrief,
    PrimaryStatusResponse,
    KPITilesResponse,
    VelocityMetrics,
    WorkFocusMetrics,
    QualityMetrics,
    CollaborationMetrics,
)
from core.factory import Factory

router = APIRouter(prefix="/member")

# Optional auth for MVP demo - remove get_current_user dependency


@router.get("/{member_id}/summary", response_model=TeamMemberSummaryResponse)
async def get_member_summary(
    member_id: int,
    team_member_controller: TeamMemberController = Depends(
        Factory().get_team_member_controller
    ),
):
    """
    Get primary status + KPI tiles for a team member.
    
    This is the top section of the Team Member Page.
    """
    team_member = await team_member_controller.get_by_id(member_id, join_={"user"})
    
    if not team_member:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    # Get recent PRs for status calculation
    recent_prs = await team_member_controller.pr_repository.get_by_author(
        team_member.user_id
    )
    
    # Calculate primary status
    status, icon, reasoning = team_member_controller.calculate_primary_status(
        wip_count=team_member.wip_count,
        reviews_pending_count=team_member.reviews_pending_count,
        unresolved_comments=team_member.unresolved_discussions_count,
        recent_prs=recent_prs
    )
    
    # Compute KPI tiles
    kpi_tiles = await team_member_controller.compute_kpi_tiles(
        team_member.id, team_member.user_id
    )
    
    return TeamMemberSummaryResponse(
        user=UserBrief(
            id=team_member.user.id,
            username=team_member.user.username,
            email=team_member.user.email,
            avatar_url=team_member.github_avatar_url,
        ),
        primary_status=PrimaryStatusResponse(
            status=status,
            icon=icon,
            reasoning=reasoning,
            computed_at=datetime.now(timezone.utc)
        ),
        kpi_tiles=KPITilesResponse(**kpi_tiles)
    )


@router.get("/{member_id}/insights", response_model=CopilotInsightsResponse)
async def get_member_insights(
    member_id: int,
    team_member_controller: TeamMemberController = Depends(
        Factory().get_team_member_controller
    ),
):
    """
    Get Copilot Insights (Signal → Recommendation) for a team member.
    
    Returns recognition, risk, health, and collaboration insights.
    """
    team_member = await team_member_controller.get_by_id(member_id)
    
    if not team_member:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    # Get recent data
    recent_prs = await team_member_controller.pr_repository.get_by_author(
        team_member.user_id
    )
    recent_events = await team_member_controller.event_repository.get_recent_events(
        team_member.id, days=7
    )
    
    # Generate insights
    insights_data = team_member_controller.generate_copilot_insights(
        team_member, recent_prs, recent_events
    )
    
    insights = [CopilotInsight(**insight) for insight in insights_data]
    
    return CopilotInsightsResponse(
        insights=insights,
        generated_at=datetime.now(timezone.utc)
    )


@router.get("/{member_id}/metrics", response_model=MetricsResponse)
async def get_member_metrics(
    member_id: int,
    team_member_controller: TeamMemberController = Depends(
        Factory().get_team_member_controller
    ),
):
    """
    Get all quadrant metrics (Velocity, Work Focus, Quality, Collaboration).
    
    This powers the Analytics tab of the Team Member Page.
    """
    team_member = await team_member_controller.get_by_id(member_id)
    
    if not team_member:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    # Compute all quadrant metrics
    velocity = await team_member_controller.compute_velocity_metrics(team_member.user_id)
    work_focus = await team_member_controller.compute_work_focus_metrics(team_member.user_id)
    quality = await team_member_controller.compute_quality_metrics(team_member.user_id, team_member)
    collaboration = await team_member_controller.compute_collaboration_metrics(team_member)
    
    return MetricsResponse(
        velocity=VelocityMetrics(**velocity),
        work_focus=WorkFocusMetrics(**work_focus),
        quality=QualityMetrics(**quality),
        collaboration=CollaborationMetrics(**collaboration),
    )


@router.get("/{member_id}/prs", response_model=PRsResponse)
async def get_member_prs(
    member_id: int,
    team_member_controller: TeamMemberController = Depends(
        Factory().get_team_member_controller
    ),
):
    """
    Get all PRs for a team member (authored + assigned for review).
    
    Returns PR cards with flow blockers and risk flags.
    """
    team_member = await team_member_controller.get_by_id(member_id, join_={"user"})
    
    if not team_member:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    # Get authored PRs
    authored = await team_member_controller.pr_repository.get_by_author(
        team_member.user_id, join_={"author", "reviewers"}
    )
    
    # Get assigned reviews (TODO: query from pr_reviewers)
    assigned_for_review = []  # Placeholder
    
    return PRsResponse(
        authored=[],  # TODO: Convert to PRCardBrief
        assigned_for_review=[],
        total_authored=len(authored),
        total_assigned=len(assigned_for_review)
    )


@router.get("/{member_id}/timeline", response_model=TimelineResponse)
async def get_member_timeline(
    member_id: int,
    days: int = 7,
    team_member_controller: TeamMemberController = Depends(
        Factory().get_team_member_controller
    ),
):
    """
    Get timeline/narrative view of member's activity.
    
    Returns chronological activity feed for the Timeline tab.
    """
    team_member = await team_member_controller.get_by_id(member_id)
    
    if not team_member:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    # Get recent events
    events = await team_member_controller.event_repository.get_recent_events(
        team_member.id, days=days
    )
    
    # Map event types to icons
    icon_map = {
        "commit": "💻",
        "pr_opened": "🔄",
        "pr_merged": "✅",
        "review_submitted": "📝",
        "issue_closed": "✔️",
    }
    
    timeline_events = [
        TimelineEvent(
            id=event.id,
            type=event.event_type,
            timestamp=event.timestamp,
            title=event.title,
            description=event.description,
            icon=icon_map.get(event.event_type, "📌"),
            metadata=event.event_metadata or {}
        )
        for event in events
    ]
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    return TimelineResponse(
        events=timeline_events,
        date_range={
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        total_events=len(timeline_events)
    )

