from pydantic import BaseModel, Field
from typing import List, Optional


class GitHubIntegrationCreateRequest(BaseModel):
    """Request schema for creating a GitHub integration"""
    access_token: str = Field(..., min_length=1, description="GitHub access token")
    github_owner: str | None = Field(None, description="GitHub owner/org name")
    selected_repos: List[str] = Field(
        default_factory=list, 
        description="List of repository names to connect (e.g., 'owner/repo')"
    )


class GitHubIntegrationUpdateRequest(BaseModel):
    """Request schema for updating a GitHub integration"""
    access_token: str | None = Field(None, min_length=1, description="GitHub access token")
    github_owner: str | None = Field(None, description="GitHub owner/org name")
    selected_repos: Optional[List[str]] = Field(
        None, 
        description="List of repository names to connect (e.g., 'owner/repo')"
    )
    is_active: bool | None = Field(None, description="Is integration active")

