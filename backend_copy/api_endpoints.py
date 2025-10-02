"""
Additional API endpoints for GitHub metrics fetching

Add these endpoints to your existing main.py FastAPI application
to provide seamless GitHub metrics access via REST API.
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import HTTPException, Query, Header, Cookie, BackgroundTasks
from pydantic import BaseModel

from .github_fetcher import GitHubFetcher, FetchResult, FetchConfig
from .github_oauth import get_session


class FetchMetricsRequest(BaseModel):
    """Request model for fetching metrics"""
    owner: str
    repo: str
    days: int = 90
    max_prs: Optional[int] = None
    max_commits: Optional[int] = None
    include_delivery_risk: bool = True
    force_refresh: bool = False


class FetchMetricsResponse(BaseModel):
    """Response model for fetch metrics"""
    success: bool
    repository: str
    fetched_at: datetime
    total_prs: int
    total_commits: int
    open_prs: int
    merged_prs: int
    contributors: int
    fetch_duration_seconds: float
    api_requests_made: int
    data_available: bool
    delivery_risk_available: bool
    error_message: Optional[str] = None


class RepositoryListItem(BaseModel):
    """Repository list item"""
    repository: str
    analysis_date: str
    days_analyzed: int
    total_prs: int
    contributors: int


# Add these endpoints to your FastAPI app

async def fetch_repository_metrics_endpoint(
    request: FetchMetricsRequest,
    background_tasks: BackgroundTasks,
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None),
) -> FetchMetricsResponse:
    """
    Fetch GitHub repository metrics
    
    This endpoint fetches comprehensive metrics for a GitHub repository
    and stores them for future access.
    """
    # Authenticate user
    sid = x_session_id or session_id
    sess = get_session(sid)
    if not sess:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get GitHub token from session
    github_token = sess.get("access_token")
    
    try:
        # Create fetcher with user's token
        fetcher = GitHubFetcher(token=github_token)
        
        # Fetch metrics
        result = await fetcher.fetch_repository_metrics(
            owner=request.owner,
            repo=request.repo,
            days=request.days,
            max_prs=request.max_prs,
            max_commits=request.max_commits,
            include_delivery_risk=request.include_delivery_risk,
            save_to_storage=True,
            force_refresh=request.force_refresh
        )
        
        return FetchMetricsResponse(
            success=result.success,
            repository=result.repository,
            fetched_at=result.fetched_at,
            total_prs=result.total_prs,
            total_commits=result.total_commits,
            open_prs=result.open_prs,
            merged_prs=result.merged_prs,
            contributors=result.contributors,
            fetch_duration_seconds=result.fetch_duration_seconds,
            api_requests_made=result.api_requests_made,
            data_available=result.data_file is not None,
            delivery_risk_available=result.delivery_risk_file is not None,
            error_message=result.error_message
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching metrics: {str(e)}")


async def get_repository_summary_endpoint(
    owner: str = Query(..., description="Repository owner"),
    repo: str = Query(..., description="Repository name"),
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    Get stored repository summary data
    
    Returns the summary metrics for a previously fetched repository.
    """
    # Authenticate user
    sid = x_session_id or session_id
    sess = get_session(sid)
    if not sess:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        fetcher = GitHubFetcher()
        data = fetcher.get_stored_data(owner, repo)
        
        if 'summary' not in data:
            raise HTTPException(status_code=404, detail="Repository summary not found. Fetch metrics first.")
        
        return data['summary']
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving summary: {str(e)}")


async def get_repository_metrics_endpoint(
    owner: str = Query(..., description="Repository owner"),
    repo: str = Query(..., description="Repository name"),
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    Get stored repository metrics data
    
    Returns the complete metrics data for a previously fetched repository.
    """
    # Authenticate user
    sid = x_session_id or session_id
    sess = get_session(sid)
    if not sess:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        fetcher = GitHubFetcher()
        data = fetcher.get_stored_data(owner, repo)
        
        if 'metrics' not in data:
            raise HTTPException(status_code=404, detail="Repository metrics not found. Fetch metrics first.")
        
        return data['metrics']
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")


async def get_delivery_risk_radar_endpoint(
    owner: str = Query(..., description="Repository owner"),
    repo: str = Query(..., description="Repository name"),
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    Get delivery risk radar analysis
    
    Returns the delivery risk analysis for a previously fetched repository.
    """
    # Authenticate user
    sid = x_session_id or session_id
    sess = get_session(sid)
    if not sess:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        fetcher = GitHubFetcher()
        data = fetcher.get_stored_data(owner, repo)
        
        if 'delivery_risk' not in data:
            raise HTTPException(status_code=404, detail="Delivery risk analysis not found. Fetch metrics with delivery risk enabled.")
        
        return data['delivery_risk']
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving delivery risk: {str(e)}")


async def list_stored_repositories_endpoint(
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None),
) -> List[RepositoryListItem]:
    """
    List all stored repositories
    
    Returns a list of all repositories that have been fetched and stored.
    """
    # Authenticate user
    sid = x_session_id or session_id
    sess = get_session(sid)
    if not sess:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        fetcher = GitHubFetcher()
        repos = fetcher.list_stored_repositories()
        
        return [
            RepositoryListItem(
                repository=repo['repository'],
                analysis_date=repo['analysis_date'],
                days_analyzed=repo['days_analyzed'],
                total_prs=repo['total_prs'],
                contributors=repo['contributors']
            )
            for repo in repos
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing repositories: {str(e)}")


# Integration instructions for main.py:
"""
To integrate these endpoints into your existing main.py, add these imports:

    from .api_endpoints import (
        fetch_repository_metrics_endpoint,
        get_repository_summary_endpoint,
        get_repository_metrics_endpoint,
        get_delivery_risk_radar_endpoint,
        list_stored_repositories_endpoint,
        FetchMetricsRequest,
        FetchMetricsResponse,
        RepositoryListItem
    )

Then add these endpoint definitions:

    @app.post("/api/fetch-metrics", response_model=FetchMetricsResponse)
    async def fetch_metrics(
        request: FetchMetricsRequest,
        background_tasks: BackgroundTasks,
        session_id: Optional[str] = Cookie(None),
        x_session_id: Optional[str] = Header(None),
    ):
        return await fetch_repository_metrics_endpoint(request, background_tasks, session_id, x_session_id)

    @app.get("/api/repository-summary")
    async def get_repository_summary(
        owner: str = Query(...),
        repo: str = Query(...),
        session_id: Optional[str] = Cookie(None),
        x_session_id: Optional[str] = Header(None),
    ):
        return await get_repository_summary_endpoint(owner, repo, session_id, x_session_id)

    @app.get("/api/repository-metrics")
    async def get_repository_metrics(
        owner: str = Query(...),
        repo: str = Query(...),
        session_id: Optional[str] = Cookie(None),
        x_session_id: Optional[str] = Header(None),
    ):
        return await get_repository_metrics_endpoint(owner, repo, session_id, x_session_id)

    @app.get("/api/delivery-risk-radar")
    async def get_delivery_risk_radar(
        owner: str = Query(...),
        repo: str = Query(...),
        session_id: Optional[str] = Cookie(None),
        x_session_id: Optional[str] = Header(None),
    ):
        return await get_delivery_risk_radar_endpoint(owner, repo, session_id, x_session_id)

    @app.get("/api/stored-repositories", response_model=List[RepositoryListItem])
    async def list_stored_repositories(
        session_id: Optional[str] = Cookie(None),
        x_session_id: Optional[str] = Header(None),
    ):
        return await list_stored_repositories_endpoint(session_id, x_session_id)
"""