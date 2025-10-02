from sqlalchemy import Select
from sqlalchemy.orm import joinedload

from app.models import User
from core.repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    User repository provides all the database operations for the User model.
    """

    async def get_by_username(
        self, username: str, join_: set[str] | None = None
    ) -> User | None:
        """
        Get user by username.

        :param username: Username.
        :param join_: Join relations.
        :return: User.
        """
        query = self._query(join_)
        query = query.filter(User.username == username)

        if join_ is not None:
            return await self._all_unique(query)

        return await self._one_or_none(query)

    async def get_by_email(
        self, email: str, join_: set[str] | None = None
    ) -> User | None:
        """
        Get user by email.

        :param email: Email.
        :param join_: Join relations.
        :return: User.
        """
        query = self._query(join_)
        query = query.filter(User.email == email)

        if join_ is not None:
            return await self._all_unique(query)
   
        return await self._one_or_none(query)

    def _join_tasks(self, query: Select) -> Select:
        """
        Join tasks.

        :param query: Query.
        :return: Query.
        """
        return query.options(joinedload(User.tasks)).execution_options(
            contains_joined_collection=True
        )

    def _join_teams(self, query: Select) -> Select:
        """
        Join teams (many-to-many relationship).

        :param query: Query.
        :return: Query.
        """
        return query.options(joinedload(User.teams)).execution_options(
            contains_joined_collection=True
        )

    def _join_managed_teams(self, query: Select) -> Select:
        """
        Join managed teams.

        :param query: Query.
        :return: Query.
        """
        return query.options(joinedload(User.managed_teams)).execution_options(
            contains_joined_collection=True
        )

    def _join_manager(self, query: Select) -> Select:
        """
        Join manager.

        :param query: Query.
        :return: Query.
        """
        return query.options(joinedload(User.manager))

    def _join_direct_reports(self, query: Select) -> Select:
        """
        Join direct reports.

        :param query: Query.
        :return: Query.
        """
        return query.options(joinedload(User.direct_reports)).execution_options(
            contains_joined_collection=True
        )
