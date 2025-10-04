from sqlalchemy import Select
from sqlalchemy.orm import joinedload

from app.models import GitHubIntegration
from core.repository import BaseRepository


class GitHubIntegrationRepository(BaseRepository[GitHubIntegration]):
    """
    GitHub integration repository provides all the database operations for the GitHubIntegration model.
    """

    async def get_by_organization(
        self, organization_id: int, join_: set[str] | None = None
    ) -> GitHubIntegration | None:
        """
        Get GitHub integration by organization ID.

        :param organization_id: Organization ID.
        :param join_: Join relations.
        :return: GitHub integration.
        """
        query = self._query(join_)
        query = query.filter(GitHubIntegration.organization_id == organization_id)

        if join_ is not None:
            return await self._all_unique(query)

        return await self._one_or_none(query)

    async def get_active_by_organization(
        self, organization_id: int, join_: set[str] | None = None
    ) -> GitHubIntegration | None:
        """
        Get active GitHub integration by organization ID.

        :param organization_id: Organization ID.
        :param join_: Join relations.
        :return: GitHub integration.
        """
        query = self._query(join_)
        query = query.filter(
            GitHubIntegration.organization_id == organization_id,
            GitHubIntegration.is_active == True
        )

        if join_ is not None:
            return await self._all_unique(query)

        return await self._one_or_none(query)

    def _join_organization(self, query: Select) -> Select:
        """
        Join organization.

        :param query: Query.
        :return: Query.
        """
        return query.options(joinedload(GitHubIntegration.organization))

