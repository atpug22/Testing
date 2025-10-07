from app.models import Team, User
from app.repositories import TeamRepository
from core.controller import BaseController


class TeamController(BaseController[Team]):
    def __init__(self, team_repository: TeamRepository):
        super().__init__(model=Team, repository=team_repository)
        self.team_repository = team_repository

    async def get_by_name(self, name: str, join_: set[str] | None = None) -> Team:
        """Get team by name."""
        return await self.team_repository.get_by_name(name, join_)

    async def get_teams_for_user(
        self, user_id: int, join_: set[str] | None = None
    ) -> list[Team]:
        """Get all teams where user is a member or manager."""
        return await self.team_repository.get_teams_for_user(user_id, join_)

    async def get_managed_teams(
        self, manager_id: int, join_: set[str] | None = None
    ) -> list[Team]:
        """Get all teams managed by a specific user."""
        return await self.team_repository.get_managed_teams(manager_id, join_)

    async def add_member(self, team: Team, user: User) -> None:
        """Add a user to a team."""
        await self.team_repository.add_member(team, user)

    async def remove_member(self, team: Team, user: User) -> None:
        """Remove a user from a team."""
        await self.team_repository.remove_member(team, user)
