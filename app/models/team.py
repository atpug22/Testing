from enum import Enum
from uuid import uuid4

from sqlalchemy import BigInteger, Column, ForeignKey, String, Table, Unicode
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base
from core.database.mixins import TimestampMixin
from core.security.access_control import (
    Allow,
    Authenticated,
    RolePrincipal,
    UserPrincipal,
)


class TeamPermission(Enum):
    CREATE = "create"
    READ = "read"
    EDIT = "edit"
    DELETE = "delete"
    MANAGE_MEMBERS = "manage_members"


# Association table for many-to-many relationship between users and teams
user_teams = Table(
    "user_teams",
    Base.metadata,
    Column(
        "user_id",
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "team_id",
        BigInteger,
        ForeignKey("teams.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Team(Base, TimestampMixin):
    __tablename__ = "teams"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    name = Column(Unicode(255), nullable=False, unique=True)
    description = Column(Unicode(500), nullable=True)

    # Manager of this team (Engineering Manager)
    manager_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    manager = relationship(
        "User",
        foreign_keys=[manager_id],
        back_populates="managed_teams",
        uselist=False,
        lazy="raise",
    )

    # Team members (many-to-many)
    members = relationship(
        "User",
        secondary=user_teams,
        back_populates="teams",
        lazy="raise",
    )

    # Pull requests associated with this team
    pull_requests = relationship(
        "PullRequest",
        back_populates="team",
        lazy="raise",
        passive_deletes=True,
    )

    __mapper_args__ = {"eager_defaults": True}

    def __acl__(self):
        basic_permissions = [TeamPermission.READ]
        manager_permissions = [
            TeamPermission.READ,
            TeamPermission.EDIT,
            TeamPermission.MANAGE_MEMBERS,
        ]
        all_permissions = list(TeamPermission)

        acl = [
            (Allow, Authenticated, basic_permissions),
            (Allow, RolePrincipal("admin"), all_permissions),
            (Allow, RolePrincipal("cto"), all_permissions),
            (Allow, RolePrincipal("engineering_head"), all_permissions),
        ]

        # Team manager has special permissions
        if self.manager_id:
            acl.append((Allow, UserPrincipal(self.manager_id), manager_permissions))

        return acl
