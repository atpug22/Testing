from app.models import Invitation
from app.repositories import InvitationRepository
from core.controller import BaseController


class InvitationController(BaseController[Invitation]):
    def __init__(self, invitation_repository: InvitationRepository):
        super().__init__(model=Invitation, repository=invitation_repository)
        self.invitation_repository = invitation_repository

    async def get_by_email(self, email: str, join_: set[str] | None = None) -> list[Invitation]:
        return await self.invitation_repository.get_by_email(email, join_)

    async def get_pending_by_email(self, email: str, join_: set[str] | None = None) -> list[Invitation]:
        return await self.invitation_repository.get_pending_by_email(email, join_)

    async def get_by_organization(self, organization_id: int, join_: set[str] | None = None) -> list[Invitation]:
        return await self.invitation_repository.get_by_organization(organization_id, join_)

