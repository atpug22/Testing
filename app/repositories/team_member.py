from sqlalchemy import Select, select
from sqlalchemy.orm import joinedload

from app.models import TeamMember, User
from core.repository import BaseRepository


class TeamMemberRepository(BaseRepository[TeamMember]):
    """
    TeamMember repository provides all the database operations for the TeamMember model.
    """

    async def get_by_user_id(
        self, user_id: int, join_: set[str] | None = None
    ) -> TeamMember | None:
        """
        Get team member by user ID.

        :param user_id: User ID.
        :param join_: Join relations.
        :return: TeamMember.
        """
        query = self._query(join_)
        query = query.filter(TeamMember.user_id == user_id)

        if join_ is not None:
            return await self._all_unique(query)

        return await self._one_or_none(query)

    async def get_by_github_username(
        self, github_username: str, join_: set[str] | None = None
    ) -> TeamMember | None:
        """
        Get team member by GitHub username.

        :param github_username: GitHub username.
        :param join_: Join relations.
        :return: TeamMember.
        """
        query = self._query(join_)
        query = query.filter(TeamMember.github_username == github_username)

        if join_ is not None:
            return await self._all_unique(query)

        return await self._one_or_none(query)

    async def get_all_active_members(
        self, join_: set[str] | None = None
    ) -> list[TeamMember]:
        """
        Get all active team members (those with recent activity).

        :param join_: Join relations.
        :return: List of TeamMembers.
        """
        query = self._query(join_)
        # Could add filter for last_active_at if needed
        
        if join_ is not None:
            return await self._all_unique(query)

        return await self._all(query)

    def _join_user(self, query: Select) -> Select:
        """Join user."""
        return query.options(joinedload(TeamMember.user))

    def _join_events(self, query: Select) -> Select:
        """Join events."""
        return query.options(joinedload(TeamMember.events)).execution_options(
            contains_joined_collection=True
        )

