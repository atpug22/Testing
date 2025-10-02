"""
GitHub Data Fetcher for LogPose
Fetches repository data, PRs, commits, and computes metrics
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PullRequest, Event, User, TeamMember
from app.models.enums import PrimaryStatus, FlowBlocker, RiskFlag
from app.models.event import EventType
from app.repositories import PullRequestRepository, EventRepository, TeamMemberRepository


class GitHubAPIClient:
    """GitHub API client with rate limiting and error handling"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.requests_made = 0
        
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "LogPose/1.0"
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
            if len(chunk) < per_page:
                break
                
            page += 1
        
        return items


class GitHubFetcher:
    """Main class for fetching GitHub repository data and storing in database"""
    
    def __init__(self, access_token: str, db_session: AsyncSession):
        self.client = GitHubAPIClient(access_token)
        self.db_session = db_session
        self.pr_repository = PullRequestRepository(PullRequest, db_session)
        self.event_repository = EventRepository(Event, db_session)
        self.team_member_repository = TeamMemberRepository(TeamMember, db_session)
    
    async def fetch_repository_data(self, owner: str, repo: str, days: int = 90) -> Dict[str, Any]:
        """Fetch comprehensive repository data and store in database"""
        print(f"🔍 Fetching data for {owner}/{repo} (last {days} days)...")
        
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        
        # Fetch pull requests
        print("📥 Fetching pull requests...")
        prs_url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls"
        all_prs = await self.client.get_paginated_limited(prs_url, params={
            "state": "all", 
            "sort": "created", 
            "direction": "desc"
        }, max_items=200)
        
        # Filter PRs by date
        print(f"  📊 Total PRs fetched: {len(all_prs)}")
        print(f"  📅 Filtering since: {since[:10]}")
        filtered_prs = [pr for pr in all_prs if pr.get("created_at", "") >= since]
        print(f"  ✅ Found {len(filtered_prs)} PRs created since {since[:10]}")
        
        # Debug: Show some sample PR dates
        if all_prs:
            sample_dates = [pr.get("created_at", "")[:10] for pr in all_prs[:3]]
            print(f"  🔍 Sample PR dates: {sample_dates}")
        
        # Process PRs (skip detailed fetching for now to avoid rate limits)
        print("📊 Processing PRs...")
        detailed_prs = []
        processed_numbers = set()  # Track processed PR numbers to avoid duplicates
        
        for i, pr in enumerate(filtered_prs):  # Process all filtered PRs
            pr_number = pr.get('number')
            if pr_number in processed_numbers:
                print(f"  ⚠️  Skipping duplicate PR #{pr_number}")
                continue
                
            processed_numbers.add(pr_number)
            if i < 5:  # Only show detailed debug for first 5 PRs
                print(f"  🔍 Processing PR #{i+1}: {pr_number}")
                print(f"    Title: {pr.get('title', 'No title')[:50]}...")
                print(f"    State: {pr.get('state', 'unknown')}")
                print(f"    Additions: {pr.get('additions', 0)}, Deletions: {pr.get('deletions', 0)}")
                print(f"    Changed files: {pr.get('changed_files', 0)}")
                print(f"    Labels: {pr.get('labels', [])}")
                print(f"    User: {pr.get('user', {}).get('login', 'unknown')}")
            elif i % 50 == 0:  # Show progress every 50 PRs
                print(f"  🔍 Processing PR #{i+1}: {pr_number}...")
            detailed_prs.append({
                "number": pr_number,
                "title": pr.get("title"),
                "description": pr.get("body", ""),
                "user": {
                    "login": pr.get("user", {}).get("login"),
                    "id": pr.get("user", {}).get("id"),
                    "avatar_url": pr.get("user", {}).get("avatar_url"),
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
                "first_review_at": None,
                "first_commit_at": None,
                "labels": [label.get("name") for label in pr.get("labels", [])],
                "html_url": pr.get("html_url"),
            })
        
        # Store PRs in database
        stored_prs = []
        for i, pr_data in enumerate(detailed_prs):
            try:
                if i < 5:  # Only show detailed debug for first 5 PRs
                    print(f"  💾 Storing PR #{pr_data.get('number', 'unknown')}...")
                # Find or create user
                user = await self._get_or_create_user(pr_data["user"])
                if i < 5:  # Only show detailed debug for first 5 PRs
                    print(f"    User: {user.username} (ID: {user.id})")
                
                # Check if PR already exists
                from app.repositories import PullRequestRepository
                pr_repo = PullRequestRepository(PullRequest, self.db_session)
                try:
                    existing_pr = await pr_repo.get_by("github_pr_id", pr_data["number"], unique=True)
                except Exception:
                    existing_pr = None
                
                if existing_pr:
                    if i < 5:  # Only show detailed debug for first 5 PRs
                        print(f"    ⚠️  PR #{pr_data.get('number', 'unknown')} already exists, updating...")
                    # Update existing PR
                    existing_pr.title = pr_data["title"]
                    existing_pr.description = pr_data["description"]
                    existing_pr.status = pr_data["state"]
                    existing_pr.labels = pr_data["labels"]
                    existing_pr.unresolved_comments = pr_data.get("comments", 0) + pr_data.get("review_comments", 0)
                    existing_pr.lines_changed = pr_data.get("additions", 0) + pr_data.get("deletions", 0)
                    existing_pr.additions = pr_data.get("additions", 0)
                    existing_pr.deletions = pr_data.get("deletions", 0)
                    existing_pr.changed_files = pr_data.get("changed_files", 0)
                    existing_pr.merged_at = datetime.fromisoformat(pr_data["merged_at"].replace('Z', '+00:00')) if pr_data["merged_at"] else None
                    existing_pr.closed_at = datetime.fromisoformat(pr_data["closed_at"].replace('Z', '+00:00')) if pr_data["closed_at"] else None
                    existing_pr.flow_blockers = self._analyze_flow_blockers(pr_data)
                    existing_pr.risk_flags = self._analyze_risk_flags(pr_data)
                    stored_prs.append(existing_pr)
                    if i < 5:  # Only show detailed debug for first 5 PRs
                        print(f"    ✅ PR #{pr_data.get('number', 'unknown')} updated successfully")
                else:
                    # Create new PR record
                    if i < 5:  # Only show detailed debug for first 5 PRs
                        print(f"    Creating new PullRequest object...")
                    pr = PullRequest(
                        github_pr_id=pr_data["number"],
                        title=pr_data["title"],
                        description=pr_data["description"],
                        github_url=pr_data["html_url"],
                        status=pr_data["state"],
                        labels=pr_data["labels"],
                        unresolved_comments=pr_data.get("comments", 0) + pr_data.get("review_comments", 0),
                        lines_changed=pr_data.get("additions", 0) + pr_data.get("deletions", 0),
                        additions=pr_data.get("additions", 0),
                        deletions=pr_data.get("deletions", 0),
                        changed_files=pr_data.get("changed_files", 0),
                        merged_at=datetime.fromisoformat(pr_data["merged_at"].replace('Z', '+00:00')) if pr_data["merged_at"] else None,
                        closed_at=datetime.fromisoformat(pr_data["closed_at"].replace('Z', '+00:00')) if pr_data["closed_at"] else None,
                        first_review_at=None, # Simplified to avoid detailed fetching
                        first_commit_at=None, # Simplified to avoid detailed fetching
                        author_id=user.id,
                        flow_blockers=self._analyze_flow_blockers(pr_data),
                        risk_flags=self._analyze_risk_flags(pr_data),
                    )
                    
                    self.db_session.add(pr)
                    stored_prs.append(pr)
                    if i < 5:  # Only show detailed debug for first 5 PRs
                        print(f"    ✅ PR #{pr_data.get('number', 'unknown')} stored successfully")
            except Exception as e:
                print(f"  ⚠️  Error processing PR #{pr_data.get('number', 'unknown')}: {e}")
                # Rollback the session to clear any failed state
                await self.db_session.rollback()
                continue
        
        await self.db_session.commit()
        print(f"  ✅ Successfully stored {len(stored_prs)} PRs in database")
        
        return {
            "repository": f"{owner}/{repo}",
            "total_prs": len(stored_prs),
            "open_prs": len([pr for pr in stored_prs if pr.status == "open"]),
            "merged_prs": len([pr for pr in stored_prs if pr.status == "merged"]),
            "api_requests_made": self.client.requests_made,
        }
    
    
    async def _get_or_create_user(self, user_data: Dict[str, Any]) -> User:
        """Get or create user from GitHub data"""
        from app.repositories import UserRepository
        user_repo = UserRepository(User, self.db_session)
        
        # Validate user_data structure
        if not isinstance(user_data, dict):
            print(f"⚠️  Invalid user_data type: {type(user_data)}")
            # Create a fallback user
            user_data = {"login": "unknown", "id": None, "avatar_url": None}
        
        if not user_data.get("id") or not user_data.get("login"):
            print(f"⚠️  Missing required user data: {user_data}")
            # Create a fallback user
            user_data = {"login": "unknown", "id": None, "avatar_url": None}
        
        # Try to find by GitHub ID first
        if user_data.get("id"):
            try:
                existing_user = await user_repo.get_by("github_id", user_data["id"], unique=True)
                if existing_user:
                    return existing_user
            except Exception:
                pass  # User not found, continue to create new one
        
        # Try to find by username
        if user_data.get("login"):
            try:
                existing_user = await user_repo.get_by("username", user_data["login"], unique=True)
                if existing_user:
                    # Update with GitHub data
                    if user_data.get("id"):
                        existing_user.github_id = user_data["id"]
                    if user_data.get("avatar_url"):
                        existing_user.github_avatar_url = user_data["avatar_url"]
                    await self.db_session.commit()
                    return existing_user
            except Exception:
                pass  # User not found, continue to create new one
        
        # Create new user
        user = User(
            username=user_data.get("login", "unknown"),
            email=f"{user_data.get('login', 'unknown')}@github.local",  # Placeholder email
            password="",  # Will be set by OAuth flow
            github_id=user_data.get("id"),
            github_avatar_url=user_data.get("avatar_url"),
        )
        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)
        
        # Create team member profile
        team_member = TeamMember(
            user_id=user.id,
            primary_status=PrimaryStatus.BALANCED.value,
            last_active_at=datetime.now(timezone.utc),
        )
        self.db_session.add(team_member)
        await self.db_session.commit()
        
        return user
    
    def _analyze_flow_blockers(self, pr_data: Dict[str, Any]) -> List[str]:
        """Analyze PR for flow blockers"""
        blockers = []
        
        # Check for stale PRs (open for >7 days)
        if pr_data["state"] == "open":
            created_at = datetime.fromisoformat(pr_data["created_at"].replace('Z', '+00:00'))
            if created_at < datetime.now(timezone.utc) - timedelta(days=7):
                blockers.append(FlowBlocker.IDLE_PR.value)
        
        # Check for high review comments
        if pr_data.get("review_comments", 0) > 10:
            blockers.append(FlowBlocker.REVIEW_STALEMATE.value)
        
        # Check for missing tests (heuristic based on changed files)
        if pr_data.get("changed_files", 0) > 5 and not any("test" in label.lower() for label in pr_data.get("labels", [])):
            blockers.append(FlowBlocker.MISSING_TESTS.value)
        
        return blockers
    
    def _analyze_risk_flags(self, pr_data: Dict[str, Any]) -> List[str]:
        """Analyze PR for risk flags"""
        flags = []
        
        # Calculate lines_changed from additions and deletions
        lines_changed = pr_data.get("additions", 0) + pr_data.get("deletions", 0)
        
        # Large changes
        if lines_changed > 1000:
            flags.append(RiskFlag.LARGE_BLAST_RADIUS.value)
        
        # Many files changed
        if pr_data.get("changed_files", 0) > 20:
            flags.append(RiskFlag.LARGE_BLAST_RADIUS.value)
        
        # Critical files (heuristic)
        critical_files = ["auth", "security", "database", "migration"]
        if any(critical in pr_data.get("title", "").lower() for critical in critical_files):
            flags.append(RiskFlag.CRITICAL_FILE_CHANGE.value)
        
        return flags
    
    async def _create_timeline_events(self, prs: List[PullRequest], owner: str, repo: str):
        """Create timeline events for PRs"""
        for pr in prs:
            # PR opened event
            event = Event(
                team_member_id=pr.author.team_member_profile.id if pr.author.team_member_profile else None,
                event_type=EventType.PR_OPENED.value,
                timestamp=pr.created_at,
                title=f"Opened PR #{pr.github_pr_id}: {pr.title}",
                description=f"Opened pull request in {owner}/{repo}",
                pr_id=pr.id,
                event_metadata={"repository": f"{owner}/{repo}"}
            )
            self.db_session.add(event)
            
            # PR merged event
            if pr.status == "merged" and pr.merged_at:
                event = Event(
                    team_member_id=pr.author.team_member_profile.id if pr.author.team_member_profile else None,
                    event_type=EventType.PR_MERGED.value,
                    timestamp=pr.merged_at,
                    title=f"Merged PR #{pr.github_pr_id}: {pr.title}",
                    description=f"Merged pull request in {owner}/{repo}",
                    pr_id=pr.id,
                    event_metadata={"repository": f"{owner}/{repo}"}
                )
                self.db_session.add(event)
        
        await self.db_session.commit()
    
    async def _update_team_member_metrics(self, prs: List[PullRequest]):
        """Update team member metrics based on PR data"""
        # Group PRs by author
        author_prs = {}
        for pr in prs:
            if pr.author_id not in author_prs:
                author_prs[pr.author_id] = []
            author_prs[pr.author_id].append(pr)
        
        # Update metrics for each author
        for author_id, author_pr_list in author_prs.items():
            team_member = await self.team_member_repository.get_by_user_id(author_id)
            if not team_member:
                continue
            
            # Calculate metrics
            open_prs = [pr for pr in author_pr_list if pr.status == "open"]
            merged_prs = [pr for pr in author_pr_list if pr.status == "merged"]
            
            # Update basic counts
            team_member.wip_count = len(open_prs)
            team_member.merged_prs_last_30_days = len(merged_prs)
            
            # Calculate average cycle time
            cycle_times = []
            for pr in merged_prs:
                if pr.created_at and pr.merged_at:
                    delta = pr.merged_at - pr.created_at
                    cycle_times.append(delta.total_seconds() / 3600)  # hours
            
            if cycle_times:
                team_member.avg_cycle_time_hours = sum(cycle_times) / len(cycle_times)
            
            # Calculate work focus distribution
            total_prs = len(author_pr_list)
            if total_prs > 0:
                feature_prs = len([pr for pr in author_pr_list if any("feat" in label.lower() for label in (pr.labels or []))])
                bug_prs = len([pr for pr in author_pr_list if any("bug" in label.lower() for label in (pr.labels or []))])
                chore_prs = len([pr for pr in author_pr_list if any("chore" in label.lower() for label in (pr.labels or []))])
                
                team_member.features_percentage = (feature_prs / total_prs) * 100
                team_member.bugs_percentage = (bug_prs / total_prs) * 100
                team_member.chores_percentage = (chore_prs / total_prs) * 100
            
            # Update last active
            if author_pr_list:
                latest_pr = max(author_pr_list, key=lambda p: p.created_at)
                team_member.last_active_at = latest_pr.created_at
            
            # Update primary status based on workload
            if team_member.wip_count > 5:
                team_member.primary_status = PrimaryStatus.OVERLOADED.value
            elif team_member.wip_count == 0 and team_member.merged_prs_last_30_days > 10:
                team_member.primary_status = PrimaryStatus.BALANCED.value
            
            await self.db_session.commit()
