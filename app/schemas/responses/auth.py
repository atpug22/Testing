"""
Authentication response schemas
"""

from typing import Optional

from pydantic import BaseModel


class AuthResponse(BaseModel):
    """Authentication response"""

    success: bool
    message: str
    user: Optional[dict] = None
    token: Optional[str] = None


class UserResponse(BaseModel):
    """User response"""

    id: int
    username: str
    email: str
    name: Optional[str] = None
    github_id: Optional[int] = None
    github_avatar_url: Optional[str] = None
    is_authenticated: bool = True
