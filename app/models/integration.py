from enum import Enum
from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Unicode, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base
from core.database.mixins import TimestampMixin


class IntegrationType(str, Enum):
    """Types of integrations"""
    GITHUB = "github"
    SLACK = "slack"
    JIRA = "jira"


class GitHubIntegration(Base, TimestampMixin):
    """GitHub integration for an organization"""
    __tablename__ = "github_integrations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    
    # Organization this integration belongs to
    organization_id = Column(
        BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    organization = relationship(
        "Organization",
        back_populates="github_integrations",
        lazy="raise",
    )

    # GitHub access token (should be encrypted in production)
    access_token = Column(Unicode(500), nullable=False)
    
    # GitHub user/org name
    github_owner = Column(Unicode(255), nullable=True)
    
    # Selected repositories to process (JSON array of repo names)
    selected_repos = Column(JSON, nullable=True, default=list)
    
    # Is this integration active
    is_active = Column(Boolean, default=True, nullable=False)

    __mapper_args__ = {"eager_defaults": True}


class SlackIntegration(Base, TimestampMixin):
    """Slack integration placeholder for an organization"""
    __tablename__ = "slack_integrations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    
    organization_id = Column(
        BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    
    webhook_url = Column(Unicode(500), nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)

    __mapper_args__ = {"eager_defaults": True}


class JiraIntegration(Base, TimestampMixin):
    """Jira integration placeholder for an organization"""
    __tablename__ = "jira_integrations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    
    organization_id = Column(
        BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    
    api_token = Column(Unicode(500), nullable=True)
    domain = Column(Unicode(255), nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)

    __mapper_args__ = {"eager_defaults": True}

