from enum import Enum
from uuid import uuid4

from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Integer, String, Table, Unicode, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.models.enums import PrimaryStatus, FlowBlocker, RiskFlag
from core.database import Base
from core.database.mixins import TimestampMixin
from core.security.access_control import Allow, RolePrincipal, TeamPrincipal, UserPrincipal


class PRPermission(Enum):
    CREATE = "create"
    READ = "read"
    EDIT = "edit"
    DELETE = "delete"


class PRStatus(str, Enum):
    """PR status"""
    OPEN = "open"
    MERGED = "merged"
    CLOSED = "closed"


# Association table for PR reviewers (many-to-many)
pr_reviewers = Table(
    "pr_reviewers",
    Base.metadata,
    Column("pr_id", BigInteger, ForeignKey("pull_requests.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class PullRequest(Base, TimestampMixin):
    __tablename__ = "pull_requests"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    
    # GitHub PR information
    github_pr_id = Column(BigInteger, nullable=False, unique=True)
    title = Column(Unicode(500), nullable=False)
    description = Column(Unicode(2000), nullable=True)
    github_url = Column(Unicode(500), nullable=True)
    status = Column(String(50), nullable=False, default=PRStatus.OPEN)  # open, merged, closed
    
    # PR metadata
    labels = Column(ARRAY(String), nullable=True)  # List of labels
    unresolved_comments = Column(Integer, default=0)
    lines_changed = Column(Integer, default=0)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    changed_files = Column(Integer, default=0)
    
    # Timestamps
    merged_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    first_review_at = Column(DateTime(timezone=True), nullable=True)
    first_commit_at = Column(DateTime(timezone=True), nullable=True)
    
    # Flow blockers and risk flags (stored as JSON arrays)
    flow_blockers = Column(ARRAY(String), nullable=True)
    risk_flags = Column(ARRAY(String), nullable=True)
    
    # Author of the PR
    author_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    author = relationship(
        "User",
        back_populates="pull_requests",
        uselist=False,
        lazy="raise",
    )
    
    # Team associated with this PR
    team_id = Column(
        BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), nullable=True
    )
    team = relationship(
        "Team",
        back_populates="pull_requests",
        uselist=False,
        lazy="raise",
    )
    
    # Reviewers (many-to-many)
    reviewers = relationship(
        "User",
        secondary="pr_reviewers",
        back_populates="assigned_reviews",
        lazy="raise",
    )

    __mapper_args__ = {"eager_defaults": True}

    def __acl__(self):
        """
        Access control list for Pull Requests.
        
        Rules:
        - CTO can access all PRs
        - Engineering Heads and Managers can access all PRs in their teams
        - Engineers can only access their own PRs
        - Admins have full access
        """
        self_permissions = [
            PRPermission.READ,
            PRPermission.EDIT,
            PRPermission.DELETE,
        ]
        team_read_permissions = [PRPermission.READ]
        all_permissions = list(PRPermission)

        acl = [
            # PR author can manage their own PR
            (Allow, UserPrincipal(self.author_id), self_permissions),
            # Admin and CTO have full access
            (Allow, RolePrincipal("admin"), all_permissions),
            (Allow, RolePrincipal("cto"), all_permissions),
            # Team managers can view all PRs in their team
            (Allow, TeamPrincipal(self.team_id), team_read_permissions),
        ]

        return acl

