"""
GitHub OAuth Integration for LogPose
Handles GitHub authentication and user session management
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

# Load environment variables from .env file
load_dotenv()

from core.config import config

# GitHub OAuth Configuration
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_BASE = "https://api.github.com"

# In-memory session storage. For production, replace with Redis or database
SESSIONS: Dict[str, Dict[str, object]] = {}
SESSION_TTL_HOURS = 24


def generate_state() -> str:
    """Generate a random state parameter for OAuth security"""
    return secrets.token_urlsafe(32)


def generate_session_id() -> str:
    """Generate a random session ID"""
    return secrets.token_urlsafe(32)


def build_oauth_login_url(state: str) -> str:
    """Build GitHub OAuth login URL"""
    if not GITHUB_CLIENT_ID:
        raise ValueError(
            "GitHub OAuth not configured. Please set GITHUB_CLIENT_ID environment variable."
        )

    scope = "repo read:org read:user user:email"
    redirect_uri = f"{APP_BASE_URL}/v1/auth/github/callback"
    return (
        f"{OAUTH_AUTHORIZE_URL}?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}&scope={scope}&state={state}"
    )


async def exchange_code_for_token(code: str) -> str:
    """Exchange OAuth code for access token"""
    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            OAUTH_TOKEN_URL,
            headers=headers,
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{APP_BASE_URL}/api/v1/auth/github/callback",
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise HTTPException(status_code=400, detail=f"OAuth error: {data}")
        return data["access_token"]


async def fetch_github_user(access_token: str) -> dict:
    """Fetch GitHub user information"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GITHUB_API_BASE}/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_github_repos(access_token: str) -> list:
    """Fetch user's GitHub repositories"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GITHUB_API_BASE}/user/repos",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
            params={"sort": "updated", "per_page": 100},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()


def set_session(session_id: str, access_token: str, user: dict) -> None:
    """Store session data"""
    SESSIONS[session_id] = {
        "access_token": access_token,
        "user": user,
        "created_at": datetime.now(timezone.utc),
    }


def get_session(session_id: Optional[str]) -> Optional[Dict[str, object]]:
    """Get session data by session ID"""
    if not session_id:
        return None
    sess = SESSIONS.get(session_id)
    if not sess:
        return None
    created_at: datetime = sess.get("created_at")  # type: ignore
    if created_at and created_at < datetime.now(timezone.utc) - timedelta(
        hours=SESSION_TTL_HOURS
    ):
        # Expire session
        SESSIONS.pop(session_id, None)
        return None
    return sess


def clear_session(session_id: Optional[str]) -> None:
    """Clear session data"""
    if session_id and session_id in SESSIONS:
        del SESSIONS[session_id]


def get_user_from_session(session_id: Optional[str]) -> Optional[dict]:
    """Get user data from session"""
    session = get_session(session_id)
    if not session:
        return None
    return session.get("user")


def get_access_token_from_session(session_id: Optional[str]) -> Optional[str]:
    """Get GitHub access token from session"""
    session = get_session(session_id)
    if not session:
        return None
    return session.get("access_token")
