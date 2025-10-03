from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class GitHubIntegrationResponse(BaseModel):
    """Response schema for GitHub integration"""
    id: int
    uuid: UUID
    organization_id: int
    github_owner: str | None
    selected_repos: list[str] | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GitHubRepositoryResponse(BaseModel):
    """Response schema for GitHub repository"""
    name: str
    full_name: str
    description: str | None
    private: bool
    html_url: str

