"""
GitHub OAuth Authentication Endpoints
"""

from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException, Query, Response
from fastapi.responses import RedirectResponse

from app.integrations.github_oauth import (
    FRONTEND_URL,
    build_oauth_login_url,
    clear_session,
    exchange_code_for_token,
    fetch_github_repos,
    fetch_github_user,
    generate_session_id,
    generate_state,
    get_access_token_from_session,
    get_user_from_session,
    set_session,
)
from app.models import User
from app.repositories import UserRepository
from core.database import get_session

router = APIRouter()


@router.get("/login")
async def github_login():
    """Initiate GitHub OAuth login"""
    try:
        state = generate_state()
        login_url = build_oauth_login_url(state)
        return {"login_url": login_url, "state": state}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/callback")
async def github_callback(code: str = Query(...), state: str = Query(...)):
    """Handle GitHub OAuth callback"""
    try:
        # Exchange code for token
        access_token = await exchange_code_for_token(code)

        # Fetch user data
        github_user = await fetch_github_user(access_token)

        # Get or create user in database
        db_session = next(get_session())
        try:
            user_repo = UserRepository(User, db_session)

            # Try to find existing user by GitHub ID
            user = await user_repo.get_by("github_id", github_user["id"])

            if not user:
                # Try to find by username
                user = await user_repo.get_by("username", github_user["login"])
                if user:
                    # Update with GitHub data
                    user.github_id = github_user["id"]
                    user.github_avatar_url = github_user["avatar_url"]
                    user.github_access_token = access_token
                else:
                    # Create new user
                    user = User(
                        username=github_user["login"],
                        email=github_user.get(
                            "email", f"{github_user['login']}@github.local"
                        ),
                        password="",  # OAuth users don't need password
                        github_id=github_user["id"],
                        github_avatar_url=github_user["avatar_url"],
                        github_access_token=access_token,
                    )
                    db_session.add(user)
                    await db_session.commit()
                    await db_session.refresh(user)
            else:
                # Update access token
                user.github_access_token = access_token
                await db_session.commit()

            # Create session
            session_id = generate_session_id()
            set_session(session_id, access_token, github_user)

            # Set session cookie and redirect
            from core.config import config

            response = RedirectResponse(url=config.FRONTEND_URL)
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="lax",
                max_age=86400,  # 24 hours
            )

            return response

        finally:
            await db_session.close()

    except Exception as e:
        print(f"OAuth callback error: {e}")  # Debug logging
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")


@router.get("/me")
async def get_current_user(session_id: Optional[str] = Cookie(None)):
    """Get current authenticated user"""
    user_data = get_user_from_session(session_id)
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return {
        "id": user_data["id"],
        "login": user_data["login"],
        "avatar_url": user_data["avatar_url"],
        "name": user_data.get("name"),
        "email": user_data.get("email"),
    }


@router.get("/repos")
async def get_user_repos(session_id: Optional[str] = Cookie(None)):
    """Get user's GitHub repositories"""
    access_token = get_access_token_from_session(session_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        repos = await fetch_github_repos(access_token)
        return [
            {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
                "private": repo["private"],
                "owner": {
                    "login": repo["owner"]["login"],
                    "id": repo["owner"]["id"],
                    "avatar_url": repo["owner"]["avatar_url"],
                },
                "description": repo.get("description"),
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "updated_at": repo.get("updated_at"),
            }
            for repo in repos
        ]
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to fetch repositories: {str(e)}"
        )


@router.post("/logout")
async def logout(session_id: Optional[str] = Cookie(None), response: Response = None):
    """Logout user"""
    clear_session(session_id)

    response = Response()
    response.delete_cookie(key="session_id")
    return {"message": "Logged out successfully"}
