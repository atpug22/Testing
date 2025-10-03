from sqlalchemy import Select
from sqlalchemy.orm import joinedload

from app.models import Organization
from core.repository import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """
    Organization repository provides all the database operations for the Organization model.
    """

    async def get_by_name(
        self, name: str, join_: set[str] | None = None
    ) -> Organization | None:
        """
        Get organization by name.

        :param name: Organization name.
        :param join_: Join relations.
        :return: Organization.
        """
        query = self._query(join_)
        query = query.filter(Organization.name == name)

        if join_ is not None:
            return await self._all_unique(query)

        return await self._one_or_none(query)

    async def get_by_user(
        self, user_id: int, join_: set[str] | None = None
    ) -> list[Organization]:
        """
        Get organizations where user is a member.

        :param user_id: User ID.
        :param join_: Join relations.
        :return: List of organizations.
        """
        query = self._query(join_)
        query = query.join(Organization.members).filter(
            Organization.members.any(id=user_id)
        )

        return await self._all(query)

    def _join_owner(self, query: Select) -> Select:
        """
        Join owner.

        :param query: Query.
        :return: Query.
        """
        return query.options(joinedload(Organization.owner))

    def _join_members(self, query: Select) -> Select:
        """
        Join members.

        :param query: Query.
        :return: Query.
        """
        return query.options(joinedload(Organization.members)).execution_options(
            contains_joined_collection=True
        )

    def _join_github_integrations(self, query: Select) -> Select:
        """
        Join GitHub integrations.

        :param query: Query.
        :return: Query.
        """
        return query.options(joinedload(Organization.github_integrations)).execution_options(
            contains_joined_collection=True
        )

