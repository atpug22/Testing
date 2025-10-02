"""
GitHub Repository Data Fetcher

This module provides seamless methods to fetch GitHub repository metrics,
compute delivery risk radar, and store data for analysis. Designed to be
reusable by other developers and applications.

Usage:
    from backend.github_fetcher import GitHubFetcher
    
    fetcher = GitHubFetcher(token="your_github_token")
    result = await fetcher.fetch_repository_metrics(
        owner="microsoft", 
        repo="vscode", 
        days=30, 
        max_prs=100
    )
"""

import asyncio
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import httpx
from pydantic import BaseModel

# Handle both direct execution and package imports
try:
    from .models import RepoDataset, MetricsResponse
    from .metrics import compute_metrics
except ImportError:
    # Direct execution fallback
    from models import RepoDataset, MetricsResponse
    from metrics import compute_metrics

# Import delivery risk analysis if available
HAS_DELIVERY_RISK = False
try:
    # Try to import from parent directory
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    from delivery_risk_integration import compute_delivery_risk_radar
    HAS_DELIVERY_RISK = True
except ImportError:
    print("⚠️  Delivery risk analysis not available. Install delivery_risk_integration.py to enable.")
    HAS_DELIVERY_RISK = False


class FetchConfig(BaseModel):
    """Configuration for repository data fetching"""
    owner: str
    repo: str
    days: int = 90
    max_prs: Optional[int] = None
    max_commits: Optional[int] = None
    include_delivery_risk: bool = True
    save_to_storage: bool = True
    force_refresh: bool = False
    semaphore_limit: int = 10  # Concurrent request limit


class FetchResult(BaseModel):
    """Result of repository data fetching"""
    success: bool
    repository: str
    fetched_at: datetime
    data_file: Optional[str] = None
    summary_file: Optional[str] = None
    delivery_risk_file: Optional[str] = None
    
    # Statistics
    total_prs: int
    total_commits: int
    open_prs: int
    merged_prs: int
    contributors: int
    
    # Timing info
    fetch_duration_seconds: float
    api_requests_made: int
    
    # Error info (if any)
    error_message: Optional[str] = None


class GitHubAPIClient:
    """Enhanced GitHub API client with rate limiting and error handling"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.requests_made = 0
        
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "GitHub-Metrics-Fetcher/1.0"
        }
        
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
    
    async def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make GET request with error handling and rate limit monitoring"""
        async with httpx.AsyncClient(headers=self.headers, timeout=60.0) as client:
            self.requests_made += 1
            resp = await client.get(url, params=params)
            
            # Monitor rate limiting
            remaining = resp.headers.get("x-ratelimit-remaining")
            if remaining and int(remaining) < 100:
                reset_time = resp.headers.get("x-ratelimit-reset")
                if reset_time:
                    reset_dt = datetime.fromtimestamp(int(reset_time), tz=timezone.utc)
                    print(f"⚠️  Rate limit warning: {remaining} requests remaining. Resets at {reset_dt}")
            
            resp.raise_for_status()
            return resp
    
    async def get_paginated_limited(self, url: str, params: Optional[Dict[str, Any]] = None, 
                                  max_items: Optional[int] = None) -> List[dict]:
        """Get paginated data with optional limit"""
        items: List[dict] = []
        page = 1
        per_page = 100
        params = params.copy() if params else {}
        
        while True:
            # Check if we have enough items
            if max_items and len(items) >= max_items:
                break
                
            params.update({"per_page": per_page, "page": page})
            resp = await self.get(url, params=params)
            chunk = resp.json()
            
            if not isinstance(chunk, list) or len(chunk) == 0:
                break
            
            # Add items up to the limit
            if max_items:
                remaining_needed = max_items - len(items)
                items.extend(chunk[:remaining_needed])
            else:
                items.extend(chunk)
            
            print(f"  📄 Fetched page {page}, got {len(chunk)} items ({len(items)} total)")
            
            # Check for next page
            link = resp.headers.get("link")
            if link and 'rel="next"' in link and (not max_items or len(items) < max_items):
                page += 1
            else:
                break
        
        return items
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        return {
            "requests_made": self.requests_made,
            "has_token": bool(self.token),
            "estimated_remaining": 5000 - self.requests_made if self.token else 60 - self.requests_made
        }


class GitHubFetcher:
    """Main class for fetching GitHub repository metrics"""
    
    def __init__(self, token: Optional[str] = None, storage_dir: Optional[str] = None):
        self.client = GitHubAPIClient(token)
        self.storage_dir = Path(storage_dir) if storage_dir else Path(__file__).parent / "storage" / "data"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_storage_path(self, owner: str, repo: str, suffix: str = "") -> Path:
        """Get storage path for repository data"""
        safe_name = f"{owner}__{repo}".replace("/", "_").replace("\\", "_")
        if suffix:
            safe_name += f"_{suffix}"
        return self.storage_dir / f"{safe_name}.json"
    
    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get basic repository information"""
        url = f"{self.client.base_url}/repos/{owner}/{repo}"
        resp = await self.client.get(url)
        repo_info = resp.json()
        
        # Get PR count estimation
        prs_url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls"
        first_resp = await self.client.get(prs_url, params={
            "state": "all", 
            "sort": "created", 
            "direction": "desc",
            "per_page": 1,
            "page": 1
        })
        
        # Estimate total PRs from Link header
        link_header = first_resp.headers.get("link", "")
        total_prs_estimate = "unknown"
        
        if 'rel="last"' in link_header:
            last_page_match = re.search(r'page=(\d+)[^>]*>;\s*rel="last"', link_header)
            if last_page_match:
                last_page = int(last_page_match.group(1))
                total_prs_estimate = f"~{last_page * 100}"
        
        return {
            "name": repo_info.get("name"),
            "full_name": repo_info.get("full_name"),
            "description": repo_info.get("description"),
            "language": repo_info.get("language"),
            "stars": repo_info.get("stargazers_count"),
            "forks": repo_info.get("forks_count"),
            "open_issues": repo_info.get("open_issues_count"),
            "created_at": repo_info.get("created_at"),
            "updated_at": repo_info.get("updated_at"),
            "estimated_total_prs": total_prs_estimate,
            "url": repo_info.get("html_url")
        }
    
    async def fetch_repository_data(self, config: FetchConfig) -> RepoDataset:
        """Fetch comprehensive repository data"""
        print(f"🔍 Fetching data for {config.owner}/{config.repo} (last {config.days} days)...")
        
        since = (datetime.now(timezone.utc) - timedelta(days=config.days)).isoformat()
        
        # Fetch pull requests
        print("📥 Fetching pull requests...")
        prs_url = f"{self.client.base_url}/repos/{config.owner}/{config.repo}/pulls"
        all_prs = await self.client.get_paginated_limited(prs_url, params={
            "state": "all", 
            "sort": "created", 
            "direction": "desc"
        }, max_items=config.max_prs)
        
        # Filter PRs by date
        filtered_prs = [pr for pr in all_prs if pr.get("created_at", "") >= since]
        print(f"  ✅ Found {len(filtered_prs)} PRs created since {since[:10]} (from {len(all_prs)} total fetched)")
        
        # Fetch detailed PR data
        print("📊 Fetching PR details (reviews and commits)...")
        semaphore = asyncio.Semaphore(config.semaphore_limit)
        
        async def build_pr_details(pr: Dict[str, Any]) -> Dict[str, Any]:
            number = pr.get("number")
            async with semaphore:
                # Fetch reviews and commits for this PR
                reviews_url = f"{self.client.base_url}/repos/{config.owner}/{config.repo}/pulls/{number}/reviews"
                commits_url = f"{self.client.base_url}/repos/{config.owner}/{config.repo}/pulls/{number}/commits"
                
                reviews_task = self.client.get_paginated_limited(reviews_url, max_items=50)
                commits_task = self.client.get_paginated_limited(commits_url, max_items=50)
                reviews, commits = await asyncio.gather(reviews_task, commits_task)
            
            # Calculate first review time
            first_review_at: Optional[str] = None
            if reviews:
                review_times = [r.get("submitted_at") for r in reviews if r.get("submitted_at")]
                if review_times:
                    first_review_at = min(review_times)
            
            # Calculate first commit time
            first_commit_at: Optional[str] = None
            if commits:
                commit_dates = [
                    c.get("commit", {}).get("author", {}).get("date") 
                    for c in commits 
                    if c.get("commit", {}).get("author", {}).get("date")
                ]
                if commit_dates:
                    first_commit_at = min(commit_dates)
            
            return {
                "number": pr.get("number"),
                "title": pr.get("title"),
                "user": {
                    "login": pr.get("user", {}).get("login"),
                    "id": pr.get("user", {}).get("id"),
                    "avatar_url": pr.get("user", {}).get("avatar_url"),
                    "html_url": pr.get("user", {}).get("html_url"),
                },
                "state": pr.get("state"),
                "created_at": pr.get("created_at"),
                "merged_at": pr.get("merged_at"),
                "closed_at": pr.get("closed_at"),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
                "changed_files": pr.get("changed_files", 0),
                "comments": pr.get("comments", 0),
                "review_comments": pr.get("review_comments", 0),
                "first_review_at": first_review_at,
                "first_commit_at": first_commit_at,
            }
        
        detailed_prs = await asyncio.gather(*[build_pr_details(pr) for pr in filtered_prs])
        
        # Fetch commits
        print("💾 Fetching commits...")
        commits_url = f"{self.client.base_url}/repos/{config.owner}/{config.repo}/commits"
        all_commits = await self.client.get_paginated_limited(commits_url, params={"since": since}, 
                                                            max_items=config.max_commits)
        
        result_commits = []
        for c in all_commits:
            author = c.get("author")
            commit_info = c.get("commit", {})
            date = commit_info.get("author", {}).get("date")
            if not date:
                continue
            
            result_commits.append({
                "sha": c.get("sha"),
                "author": {
                    "login": author.get("login") if author else None,
                    "id": author.get("id") if author else None,
                    "avatar_url": author.get("avatar_url") if author else None,
                    "html_url": author.get("html_url") if author else None,
                } if author else None,
                "commit_author_name": commit_info.get("author", {}).get("name"),
                "commit_author_email": commit_info.get("author", {}).get("email"),
                "date": date,
            })
        
        print(f"  ✅ Found {len(result_commits)} commits")
        
        # Create dataset
        dataset = RepoDataset.model_validate({
            "repo": config.repo,
            "owner": config.owner,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "prs": detailed_prs,
            "commits": result_commits,
        })
        
        return dataset
    
    async def fetch_repository_metrics(self, 
                                     owner: str, 
                                     repo: str, 
                                     days: int = 90,
                                     max_prs: Optional[int] = None,
                                     max_commits: Optional[int] = None,
                                     include_delivery_risk: bool = True,
                                     save_to_storage: bool = True,
                                     force_refresh: bool = False) -> FetchResult:
        """
        Main method to fetch repository metrics seamlessly
        
        Args:
            owner: Repository owner (e.g., 'microsoft')
            repo: Repository name (e.g., 'vscode')
            days: Number of days to analyze (default: 90)
            max_prs: Maximum PRs to fetch (None for all recent)
            max_commits: Maximum commits to fetch (None for all recent)
            include_delivery_risk: Whether to compute delivery risk radar
            save_to_storage: Whether to save data to storage directory
            force_refresh: Whether to force refresh even if data exists
            
        Returns:
            FetchResult with all the computed metrics and file paths
        """
        start_time = datetime.now()
        
        try:
            # Create config
            config = FetchConfig(
                owner=owner,
                repo=repo,
                days=days,
                max_prs=max_prs,
                max_commits=max_commits,
                include_delivery_risk=include_delivery_risk,
                save_to_storage=save_to_storage,
                force_refresh=force_refresh
            )
            
            # Check if data already exists
            data_path = self._get_storage_path(owner, repo, "metrics")
            if data_path.exists() and not force_refresh:
                print(f"📁 Found existing data at {data_path}")
                print("   Use force_refresh=True to fetch new data")
                
                # Load existing data
                with open(data_path, 'r') as f:
                    existing_data = json.load(f)
                
                return FetchResult(
                    success=True,
                    repository=f"{owner}/{repo}",
                    fetched_at=datetime.fromisoformat(existing_data["dataset"]["fetched_at"]),
                    data_file=str(data_path),
                    total_prs=len(existing_data["dataset"]["prs"]),
                    total_commits=len(existing_data["dataset"]["commits"]),
                    open_prs=len([pr for pr in existing_data["dataset"]["prs"] if pr["state"] == "open"]),
                    merged_prs=existing_data["metrics"]["team_summary"]["total_merged_prs"],
                    contributors=len(existing_data["metrics"]["contributors"]),
                    fetch_duration_seconds=0.0,
                    api_requests_made=0
                )
            
            # Fetch repository info
            print("🏷️  Getting repository information...")
            repo_info = await self.get_repository_info(owner, repo)
            print(f"   📊 {repo_info['full_name']} - {repo_info['language']} - ⭐ {repo_info['stars']}")
            print(f"   📈 Estimated PRs: {repo_info['estimated_total_prs']}")
            
            # Fetch data
            dataset = await self.fetch_repository_data(config)
            
            # Compute standard metrics
            print("🧮 Computing standard metrics...")
            metrics = compute_metrics(dataset)
            
            # Create metrics response
            metrics_response = MetricsResponse(dataset=dataset, metrics=metrics)
            
            # Compute delivery risk if requested
            delivery_risk_data = None
            if include_delivery_risk and HAS_DELIVERY_RISK:
                print("🎯 Computing delivery risk radar...")
                delivery_risk_data = compute_delivery_risk_radar(dataset)
            
            # Calculate statistics
            open_prs = len([pr for pr in dataset.prs if pr.state == "open"])
            fetch_duration = (datetime.now() - start_time).total_seconds()
            
            # Save data if requested
            data_file = None
            summary_file = None
            delivery_risk_file = None
            
            if save_to_storage:
                print("💾 Saving data to storage...")
                
                # Save complete metrics data
                data_file = self._get_storage_path(owner, repo, "metrics")
                with open(data_file, 'w') as f:
                    json.dump(json.loads(metrics_response.model_dump_json()), f, indent=2)
                print(f"   📄 Metrics saved to: {data_file}")
                
                # Save summary data
                summary_file = self._get_storage_path(owner, repo, "summary")
                summary_data = {
                    "repository": f"{owner}/{repo}",
                    "repository_info": repo_info,
                    "analysis_date": datetime.now(timezone.utc).isoformat(),
                    "config": config.model_dump(),
                    "days_analyzed": days,
                    "total_prs": len(dataset.prs),
                    "total_commits": len(dataset.commits),
                    "open_prs": open_prs,
                    "merged_prs": metrics.team_summary.total_merged_prs,
                    "contributors": len(metrics.contributors),
                    "avg_merge_time_hours": metrics.team_summary.avg_time_to_merge_hours,
                    "fetch_duration_seconds": fetch_duration,
                    "api_requests_made": self.client.requests_made,
                    "top_contributors": [
                        {
                            "login": c.user.login,
                            "prs": len([pr for pr in dataset.prs if pr.user.login == c.user.login]),
                            "avg_merge_time": c.avg_time_to_merge_hours
                        }
                        for c in sorted(metrics.contributors, 
                                      key=lambda x: len([pr for pr in dataset.prs if pr.user.login == x.user.login]), 
                                      reverse=True)[:10]
                    ]
                }
                
                with open(summary_file, 'w') as f:
                    json.dump(summary_data, f, indent=2, default=str)
                print(f"   📊 Summary saved to: {summary_file}")
                
                # Save delivery risk data
                if delivery_risk_data:
                    delivery_risk_file = self._get_storage_path(owner, repo, "delivery_risk")
                    with open(delivery_risk_file, 'w') as f:
                        json.dump(json.loads(delivery_risk_data.model_dump_json()), f, indent=2, default=str)
                    print(f"   🎯 Delivery risk saved to: {delivery_risk_file}")
            
            # Create result
            result = FetchResult(
                success=True,
                repository=f"{owner}/{repo}",
                fetched_at=dataset.fetched_at,
                data_file=str(data_file) if data_file else None,
                summary_file=str(summary_file) if summary_file else None,
                delivery_risk_file=str(delivery_risk_file) if delivery_risk_file else None,
                total_prs=len(dataset.prs),
                total_commits=len(dataset.commits),
                open_prs=open_prs,
                merged_prs=metrics.team_summary.total_merged_prs,
                contributors=len(metrics.contributors),
                fetch_duration_seconds=fetch_duration,
                api_requests_made=self.client.requests_made
            )
            
            print(f"\n✅ Successfully fetched metrics for {owner}/{repo}")
            print(f"   📊 {result.total_prs} PRs, {result.total_commits} commits, {result.contributors} contributors")
            print(f"   ⏱️  Completed in {result.fetch_duration_seconds:.1f}s using {result.api_requests_made} API requests")
            
            return result
            
        except Exception as e:
            return FetchResult(
                success=False,
                repository=f"{owner}/{repo}",
                fetched_at=datetime.now(timezone.utc),
                total_prs=0,
                total_commits=0,
                open_prs=0,
                merged_prs=0,
                contributors=0,
                fetch_duration_seconds=(datetime.now() - start_time).total_seconds(),
                api_requests_made=self.client.requests_made,
                error_message=str(e)
            )
    
    def list_stored_repositories(self) -> List[Dict[str, Any]]:
        """List all repositories that have been fetched and stored"""
        repos = []
        
        for file_path in self.storage_dir.glob("*_summary.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                repos.append({
                    "repository": data.get("repository"),
                    "analysis_date": data.get("analysis_date"),
                    "days_analyzed": data.get("days_analyzed"),
                    "total_prs": data.get("total_prs"),
                    "contributors": data.get("contributors"),
                    "files": {
                        "summary": str(file_path),
                        "metrics": str(file_path).replace("_summary.json", "_metrics.json"),
                        "delivery_risk": str(file_path).replace("_summary.json", "_delivery_risk.json")
                    }
                })
            except Exception:
                continue
        
        return sorted(repos, key=lambda x: x["analysis_date"], reverse=True)
    
    def get_stored_data(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get stored data for a repository"""
        summary_path = self._get_storage_path(owner, repo, "summary")
        metrics_path = self._get_storage_path(owner, repo, "metrics")
        delivery_risk_path = self._get_storage_path(owner, repo, "delivery_risk")
        
        result = {}
        
        if summary_path.exists():
            with open(summary_path, 'r') as f:
                result["summary"] = json.load(f)
        
        if metrics_path.exists():
            with open(metrics_path, 'r') as f:
                result["metrics"] = json.load(f)
        
        if delivery_risk_path.exists():
            with open(delivery_risk_path, 'r') as f:
                result["delivery_risk"] = json.load(f)
        
        return result


# Convenience functions for easy usage
async def fetch_metrics(owner: str, repo: str, **kwargs) -> FetchResult:
    """Convenience function to fetch metrics"""
    fetcher = GitHubFetcher()
    return await fetcher.fetch_repository_metrics(owner, repo, **kwargs)


def list_repositories() -> List[Dict[str, Any]]:
    """Convenience function to list stored repositories"""
    fetcher = GitHubFetcher()
    return fetcher.list_stored_repositories()


def get_repository_data(owner: str, repo: str) -> Dict[str, Any]:
    """Convenience function to get stored repository data"""
    fetcher = GitHubFetcher()
    return fetcher.get_stored_data(owner, repo)