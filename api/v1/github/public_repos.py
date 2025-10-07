"""
Public Repository Integration Endpoints
Allows fetching data from any public GitHub repository
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.integrations.github_fetcher import GitHubFetcher
from core.database import get_session

router = APIRouter()


class FetchPublicRepoRequest(BaseModel):
    """Request model for fetching public repository data"""

    owner: str
    repo: str
    days: int = 90
    github_token: Optional[str] = None


class FetchPublicRepoResponse(BaseModel):
    """Response model for fetch public repository"""

    success: bool
    repository: str
    total_prs: int
    open_prs: int
    merged_prs: int
    api_requests_made: int
    message: str


@router.post("/fetch-public", response_model=FetchPublicRepoResponse)
async def fetch_public_repository_data(request: FetchPublicRepoRequest):
    """Fetch and store data from any public GitHub repository"""

    # Use provided token or a default one (you might want to use a service account token)
    access_token = (
        request.github_token or "ghp_default_token_here"
    )  # Replace with a default token

    try:
        async for db_session in get_session():
            fetcher = GitHubFetcher(access_token, db_session)
            result = await fetcher.fetch_repository_data(
                owner=request.owner, repo=request.repo, days=request.days
            )

            return FetchPublicRepoResponse(
                success=True,
                repository=f"{request.owner}/{request.repo}",
                total_prs=result["total_prs"],
                open_prs=result["open_prs"],
                merged_prs=result["merged_prs"],
                api_requests_made=result["api_requests_made"],
                message=f"Successfully fetched {result['total_prs']} PRs from {request.owner}/{request.repo}",
            )

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to fetch repository data: {str(e)}"
        )


@router.get("/search")
async def search_repositories(
    query: str = Query(
        ..., description="Repository search query (e.g., 'owner/repo' or 'react')"
    ),
    limit: int = Query(10, description="Number of results to return"),
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
                "language": "Unknown",
            }
        ],
    }
