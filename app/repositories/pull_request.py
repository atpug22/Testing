from sqlalchemy import Select
from sqlalchemy.orm import joinedload

from app.models import PullRequest
from core.repository import BaseRepository


class PullRequestRepository(BaseRepository[PullRequest]):
    """
    PullRequest repository provides all the database operations for the PullRequest model.
    """

    async def get_by_github_id(
        self, github_pr_id: int, join_: set[str] | None = None
    ) -> PullRequest | None:
        """
        Get pull request by GitHub PR ID.

        :param github_pr_id: GitHub PR ID.
        :param join_: Join relations.
        :return: PullRequest.
        """
        query = self._query(join_)
        query = query.filter(PullRequest.github_pr_id == github_pr_id)

        if join_ is not None:
            return await self._all_unique(query)

        return await self._one_or_none(query)

    async def get_by_author(
        self, author_id: int, join_: set[str] | None = None
    ) -> list[PullRequest]:
        """
        Get all pull requests by author.

        :param author_id: Author user ID.
        :param join_: Join relations.
        :return: List of pull requests.
        """
        query = self._query(join_)
        query = query.filter(PullRequest.author_id == author_id)

        if join_ is not None:
            return await self._all_unique(query)

        return await self._all(query)

    async def get_by_team(
        self, team_id: int, join_: set[str] | None = None
    ) -> list[PullRequest]:
        """
        Get all pull requests for a team.

        :param team_id: Team ID.
        :param join_: Join relations.
        :return: List of pull requests.
        """
        query = self._query(join_)
        query = query.filter(PullRequest.team_id == team_id)

        if join_ is not None:
            return await self._all_unique(query)

        return await self._all(query)

    async def get_by_status(
        self, status: str, join_: set[str] | None = None
    ) -> list[PullRequest]:
        """
        Get all pull requests by status.

        :param status: PR status (open, closed, merged).
        :param join_: Join relations.
        :return: List of pull requests.
        """
        query = self._query(join_)
        query = query.filter(PullRequest.status == status)

        if join_ is not None:
            return await self._all_unique(query)

        return await self._all(query)

    def _join_author(self, query: Select) -> Select:
        """
        Join author.

        :param query: Query.
        :return: Query.
        """
        return query.options(joinedload(PullRequest.author))

    def _join_team(self, query: Select) -> Select:
        """
        Join team.

        :param query: Query.
        :return: Query.
        """
        return query.options(joinedload(PullRequest.team))

