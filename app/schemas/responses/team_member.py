from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


# === User/Author schemas ===
class UserBrief(BaseModel):
    """Brief user information"""
    id: int
    username: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


# === KPI Tile Schemas ===
class KPITile(BaseModel):
    """KPI tile with hover details"""
    label: str
    value: int
    trend: Optional[str] = None  # "up", "down", "stable"
    hover_details: Optional[List[str]] = []  # Hover content


class KPITilesResponse(BaseModel):
    """All KPI tiles for the dashboard"""
    wip: KPITile
    reviews: KPITile
    in_discussion: KPITile
    last_active: Dict[str, Any]  # {label, value, timestamp}


# === Primary Status ===
class PrimaryStatusResponse(BaseModel):
    """Primary status with icon and reasoning"""
    status: str  # balanced, overloaded, blocked, etc.
    icon: str  # 🟢, 🟠, 🔴, 🚀, 🔥, 🧑‍🏫
    reasoning: str
    computed_at: datetime


# === Copilot Insights ===
class CopilotInsight(BaseModel):
    """A single copilot insight"""
    type: str  # recognition, risk, health, collaboration
    signal: str  # The observation
    recommendation: str  # The action
    priority: str  # high, medium, low
    icon: str  # 🎉, ⚠️, 🚩, 🤝
    pr_ids: Optional[List[int]] = []  # Related PRs if any


class CopilotInsightsResponse(BaseModel):
    """All copilot insights"""
    insights: List[CopilotInsight]
    generated_at: datetime


# === Metrics Quadrants ===
class VelocityMetrics(BaseModel):
    """Velocity quadrant metrics"""
    merged_prs_by_week: List[Dict[str, Any]]  # [{week, count}]
    avg_cycle_time_trend: List[Dict[str, Any]]  # [{date, hours}]
    total_merged_last_30_days: int
    avg_cycle_time_hours: Optional[float]


class WorkFocusMetrics(BaseModel):
    """Work focus quadrant metrics"""
    distribution: Dict[str, float]  # {feature: 60%, bug: 30%, chore: 10%}
    codebase_familiarity_percentage: float
    new_modules_touched: int


class QualityMetrics(BaseModel):
    """Quality quadrant metrics"""
    rework_rate_percentage: float
    rework_trend: str  # "up", "down", "stable"
    revert_count: int
    revert_trend: str
    churn_percentage: Optional[float]


class CollaborationMetrics(BaseModel):
    """Collaboration quadrant metrics"""
    review_velocity_median_hours: Optional[float]
    collaboration_reach: int  # Number of teammates helped
    top_collaborators: List[Dict[str, Any]]  # [{user_id, name, avatar, count}]


class MetricsResponse(BaseModel):
    """All quadrant metrics"""
    velocity: VelocityMetrics
    work_focus: WorkFocusMetrics
    quality: QualityMetrics
    collaboration: CollaborationMetrics


# === PR Card Schemas ===
class PRCardBrief(BaseModel):
    """Brief PR information for cards"""
    id: int
    number: int
    title: str
    status: str  # open, merged, closed
    author: UserBrief
    created_at: datetime
    merged_at: Optional[datetime] = None
    labels: List[str] = []
    flow_blockers: List[str] = []  # broken_build, awaiting_review, etc.
    risk_flags: List[str] = []  # critical_file, large_blast_radius, etc.
    unresolved_comments: int = 0
    reviewers: List[UserBrief] = []
    assigned_days_ago: Optional[int] = None  # For review assignments

    class Config:
        from_attributes = True


class PRsResponse(BaseModel):
    """List of PRs for a team member"""
    authored: List[PRCardBrief]
    assigned_for_review: List[PRCardBrief]
    total_authored: int
    total_assigned: int


# === Timeline Events ===
class TimelineEvent(BaseModel):
    """A single timeline event"""
    id: int
    type: str  # commit, pr_opened, review_submitted, etc.
    timestamp: datetime
    title: str
    description: Optional[str] = None
    icon: str  # 💻, 🔄, ✅, 📝, etc.
    metadata: Optional[Dict[str, Any]] = {}

    class Config:
        from_attributes = True


class TimelineResponse(BaseModel):
    """Timeline/narrative view"""
    events: List[TimelineEvent]
    date_range: Dict[str, str]  # {start, end}
    total_events: int


# === Summary Response (combines multiple sections) ===
class TeamMemberSummaryResponse(BaseModel):
    """Complete summary for Team Member Page"""
    user: UserBrief
    primary_status: PrimaryStatusResponse
    kpi_tiles: KPITilesResponse


# === Full Team Member Profile ===
class TeamMemberProfileResponse(BaseModel):
    """Complete team member profile"""
    id: int
    user_id: int
    user: UserBrief
    primary_status: str
    last_active_at: Optional[datetime]
    github_username: Optional[str]
    github_avatar_url: Optional[str]
    
    # Computed metrics
    wip_count: int
    reviews_pending_count: int
    unresolved_discussions_count: int
    
    class Config:
        from_attributes = True

