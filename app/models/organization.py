from enum import Enum
from uuid import uuid4

from sqlalchemy import BigInteger, Column, ForeignKey, String, Table, Unicode
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum

from core.database import Base
from core.database.mixins import TimestampMixin


class OrganizationRole(str, Enum):
    """Roles within an organization"""
    ADMIN = "admin"
    MEMBER = "member"


class OrganizationPermission(Enum):
    CREATE = "create"
    READ = "read"
    EDIT = "edit"
    DELETE = "delete"
    MANAGE_MEMBERS = "manage_members"
    MANAGE_INTEGRATIONS = "manage_integrations"


# Association table for many-to-many relationship between users and organizations
organization_members = Table(
    "organization_members",
    Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("organization_id", BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True),
    Column("role", SQLEnum(OrganizationRole, native_enum=False, length=50), nullable=False, default=OrganizationRole.MEMBER),
)


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    name = Column(Unicode(255), nullable=False, unique=True)
    description = Column(Unicode(500), nullable=True)

    # Owner of the organization
    owner_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    owner = relationship(
        "User",
        foreign_keys=[owner_id],
        back_populates="owned_organizations",
        uselist=False,
        lazy="raise",
    )

    # Organization members (many-to-many)
    members = relationship(
        "User",
        secondary=organization_members,
        back_populates="organizations",
        lazy="raise",
    )

    # Integrations for this organization
    github_integrations = relationship(
        "GitHubIntegration",
        back_populates="organization",
        lazy="raise",
        cascade="all, delete-orphan",
    )

    # Invitations for this organization
    invitations = relationship(
        "Invitation",
        back_populates="organization",
        lazy="raise",
        cascade="all, delete-orphan",
    )

    __mapper_args__ = {"eager_defaults": True}

