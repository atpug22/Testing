from sqlalchemy import Select
from sqlalchemy.orm import joinedload

from app.models import Team, User
from core.repository import BaseRepository


class TeamRepository(BaseRepository[Team]):
    """
    Team repository provides all the database operations for the Team model.
    """

    async def get_by_name(
        self, name: str, join_: set[str] | None = None
    ) -> Team | None:
        """
        Get team by name.

        :param name: Team name.
        :param join_: Join relations.
        :return: Team.
        """
        query = self._query(join_)
        query = query.filter(Team.name == name)

        if join_ is not None:
            return await self._all_unique(query)

        return await self._one_or_none(query)

    async def get_teams_for_user(
        self, user_id: int, join_: set[str] | None = None
    ) -> list[Team]:
        """
        Get all teams where user is a member or manager.

        :param user_id: User ID.
        :param join_: Join relations.
        :return: List of teams.
        """
        query = self._query(join_)
        # Teams where user is a member or manager
        query = query.filter(
            (Team.members.any(User.id == user_id)) | (Team.manager_id == user_id)
        )

        if join_ is not None:
            return await self._all_unique(query)

        return await self._all(query)

    async def get_managed_teams(
        self, manager_id: int, join_: set[str] | None = None
    ) -> list[Team]:
        """
        Get all teams managed by a specific user.

        :param manager_id: Manager user ID.
        :param join_: Join relations.
        :return: List of teams.
        """
        query = self._query(join_)
        query = query.filter(Team.manager_id == manager_id)

        if join_ is not None:
            return await self._all_unique(query)

        return await self._all(query)

    async def add_member(self, team: Team, user: User) -> None:
        """
        Add a user to a team.

        :param team: Team instance.
        :param user: User instance.
        :return: None
        """
        if user not in team.members:
            team.members.append(user)

    async def remove_member(self, team: Team, user: User) -> None:
        """
        Remove a user from a team.

        :param team: Team instance.
        :param user: User instance.
        :return: None
        """
        if user in team.members:
            team.members.remove(user)

    def _join_manager(self, query: Select) -> Select:
        """
        Join manager.

        :param query: Query.
        :return: Query.
        """
        return query.options(joinedload(Team.manager))

    def _join_members(self, query: Select) -> Select:
        """
        Join members.

        :param query: Query.
        :return: Query.
        """
        return query.options(joinedload(Team.members)).execution_options(
            contains_joined_collection=True
        )

    def _join_pull_requests(self, query: Select) -> Select:
        """
        Join pull requests.

        :param query: Query.
        :return: Query.
        """
        return query.options(joinedload(Team.pull_requests)).execution_options(
            contains_joined_collection=True
        )

