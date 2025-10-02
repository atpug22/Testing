from http import HTTPStatus

from fastapi import Depends, Request

from app.controllers.user import UserController
from core.exceptions import CustomException
from core.factory import Factory
from core.security.access_control import (
    AccessControl,
    Authenticated,
    Everyone,
    RolePrincipal,
    TeamPrincipal,
    UserPrincipal,
)


class InsufficientPermissionsException(CustomException):
    code = HTTPStatus.FORBIDDEN
    error_code = HTTPStatus.FORBIDDEN
    message = "Insufficient permissions"


async def get_user_principals(
    request: Request,
    user_controller: UserController = Depends(Factory().get_user_controller),
) -> list:
    user_id = request.user.id
    principals = [Everyone]

    if not user_id:
        return principals

    # Load user with teams and managed_teams relationships
    user = await user_controller.get_by_id(
        id_=user_id, join_={"teams", "managed_teams"}
    )

    principals.append(Authenticated)
    principals.append(UserPrincipal(user.id))

    # Add role-based principal
    if user.role:
        principals.append(RolePrincipal(user.role.value))

    # Legacy admin check
    if user.is_admin:
        principals.append(RolePrincipal("admin"))

    # Add team principals for all teams the user is a member of
    if hasattr(user, "teams") and user.teams:
        for team in user.teams:
            principals.append(TeamPrincipal(team.id))

    # Add team principals for all teams the user manages
    if hasattr(user, "managed_teams") and user.managed_teams:
        for team in user.managed_teams:
            principals.append(TeamPrincipal(team.id))

    return principals


Permissions = AccessControl(
    user_principals_getter=get_user_principals,
    permission_exception=InsufficientPermissionsException,
)
