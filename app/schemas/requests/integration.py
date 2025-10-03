from pydantic import BaseModel, Field


class GitHubIntegrationCreateRequest(BaseModel):
    """Request schema for creating a GitHub integration"""
    access_token: str = Field(..., min_length=1, description="GitHub access token")
    github_owner: str | None = Field(None, description="GitHub owner/org name")


class GitHubIntegrationUpdateRequest(BaseModel):
    """Request schema for updating a GitHub integration"""
    access_token: str | None = Field(None, min_length=1, description="GitHub access token")
    github_owner: str | None = Field(None, description="GitHub owner/org name")
    selected_repos: list[str] | None = Field(None, description="Selected repositories")
    is_active: bool | None = Field(None, description="Is integration active")

