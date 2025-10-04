"""
Public Repository Integration Endpoints
Allows fetching data from any public GitHub repository
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import text

from app.integrations.enhanced_github_fetcher import EnhancedGitHubFetcher
from app.controllers.integration import GitHubIntegrationController
from core.database import get_session
from core.factory import Factory

router = APIRouter()


class FetchPublicRepoRequest(BaseModel):
    """Request model for fetching public repository data"""
    owner: str
    repo: str
    days: int = 90
    organization_id: int


class FetchPublicRepoResponse(BaseModel):
    """Response model for fetch public repository"""
    success: bool
    repository: str
    total_prs: int
    new_prs: int
    existing_prs: int
    open_prs: int
    merged_prs: int
    api_requests_made: int
    message: str


@router.post("/fetch-public", response_model=FetchPublicRepoResponse)
async def fetch_public_repository_data(
    request: FetchPublicRepoRequest,
    integration_controller: GitHubIntegrationController = Depends(Factory().get_integration_controller)
):
    """Fetch and store data from any public GitHub repository"""
    
    # Get GitHub integration for the organization
    integration = await integration_controller.get_by_organization(request.organization_id)
    if not integration:
        raise HTTPException(status_code=404, detail="GitHub integration not found for this organization")
    
    if not integration.is_active:
        raise HTTPException(status_code=400, detail="GitHub integration is not active")
    
    access_token = integration.access_token
    
    try:
        async for db_session in get_session():
            fetcher = EnhancedGitHubFetcher(access_token, db_session)
            result = await fetcher.fetch_comprehensive_repository_data(
                owner=request.owner,
                repo=request.repo,
                days=request.days
            )
            
            return FetchPublicRepoResponse(
                success=True,
                repository=f"{request.owner}/{request.repo}",
                total_prs=result["total_prs"],
                new_prs=result["new_prs"],
                existing_prs=result["existing_prs"],
                open_prs=result["open_prs"],
                merged_prs=result["merged_prs"],
                api_requests_made=result["api_requests_made"],
                message=f"Successfully processed {result['new_prs']} new PRs from {request.owner}/{request.repo} (total: {result['total_prs']})"
            )
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch repository data: {str(e)}")


@router.get("/prs")
async def get_existing_prs(
    owner: str = Query(..., description="Repository owner"),
    repo: str = Query(..., description="Repository name"),
    organization_id: int = Query(..., description="Organization ID"),
    integration_controller: GitHubIntegrationController = Depends(Factory().get_integration_controller)
):
    """Get existing PRs from database for a specific repository"""
    try:
        # Verify organization has GitHub integration
        integration = await integration_controller.get_by_organization(organization_id)
        if not integration:
            raise HTTPException(status_code=404, detail="GitHub integration not found for this organization")
        
        async for db_session in get_session():
            from app.repositories import PullRequestRepository
            from app.models import PullRequest
            
            pr_repo = PullRequestRepository(PullRequest, db_session)
            
            # Query PRs by repository info
            query = text("""
                SELECT * FROM pull_requests 
                WHERE repository_info->>'owner' = :owner 
                AND repository_info->>'repo' = :repo
                ORDER BY created_at DESC
            """)
            result = await db_session.execute(
                query, 
                {"owner": owner, "repo": repo}
            )
            prs = result.fetchall()
            
            # Convert to list of dictionaries
            pr_list = []
            for pr in prs:
                pr_dict = {
                    "id": pr.id,
                    "github_pr_id": pr.github_pr_id,
                    "title": pr.title,
                    "description": pr.description,
                    "status": pr.status,
                    "labels": pr.labels or [],
                    "additions": pr.additions,
                    "deletions": pr.deletions,
                    "changed_files": pr.changed_files,
                    "created_at": pr.created_at.isoformat() if pr.created_at else None,
                    "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                    "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
                    "pr_metadata": pr.pr_metadata or {},
                    "cicd_metadata": pr.cicd_metadata or {},
                    "time_cycle_metadata": pr.time_cycle_metadata or {},
                    "reviewers_metadata": pr.reviewers_metadata or {},
                    "file_changes_metadata": pr.file_changes_metadata or {},
                    "linked_issues_metadata": pr.linked_issues_metadata or {},
                    "git_blame_metadata": pr.git_blame_metadata or {},
                    "repository_info": pr.repository_info or {}
                }
                pr_list.append(pr_dict)
            
            return pr_list
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch existing PRs: {str(e)}")


@router.get("/search")
async def search_repositories(
    query: str = Query(..., description="Repository search query (e.g., 'owner/repo' or 'react')"),
    limit: int = Query(10, description="Number of results to return")
):
    """Search for public repositories"""
    # This would integrate with GitHub's search API
    # For now, return a simple response
    return {
        "query": query,
        "repositories": [
            {
                "full_name": f"{query}",
                "description": f"Repository: {query}",
                "stars": 0,
                "language": "Unknown"
            }
        ]
    }
