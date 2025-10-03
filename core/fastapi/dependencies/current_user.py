from fastapi import Depends, Request, HTTPException, status

from app.controllers.user import UserController
from core.factory import Factory
from core.exceptions import NotFoundException


async def get_current_user(
    request: Request,
    user_controller: UserController = Depends(Factory().get_user_controller),
):
    try:
        return await user_controller.get_by_id(request.user.id)
    except NotFoundException:
        # User was authenticated but doesn't exist in database anymore
        # This could happen if user was deleted or session/token is stale
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
