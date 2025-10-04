from functools import partial

from fastapi import Depends

from app.controllers import (
    AuthController,
    PullRequestController,
    TaskController,
    TeamController,
    TeamMemberController,
    UserController,
)
from app.controllers.integration import GitHubIntegrationController
from app.controllers.invitation import InvitationController
from app.controllers.organization import OrganizationController
from app.models import Event, PullRequest, Task, Team, TeamMember, User, Organization, GitHubIntegration, Invitation
from app.repositories import (
    EventRepository,
    GitHubIntegrationRepository,
    InvitationRepository,
    OrganizationRepository,
    PullRequestRepository,
    TaskRepository,
    TeamRepository,
    TeamMemberRepository,
    UserRepository,
)
from core.database import get_session


class Factory:
    """
    This is the factory container that will instantiate all the controllers and
    repositories which can be accessed by the rest of the application.
    """

    # Repositories
    task_repository = partial(TaskRepository, Task)
    user_repository = partial(UserRepository, User)
    team_repository = partial(TeamRepository, Team)
    pull_request_repository = partial(PullRequestRepository, PullRequest)
    team_member_repository = partial(TeamMemberRepository, TeamMember)
    event_repository = partial(EventRepository, Event)
    organization_repository = partial(OrganizationRepository, Organization)
    integration_repository = partial(GitHubIntegrationRepository, GitHubIntegration)
    invitation_repository = partial(InvitationRepository, Invitation)

    def get_user_controller(self, db_session=Depends(get_session)):
        return UserController(
            user_repository=self.user_repository(db_session=db_session)
        )

    def get_task_controller(self, db_session=Depends(get_session)):
        return TaskController(
            task_repository=self.task_repository(db_session=db_session)
        )

    def get_auth_controller(self, db_session=Depends(get_session)):
        return AuthController(
            user_repository=self.user_repository(db_session=db_session),
        )

    def get_team_controller(self, db_session=Depends(get_session)):
        return TeamController(
            team_repository=self.team_repository(db_session=db_session)
        )

    def get_pull_request_controller(self, db_session=Depends(get_session)):
        return PullRequestController(
            pull_request_repository=self.pull_request_repository(db_session=db_session)
        )

    def get_team_member_controller(self, db_session=Depends(get_session)):
        return TeamMemberController(
            team_member_repository=self.team_member_repository(db_session=db_session),
            event_repository=self.event_repository(db_session=db_session),
            pr_repository=self.pull_request_repository(db_session=db_session),
        )

    def get_organization_controller(self, db_session=Depends(get_session)):
        return OrganizationController(
            organization_repository=self.organization_repository(db_session=db_session)
        )

    def get_integration_controller(self, db_session=Depends(get_session)):
        return GitHubIntegrationController(
            integration_repository=self.integration_repository(db_session=db_session)
        )

    def get_invitation_controller(self, db_session=Depends(get_session)):
        return InvitationController(
            invitation_repository=self.invitation_repository(db_session=db_session)
        )
