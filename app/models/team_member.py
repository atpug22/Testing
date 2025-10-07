from uuid import uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Unicode,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.enums import PrimaryStatus, WorkFocusType
from core.database import Base
from core.database.mixins import TimestampMixin


class TeamMember(Base, TimestampMixin):
    """
    Extended profile for team members in LogPose.
    Contains all metrics, integration data, and analytics.
    Keeps the User model clean for auth/RBAC only.
    """

    __tablename__ = "team_members"
    __table_args__ = {"extend_existing": True}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)

    # One-to-one with User
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    user = relationship(
        "User",
        back_populates="team_member_profile",
        uselist=False,
        lazy="raise",
    )

    # === Team Member Page - Primary Status ===
    primary_status = Column(
        String(50),
        nullable=False,
        default=PrimaryStatus.BALANCED.value,
    )
    last_active_at = Column(DateTime(timezone=True), nullable=True)

    # === KPI Metrics (computed periodically) ===
    wip_count = Column(Integer, default=0)  # Work in Progress PRs
    reviews_pending_count = Column(Integer, default=0)  # Assigned reviews
    unresolved_discussions_count = Column(Integer, default=0)  # In Discussion threads

    # === Velocity Metrics ===
    merged_prs_last_30_days = Column(Integer, default=0)
    avg_cycle_time_hours = Column(Float, nullable=True)  # Time from open to merge
    avg_time_to_first_review_hours = Column(Float, nullable=True)

    # === Work Focus Metrics ===
    work_focus_distribution = Column(
        JSON, nullable=True
    )  # {feature: 60%, bug: 30%, chore: 10%}
    codebase_familiarity_percentage = Column(Float, default=0.0)  # % of modules touched

    # === Quality Metrics ===
    rework_rate_percentage = Column(Float, default=0.0)  # % of PRs needing rework
    revert_count = Column(Integer, default=0)  # Number of reverts in last 30 days
    churn_percentage = Column(Float, nullable=True)  # Code churn %

    # === Collaboration Metrics ===
    review_velocity_median_hours = Column(Float, nullable=True)  # Median time to review
    collaboration_reach = Column(Integer, default=0)  # # of teammates helped
    top_collaborators = Column(JSON, nullable=True)  # [{user_id, name, count}]

    # === GitHub Integration Data ===
    github_username = Column(Unicode(255), nullable=True)
    github_user_id = Column(BigInteger, nullable=True)
    github_avatar_url = Column(Unicode(500), nullable=True)
    github_profile_url = Column(Unicode(500), nullable=True)
    github_last_synced_at = Column(DateTime(timezone=True), nullable=True)

    # === Jira Integration Data (future) ===
    jira_user_id = Column(Unicode(255), nullable=True)
    jira_email = Column(Unicode(255), nullable=True)
    jira_last_synced_at = Column(DateTime(timezone=True), nullable=True)
    jira_metrics = Column(JSON, nullable=True)  # Extensible JSON for Jira metrics

    # === Confluence Integration Data (future) ===
    confluence_user_id = Column(Unicode(255), nullable=True)
    confluence_last_synced_at = Column(DateTime(timezone=True), nullable=True)
    confluence_metrics = Column(JSON, nullable=True)

    # === Slack/Chat Integration Data (future) ===
    slack_user_id = Column(Unicode(255), nullable=True)
    slack_last_synced_at = Column(DateTime(timezone=True), nullable=True)
    chat_activity_metrics = Column(JSON, nullable=True)

    # === Computed Insights (cached) ===
    copilot_insights = Column(
        JSON, nullable=True
    )  # [{type, signal, recommendation, priority}]
    risk_factors = Column(JSON, nullable=True)  # Current risk factors

    # === Timeline/Activity ===
    events = relationship(
        "Event",
        back_populates="team_member",
        lazy="raise",
        cascade="all, delete-orphan",
    )

    __mapper_args__ = {"eager_defaults": True}

    def __repr__(self):
        return f"<TeamMember(id={self.id}, user_id={self.user_id}, status={self.primary_status})>"
