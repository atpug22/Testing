from typing import Callable

from fastapi import APIRouter, Depends, HTTPException
import httpx

from app.controllers.integration import GitHubIntegrationController
from app.controllers.organization import OrganizationController
from app.models.integration import GitHubIntegration
from app.models.organization import OrganizationRole
from app.models.user import User
from app.schemas.requests.integration import (
    GitHubIntegrationCreateRequest,
    GitHubIntegrationUpdateRequest,
)
from app.schemas.responses.integration import (
    GitHubIntegrationResponse,
    GitHubRepositoryResponse,
)
from core.factory import Factory
from core.fastapi.dependencies import AuthenticationRequired
from core.fastapi.dependencies.current_user import get_current_user
from sqlalchemy import select
from core.database.session import session
from app.models.organization import organization_members

integration_router = APIRouter()


async def check_org_admin(organization_id: int, user_id: int):
    """Check if user is admin of the organization"""
    stmt = select(organization_members.c.role).where(
        organization_members.c.organization_id == organization_id,
        organization_members.c.user_id == user_id
    )
    result = await session.execute(stmt)
    role = result.scalar_one_or_none()
    
    if role != OrganizationRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only organization admins can manage integrations")


@integration_router.get("/github/{organization_id}", dependencies=[Depends(AuthenticationRequired)])
async def get_github_integration(
    organization_id: int,
    user: User = Depends(get_current_user),
    integration_controller: GitHubIntegrationController = Depends(Factory().get_integration_controller),
) -> GitHubIntegrationResponse | None:
    """Get GitHub integration for an organization"""
    integration = await integration_controller.get_by_organization(organization_id)
    
    if integration:
        # Don't return the access token
        response = GitHubIntegrationResponse.model_validate(integration)
        return response
    
    return None


@integration_router.post("/github/{organization_id}", status_code=201, dependencies=[Depends(AuthenticationRequired)])
async def create_github_integration(
    organization_id: int,
    request: GitHubIntegrationCreateRequest,
    user: User = Depends(get_current_user),
    integration_controller: GitHubIntegrationController = Depends(Factory().get_integration_controller),
    organization_controller: OrganizationController = Depends(Factory().get_organization_controller),
) -> GitHubIntegrationResponse:
    """Create GitHub integration (admin only)"""
    # Check if user is admin
    await check_org_admin(organization_id, user.id)
    
    # Check if organization exists
    organization = await organization_controller.get_by_id(organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check if integration already exists
    existing = await integration_controller.get_by_organization(organization_id)
    if existing:
        raise HTTPException(status_code=400, detail="GitHub integration already exists for this organization")
    
    # Validate GitHub token by making a test request
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {request.access_token}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid GitHub access token")
            
            user_data = response.json()
            github_owner = request.github_owner or user_data.get("login")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to validate GitHub token")
    
    # Create integration
    integration = await integration_controller.create({
        "organization_id": organization_id,
        "access_token": request.access_token,
        "github_owner": github_owner,
        "selected_repos": request.selected_repos,
        "is_active": True,
    })
    
    return GitHubIntegrationResponse.model_validate(integration)


@integration_router.patch("/github/{organization_id}", dependencies=[Depends(AuthenticationRequired)])
async def update_github_integration(
    organization_id: int,
    request: GitHubIntegrationUpdateRequest,
    user: User = Depends(get_current_user),
    integration_controller: GitHubIntegrationController = Depends(Factory().get_integration_controller),
) -> GitHubIntegrationResponse:
    """Update GitHub integration (admin only)"""
    # Check if user is admin
    await check_org_admin(organization_id, user.id)
    
    # Get existing integration
    integration = await integration_controller.get_by_organization(organization_id)
    if not integration:
        raise HTTPException(status_code=404, detail="GitHub integration not found")
    
    # Update fields
    if request.access_token:
        integration.access_token = request.access_token
    if request.github_owner:
        integration.github_owner = request.github_owner
    if request.selected_repos is not None:
        integration.selected_repos = request.selected_repos
    if request.is_active is not None:
        integration.is_active = request.is_active
    
    updated = await integration_controller.update(id_=integration.id, obj=integration)
    return updated


@integration_router.delete("/github/{organization_id}", dependencies=[Depends(AuthenticationRequired)])
async def delete_github_integration(
    organization_id: int,
    user: User = Depends(get_current_user),
    integration_controller: GitHubIntegrationController = Depends(Factory().get_integration_controller),
):
    """Delete GitHub integration (admin only)"""
    # Check if user is admin
    await check_org_admin(organization_id, user.id)
    
    integration = await integration_controller.get_by_organization(organization_id)
    if not integration:
        raise HTTPException(status_code=404, detail="GitHub integration not found")
    
    await integration_controller.delete(id_=integration.id)
    return {"message": "GitHub integration deleted successfully"}


@integration_router.get("/github/{organization_id}/repositories", dependencies=[Depends(AuthenticationRequired)])
async def get_github_repositories(
    organization_id: int,
    user: User = Depends(get_current_user),
    integration_controller: GitHubIntegrationController = Depends(Factory().get_integration_controller),
) -> list[GitHubRepositoryResponse]:
    """Get GitHub repositories for the integration"""
    # Check if user is admin
    await check_org_admin(organization_id, user.id)
    
    integration = await integration_controller.get_by_organization(organization_id)
    if not integration:
        raise HTTPException(status_code=404, detail="GitHub integration not found")
    
    # Fetch repositories from GitHub API
    try:
        async with httpx.AsyncClient() as client:
            # Fetch user/org repos
            if integration.github_owner:
                url = f"https://api.github.com/users/{integration.github_owner}/repos"
            else:
                url = "https://api.github.com/user/repos"
            
            response = await client.get(
                url,
                headers={"Authorization": f"token {integration.access_token}"},
                params={"per_page": 100, "sort": "updated"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch repositories from GitHub")
            
            repos = response.json()
            return [
                GitHubRepositoryResponse(
                    name=repo["name"],
                    full_name=repo["full_name"],
                    description=repo.get("description"),
                    private=repo["private"],
                    html_url=repo["html_url"],
                )
                for repo in repos
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch repositories: {str(e)}")

