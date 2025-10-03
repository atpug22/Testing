from sqlalchemy import Select
from sqlalchemy.orm import joinedload

from app.models import Invitation
from app.models.invitation import InvitationStatus
from core.repository import BaseRepository


class InvitationRepository(BaseRepository[Invitation]):
    """
    Invitation repository provides all the database operations for the Invitation model.
    """

    async def get_by_email(
        self, email: str, join_: set[str] | None = None
    ) -> list[Invitation]:
        """
        Get all invitations for an email address.

        :param email: Email address.
        :param join_: Join relations.
        :return: List of invitations.
        """
        query = self._query(join_)
        query = query.filter(Invitation.email == email)

        return await self._all(query)

    async def get_pending_by_email(
        self, email: str, join_: set[str] | None = None
    ) -> list[Invitation]:
        """
        Get pending invitations for an email address.

        :param email: Email address.
        :param join_: Join relations.
        :return: List of pending invitations.
        """
        query = self._query(join_)
        query = query.filter(
            Invitation.email == email,
            Invitation.status == InvitationStatus.PENDING
        )

        return await self._all(query)

    async def get_by_organization(
        self, organization_id: int, join_: set[str] | None = None
    ) -> list[Invitation]:
        """
        Get all invitations for an organization.

        :param organization_id: Organization ID.
        :param join_: Join relations.
        :return: List of invitations.
        """
        query = self._query(join_)
        query = query.filter(Invitation.organization_id == organization_id)

        return await self._all(query)

    def _join_organization(self, query: Select) -> Select:
        """
        Join organization.

        :param query: Query.
        :return: Query.
        """
        return query.options(joinedload(Invitation.organization))

    def _join_invited_by(self, query: Select) -> Select:
        """
        Join invited_by user.

        :param query: Query.
        :return: Query.
        """
        return query.options(joinedload(Invitation.invited_by))

