from enum import Enum
from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, Column, Enum as SQLEnum, ForeignKey, Unicode
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.role import Role
from core.database import Base
from core.database.mixins import TimestampMixin
from core.security.access_control import Allow, Everyone, RolePrincipal, UserPrincipal


class UserPermission(Enum):
    CREATE = "create"
    READ = "read"
    EDIT = "edit"
    DELETE = "delete"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    email = Column(Unicode(255), nullable=False, unique=True)
    password = Column(Unicode(255), nullable=False)
    username = Column(Unicode(255), nullable=False, unique=True)
    is_admin = Column(Boolean, default=False)
    
    # GitHub integration fields
    github_id = Column(BigInteger, nullable=True, unique=True)
    github_avatar_url = Column(Unicode(500), nullable=True)
    github_access_token = Column(Unicode(500), nullable=True)  # Encrypted in production
    
    # Role for hierarchical access control
    role = Column(
        SQLEnum(Role, native_enum=False, length=50),
        nullable=False,
        default=Role.ENGINEER,
    )

    # Manager relationship (self-referential)
    manager_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    manager = relationship(
        "User",
        remote_side=[id],
        foreign_keys=[manager_id],
        back_populates="direct_reports",
        uselist=False,
        lazy="raise",
    )
    direct_reports = relationship(
        "User",
        back_populates="manager",
        foreign_keys=[manager_id],
        lazy="raise",
    )

    # Teams this user is a member of (many-to-many)
    teams = relationship(
        "Team",
        secondary="user_teams",
        back_populates="members",
        lazy="raise",
    )

    # Teams this user manages (one-to-many)
    managed_teams = relationship(
        "Team",
        back_populates="manager",
        foreign_keys="Team.manager_id",
        lazy="raise",
    )

    tasks = relationship(
        "Task", back_populates="author", lazy="raise", passive_deletes=True
    )
    
    # Pull requests created by this user
    pull_requests = relationship(
        "PullRequest",
        back_populates="author",
        lazy="raise",
        passive_deletes=True,
        foreign_keys="PullRequest.author_id",
    )
    
    # Pull requests assigned for review
    assigned_reviews = relationship(
        "PullRequest",
        secondary="pr_reviewers",
        back_populates="reviewers",
        lazy="raise",
    )
    
    # LogPose-specific profile (one-to-one)
    team_member_profile = relationship(
        "TeamMember",
        back_populates="user",
        uselist=False,
        lazy="raise",
        cascade="all, delete-orphan",
    )

    __mapper_args__ = {"eager_defaults": True}

    def __acl__(self):
        basic_permissions = [UserPermission.READ, UserPermission.CREATE]
        self_permissions = [
            UserPermission.READ,
            UserPermission.EDIT,
            UserPermission.CREATE,
        ]
        all_permissions = list(UserPermission)

        return [
            (Allow, Everyone, basic_permissions),
            (Allow, UserPrincipal(value=self.id), self_permissions),
            (Allow, RolePrincipal(value="admin"), all_permissions),
        ]
