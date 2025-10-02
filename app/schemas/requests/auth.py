"""
Authentication request schemas
"""

from pydantic import BaseModel, EmailStr


class EmailLoginRequest(BaseModel):
    """Email login request"""
    email: EmailStr
    password: str


class EmailRegisterRequest(BaseModel):
    """Email registration request"""
    email: EmailStr
    password: str
    username: str
    name: str


class GitHubConnectRequest(BaseModel):
    """GitHub connection request"""
    github_username: str
    github_token: str
