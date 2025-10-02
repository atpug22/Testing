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
from app.models import Event, PullRequest, Task, Team, TeamMember, User
from app.repositories import (
    EventRepository,
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
