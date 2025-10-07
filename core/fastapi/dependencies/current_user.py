from typing import Optional

from fastapi import Depends, HTTPException, Request, status

from app.controllers.user import UserController
from core.factory import Factory


async def get_current_user(
    request: Request,
    user_controller: UserController = Depends(Factory().get_user_controller),
):
    """Get current authenticated user. Raises 401 if not authenticated."""
    if not hasattr(request, "user") or not hasattr(request.user, "id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return await user_controller.get_by_id(request.user.id)


async def get_current_user_optional(
    request: Request,
    user_controller: UserController = Depends(Factory().get_user_controller),
) -> Optional[dict]:
    """Get current user if authenticated, otherwise return None."""
    try:
        if not hasattr(request, "user") or not hasattr(request.user, "id"):
            return None
        return await user_controller.get_by_id(request.user.id)
    except Exception:
        return None
