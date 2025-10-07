"""
Unified authentication endpoint for getting current user
"""

from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException

from app.integrations.github_oauth import get_session, get_user_from_session

router = APIRouter()


@router.get("/me")
async def get_current_user(session_id: Optional[str] = Cookie(None)):
    """Get current authenticated user (works for both email and GitHub auth)"""
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")

    user = get_user_from_session(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
