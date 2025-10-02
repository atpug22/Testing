from app.models import PullRequest
from app.repositories import PullRequestRepository
from core.controller import BaseController


class PullRequestController(BaseController[PullRequest]):
    def __init__(self, pull_request_repository: PullRequestRepository):
        super().__init__(model=PullRequest, repository=pull_request_repository)
        self.pull_request_repository = pull_request_repository

    async def get_by_github_id(
        self, github_pr_id: int, join_: set[str] | None = None
    ) -> PullRequest:
        """Get pull request by GitHub PR ID."""
        return await self.pull_request_repository.get_by_github_id(github_pr_id, join_)

    async def get_by_author(
        self, author_id: int, join_: set[str] | None = None
    ) -> list[PullRequest]:
        """Get all pull requests by author."""
        return await self.pull_request_repository.get_by_author(author_id, join_)

    async def get_by_team(
        self, team_id: int, join_: set[str] | None = None
    ) -> list[PullRequest]:
        """Get all pull requests for a team."""
        return await self.pull_request_repository.get_by_team(team_id, join_)

    async def get_by_status(
        self, status: str, join_: set[str] | None = None
    ) -> list[PullRequest]:
        """Get all pull requests by status."""
        return await self.pull_request_repository.get_by_status(status, join_)

