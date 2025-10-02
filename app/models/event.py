from enum import Enum
from uuid import uuid4

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Unicode, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base
from core.database.mixins import TimestampMixin


class EventType(str, Enum):
    """Types of events for timeline"""
    COMMIT = "commit"
    PR_OPENED = "pr_opened"
    PR_MERGED = "pr_merged"
    PR_CLOSED = "pr_closed"
    REVIEW_SUBMITTED = "review_submitted"
    REVIEW_REQUESTED = "review_requested"
    COMMENT_ADDED = "comment_added"
    ISSUE_CLOSED = "issue_closed"
    ISSUE_OPENED = "issue_opened"
    DEPLOYMENT = "deployment"
    RELEASE = "release"


class Event(Base, TimestampMixin):
    """
    Timeline events for team members.
    Tracks all significant activities for the narrative view.
    """
    __tablename__ = "events"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    
    # Link to team member
    team_member_id = Column(
        BigInteger, 
        ForeignKey("team_members.id", ondelete="CASCADE"), 
        nullable=False
    )
    team_member = relationship(
        "TeamMember",
        back_populates="events",
        uselist=False,
        lazy="raise",
    )
    
    # Event details
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    title = Column(Unicode(500), nullable=False)
    description = Column(Unicode(1000), nullable=True)
    
    # Related entities
    pr_id = Column(BigInteger, ForeignKey("pull_requests.id", ondelete="SET NULL"), nullable=True)
    related_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Extensible metadata (renamed from 'metadata' which is reserved in SQLAlchemy)
    event_metadata = Column(JSON, nullable=True)  # {blast_radius, issue_id, deployment_env, etc.}

    __mapper_args__ = {"eager_defaults": True}

    def __repr__(self):
        return f"<Event(id={self.id}, type={self.event_type}, timestamp={self.timestamp})>"

