from app.models import Organization
from app.repositories import OrganizationRepository
from core.controller import BaseController


class OrganizationController(BaseController[Organization]):
    def __init__(self, organization_repository: OrganizationRepository):
        super().__init__(model=Organization, repository=organization_repository)
        self.organization_repository = organization_repository

    async def get_by_name(self, name: str, join_: set[str] | None = None) -> Organization | None:
        return await self.organization_repository.get_by_name(name, join_)

    async def get_by_user(self, user_id: int, join_: set[str] | None = None) -> list[Organization]:
        return await self.organization_repository.get_by_user(user_id, join_)

