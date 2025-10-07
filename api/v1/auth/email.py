"""
Email Authentication Endpoints
"""

from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException, Response
from fastapi.responses import RedirectResponse

from app.models import User
from app.repositories import UserRepository
from app.schemas.requests.auth import EmailLoginRequest, EmailRegisterRequest
from app.schemas.responses.auth import AuthResponse, UserResponse
from core.database import get_session
from core.security.password_handler import PasswordHandler

router = APIRouter()


@router.post("/login", response_model=AuthResponse)
async def email_login(request: EmailLoginRequest, response: Response):
    """Email login"""
    try:
        async for db_session in get_session():
            try:
                user_repo = UserRepository(User, db_session)

                # Find user by email
                user = await user_repo.get_by("email", request.email, unique=True)
                if not user:
                    raise HTTPException(status_code=401, detail="Invalid credentials")

                # Verify password
                if not PasswordHandler.verify_password(request.password, user.password):
                    raise HTTPException(status_code=401, detail="Invalid credentials")

                # Create session
                from app.integrations.github_oauth import (
                    generate_session_id,
                    set_session,
                )

                session_id = generate_session_id()

                # Create user data for session
                user_data = {
                    "id": user.id,
                    "login": user.username,
                    "email": user.email,
                    "avatar_url": user.github_avatar_url,
                    "name": getattr(user, "name", user.username),
                }

                set_session(
                    session_id, "", user_data
                )  # No GitHub token for email users

                # Set session cookie
                response.set_cookie(
                    key="session_id",
                    value=session_id,
                    httponly=True,
                    secure=False,
                    samesite="lax",
                    max_age=86400,  # 24 hours
                )

                return AuthResponse(
                    success=True, message="Login successful", user=user_data
                )

            finally:
                await db_session.close()

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Login failed: {str(e)}")


@router.post("/register", response_model=AuthResponse)
async def email_register(request: EmailRegisterRequest, response: Response):
    """Email registration"""
    try:
        async for db_session in get_session():
            try:
                user_repo = UserRepository(User, db_session)

                # Check if user already exists
                from sqlalchemy import select

                existing_user_query = select(User).where(User.email == request.email)
                existing_user = await db_session.scalar(existing_user_query)
                if existing_user:
                    raise HTTPException(status_code=400, detail="User already exists")

                existing_username_query = select(User).where(
                    User.username == request.username
                )
                existing_username = await db_session.scalar(existing_username_query)
                if existing_username:
                    raise HTTPException(
                        status_code=400, detail="Username already taken"
                    )

                # Create new user
                hashed_password = PasswordHandler.hash_password(request.password)
                user = User(
                    username=request.username,
                    email=request.email,
                    password=hashed_password,
                )
                db_session.add(user)
                await db_session.commit()
                await db_session.refresh(user)

                # Create session
                from app.integrations.github_oauth import (
                    generate_session_id,
                    set_session,
                )

                session_id = generate_session_id()

                user_data = {
                    "id": user.id,
                    "login": user.username,
                    "email": user.email,
                    "avatar_url": None,
                    "name": request.name,
                }

                set_session(session_id, "", user_data)

                # Set session cookie
                response.set_cookie(
                    key="session_id",
                    value=session_id,
                    httponly=True,
                    secure=False,
                    samesite="lax",
                    max_age=86400,
                )

                return AuthResponse(
                    success=True, message="Registration successful", user=user_data
                )

            finally:
                await db_session.close()

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")
