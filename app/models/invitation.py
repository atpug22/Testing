from enum import Enum
from uuid import uuid4
from datetime import datetime, timedelta

from sqlalchemy import BigInteger, Column, ForeignKey, Unicode, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum

from core.database import Base
from core.database.mixins import TimestampMixin


class InvitationStatus(str, Enum):
    """Status of an invitation"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class Invitation(Base, TimestampMixin):
    """Invitation to join an organization"""
    __tablename__ = "invitations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    
    # Email of the person being invited
    email = Column(Unicode(255), nullable=False)
    
    # Organization they're being invited to
    organization_id = Column(
        BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    organization = relationship(
        "Organization",
        back_populates="invitations",
        lazy="raise",
    )
    
    # Role they'll have in the organization
    role = Column(Unicode(50), nullable=False, default="member")
    
    # Who invited them
    invited_by_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    invited_by = relationship(
        "User",
        foreign_keys=[invited_by_id],
        lazy="raise",
    )
    
    # Status and expiry
    status = Column(
        SQLEnum(InvitationStatus, native_enum=False, length=50),
        nullable=False,
        default=InvitationStatus.PENDING,
    )
    expires_at = Column(DateTime, nullable=False)
    
    # When they accepted/declined
    responded_at = Column(DateTime, nullable=True)

    __mapper_args__ = {"eager_defaults": True}

    @staticmethod
    def create_expiry(days=7):
        """Create an expiry datetime (default 7 days from now)"""
        return datetime.utcnow() + timedelta(days=days)

    def is_expired(self):
        """Check if the invitation has expired"""
        return datetime.utcnow() > self.expires_at

    def is_valid(self):
        """Check if the invitation is still valid"""
        return (
            self.status == InvitationStatus.PENDING
            and not self.is_expired()
        )

