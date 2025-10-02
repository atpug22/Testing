"""
GitHub Repository Integration Endpoints
"""

from fastapi import APIRouter, HTTPException, Cookie, Depends, BackgroundTasks
from typing import Optional
from pydantic import BaseModel

from app.integrations.github_oauth import get_access_token_from_session, get_user_from_session
from app.integrations.github_fetcher import GitHubFetcher
from core.database import get_session

router = APIRouter()


class FetchRepositoryRequest(BaseModel):
    """Request model for fetching repository data"""
    owner: str
    repo: str
    days: int = 90


class FetchRepositoryResponse(BaseModel):
    """Response model for fetch repository"""
    success: bool
    repository: str
    total_prs: int
    open_prs: int
    merged_prs: int
    api_requests_made: int
    message: str


@router.post("/fetch", response_model=FetchRepositoryResponse)
async def fetch_repository_data(
    request: FetchRepositoryRequest,
    background_tasks: BackgroundTasks,
    session_id: Optional[str] = Cookie(None)
):
    """Fetch and store repository data from GitHub"""
    access_token = get_access_token_from_session(session_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_data = get_user_from_session(session_id)
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        async for db_session in get_session():
            fetcher = GitHubFetcher(access_token, db_session)
            result = await fetcher.fetch_repository_data(
                owner=request.owner,
                repo=request.repo,
                days=request.days
            )
            
            return FetchRepositoryResponse(
                success=True,
                repository=f"{request.owner}/{request.repo}",
                total_prs=result["total_prs"],
                open_prs=result["open_prs"],
                merged_prs=result["merged_prs"],
                api_requests_made=result["api_requests_made"],
                message=f"Successfully fetched {result['total_prs']} PRs from {request.owner}/{request.repo}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch repository data: {str(e)}")


@router.get("/status")
async def get_integration_status(session_id: Optional[str] = Cookie(None)):
    """Get GitHub integration status"""
    user_data = get_user_from_session(session_id)
    if not user_data:
        return {"authenticated": False, "user": None}
    
    return {
        "authenticated": True,
        "user": {
            "id": user_data["id"],
            "login": user_data["login"],
            "avatar_url": user_data["avatar_url"],
            "name": user_data.get("name"),
        }
    }
