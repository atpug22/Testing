from app.models import GitHubIntegration
from app.repositories import GitHubIntegrationRepository
from core.controller import BaseController


class GitHubIntegrationController(BaseController[GitHubIntegration]):
    def __init__(self, integration_repository: GitHubIntegrationRepository):
        super().__init__(model=GitHubIntegration, repository=integration_repository)
        self.integration_repository = integration_repository

    async def get_by_organization(
        self, organization_id: int, join_: set[str] | None = None
    ) -> GitHubIntegration | None:
        return await self.integration_repository.get_by_organization(organization_id, join_)

    async def get_active_by_organization(
        self, organization_id: int, join_: set[str] | None = None
    ) -> GitHubIntegration | None:
        return await self.integration_repository.get_active_by_organization(organization_id, join_)

