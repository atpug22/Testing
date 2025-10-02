from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

import httpx
from dotenv import load_dotenv

load_dotenv()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_BASE = "https://api.github.com"

# In-memory session storage. For production, replace with a persistent store (e.g., Redis).
SESSIONS: Dict[str, Dict[str, object]] = {}
SESSION_TTL_HOURS = 24


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def generate_session_id() -> str:
    return secrets.token_urlsafe(32)


def build_oauth_login_url(state: str) -> str:
    scope = "repo read:org read:user user:email"
    redirect_uri = f"{APP_BASE_URL}/auth/callback"
    return (
        f"{OAUTH_AUTHORIZE_URL}?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}&scope={scope}&state={state}"
    )


async def exchange_code_for_token(code: str) -> str:
    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            OAUTH_TOKEN_URL,
            headers=headers,
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{APP_BASE_URL}/auth/callback",
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"OAuth error: {data}")
        return data["access_token"]


async def fetch_github_user(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GITHUB_API_BASE}/user",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()


def set_session(session_id: str, access_token: str, user: dict) -> None:
    SESSIONS[session_id] = {
        "access_token": access_token,
        "user": user,
        "created_at": datetime.now(timezone.utc),
    }


def get_session(session_id: Optional[str]) -> Optional[Dict[str, object]]:
    if not session_id:
        return None
    sess = SESSIONS.get(session_id)
    if not sess:
        return None
    created_at: datetime = sess.get("created_at")  # type: ignore
    if created_at and created_at < datetime.now(timezone.utc) - timedelta(hours=SESSION_TTL_HOURS):
        # Expire session
        SESSIONS.pop(session_id, None)
        return None
    return sess


def clear_session(session_id: Optional[str]) -> None:
    if session_id and session_id in SESSIONS:
        del SESSIONS[session_id] 