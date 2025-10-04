"""
Enhanced GitHub Data Fetcher for Public Repositories
Fetches comprehensive PR data including metadata, CI/CD, reviewers, file changes, etc.
"""

import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models import PullRequest, User, TeamMember
from app.models.enums import PrimaryStatus, FlowBlocker, RiskFlag
from app.repositories import PullRequestRepository, UserRepository, TeamMemberRepository


class EnhancedGitHubAPIClient:
    """Enhanced GitHub API client with comprehensive data fetching capabilities"""
    
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
            if max_items and len(items) >= max_items:
                break
                
            params.update({"per_page": per_page, "page": page})
            resp = await self.get(url, params=params)
            chunk = resp.json()
            
            if not isinstance(chunk, list) or len(chunk) == 0:
                break
            
            if max_items:
                remaining_needed = max_items - len(items)
                items.extend(chunk[:remaining_needed])
            else:
                items.extend(chunk)
            
            print(f"  📄 Fetched page {page}, got {len(chunk)} items ({len(items)} total)")
            
            if len(chunk) < per_page:
                break
                
            page += 1
        
        return items


class EnhancedGitHubFetcher:
    """Enhanced GitHub fetcher for comprehensive PR data analysis"""
    
    def __init__(self, access_token: str, db_session: AsyncSession):
        self.client = EnhancedGitHubAPIClient(access_token)
        self.db_session = db_session
        self.pr_repository = PullRequestRepository(PullRequest, db_session)
        self.user_repository = UserRepository(User, db_session)
        self.team_member_repository = TeamMemberRepository(TeamMember, db_session)
    
    async def fetch_comprehensive_repository_data(self, owner: str, repo: str, days: int = 30) -> Dict[str, Any]:
        """Fetch comprehensive repository data with all metadata"""
        print(f"🔍 Fetching comprehensive data for {owner}/{repo} (last {days} days)...")
        
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Check what data we already have in DB
        existing_prs = await self._get_existing_prs(owner, repo, since)
        existing_pr_numbers = {pr.github_pr_id for pr in existing_prs}
        
        print(f"📊 Found {len(existing_prs)} existing PRs in database")
        
        # Fetch all PRs from GitHub
        print("📥 Fetching PRs from GitHub...")
        prs_url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls"
        all_prs = await self.client.get_paginated_limited(prs_url, params={
            "state": "all", 
            "sort": "created", 
            "direction": "desc"
        }, max_items=200)
        
        # Filter PRs by date and exclude existing ones
        filtered_prs = [
            pr for pr in all_prs 
            if pr.get("created_at", "") >= since and pr.get("number") not in existing_pr_numbers
        ]
        
        print(f"✅ Found {len(filtered_prs)} new PRs to process")
        
        # Process each PR with comprehensive data
        processed_prs = []
        for i, pr in enumerate(filtered_prs):
            try:
                print(f"🔍 Processing PR #{pr.get('number')} ({i+1}/{len(filtered_prs)})...")
                comprehensive_pr_data = await self._fetch_comprehensive_pr_data(owner, repo, pr)
                processed_prs.append(comprehensive_pr_data)
            except Exception as e:
                print(f"⚠️  Error processing PR #{pr.get('number')}: {e}")
                continue
        
        # Store processed PRs in database
        stored_prs = []
        for pr_data in processed_prs:
            try:
                stored_pr = await self._store_comprehensive_pr(pr_data)
                stored_prs.append(stored_pr)
            except Exception as e:
                print(f"⚠️  Error storing PR #{pr_data.get('number')}: {e}")
                continue
        
        await self.db_session.commit()
        print(f"✅ Successfully stored {len(stored_prs)} comprehensive PRs")
        
        return {
            "repository": f"{owner}/{repo}",
            "total_prs": len(stored_prs) + len(existing_prs),
            "new_prs": len(stored_prs),
            "existing_prs": len(existing_prs),
            "open_prs": len([pr for pr in stored_prs if pr.status == "open"]),
            "merged_prs": len([pr for pr in stored_prs if pr.status == "merged"]),
            "api_requests_made": self.client.requests_made,
        }
    
    async def _get_existing_prs(self, owner: str, repo: str, since: str) -> List[PullRequest]:
        """Get existing PRs from database for this repository"""
        try:
            # Query PRs by repository info
            query = text("""
                SELECT * FROM pull_requests 
                WHERE repository_info->>'owner' = :owner 
                AND repository_info->>'repo' = :repo
                AND created_at >= :since
            """)
            result = await self.db_session.execute(
                query, 
                {"owner": owner, "repo": repo, "since": since}
            )
            return result.fetchall()
        except Exception as e:
            print(f"⚠️  Error fetching existing PRs: {e}")
            return []
    
    async def _fetch_comprehensive_pr_data(self, owner: str, repo: str, pr: dict) -> dict:
        """Fetch comprehensive data for a single PR"""
        pr_number = pr.get("number")
        
        # Base PR data
        pr_data = {
            "number": pr_number,
            "title": pr.get("title"),
            "description": pr.get("body", ""),
            "user": pr.get("user", {}),
            "state": pr.get("state"),
            "created_at": pr.get("created_at"),
            "merged_at": pr.get("merged_at"),
            "closed_at": pr.get("closed_at"),
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0),
            "changed_files": pr.get("changed_files", 0),
            "html_url": pr.get("html_url"),
            "labels": [label.get("name") for label in pr.get("labels", [])],
            "repository_info": {"owner": owner, "repo": repo}
        }
        
        # Fetch comprehensive metadata
        pr_data["pr_metadata"] = await self._fetch_pr_metadata(owner, repo, pr_number)
        pr_data["cicd_metadata"] = await self._fetch_cicd_metadata(owner, repo, pr_number)
        pr_data["time_cycle_metadata"] = await self._fetch_time_cycle_metadata(owner, repo, pr_number)
        pr_data["reviewers_metadata"] = await self._fetch_reviewers_metadata(owner, repo, pr_number)
        pr_data["file_changes_metadata"] = await self._fetch_file_changes_metadata(owner, repo, pr_number)
        pr_data["linked_issues_metadata"] = await self._fetch_linked_issues_metadata(owner, repo, pr_number)
        pr_data["git_blame_metadata"] = await self._fetch_git_blame_metadata(owner, repo, pr_number)
        
        return pr_data
    
    async def _fetch_pr_metadata(self, owner: str, repo: str, pr_number: int) -> dict:
        """Fetch PR metadata: description, labels, comments"""
        try:
            # Get detailed PR info
            pr_url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
            pr_resp = await self.client.get(pr_url)
            pr_details = pr_resp.json()
            
            # Get comments
            comments_url = f"{self.client.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
            comments_resp = await self.client.get(comments_url)
            comments = comments_resp.json()
            
            # Get review comments
            review_comments_url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
            review_comments_resp = await self.client.get(review_comments_url)
            review_comments = review_comments_resp.json()
            
            return {
                "description": pr_details.get("body", ""),
                "labels": [label.get("name") for label in pr_details.get("labels", [])],
                "comments_count": len(comments),
                "review_comments_count": len(review_comments),
                "comments": [
                    {
                        "author": comment.get("user", {}).get("login"),
                        "body": comment.get("body", ""),
                        "created_at": comment.get("created_at"),
                        "type": "comment"
                    } for comment in comments
                ],
                "review_comments": [
                    {
                        "author": comment.get("user", {}).get("login"),
                        "body": comment.get("body", ""),
                        "created_at": comment.get("created_at"),
                        "path": comment.get("path"),
                        "position": comment.get("position"),
                        "type": "review_comment"
                    } for comment in review_comments
                ]
            }
        except Exception as e:
            print(f"⚠️  Error fetching PR metadata for #{pr_number}: {e}")
            return {}
    
    async def _fetch_cicd_metadata(self, owner: str, repo: str, pr_number: int) -> dict:
        """Fetch CI/CD checks and status"""
        try:
            # Get check runs
            checks_url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/checks"
            checks_resp = await self.client.get(checks_url)
            checks_data = checks_resp.json()
            
            # Get status checks
            status_url = f"{self.client.base_url}/repos/{owner}/{repo}/commits/{pr_number}/status"
            status_resp = await self.client.get(status_url)
            status_data = status_resp.json()
            
            # Analyze CI/CD status
            check_runs = checks_data.get("check_runs", [])
            statuses = status_data.get("statuses", [])
            
            failing_checks = []
            passing_checks = []
            
            for check in check_runs:
                if check.get("conclusion") == "failure":
                    failing_checks.append({
                        "name": check.get("name"),
                        "conclusion": check.get("conclusion"),
                        "started_at": check.get("started_at"),
                        "completed_at": check.get("completed_at")
                    })
                elif check.get("conclusion") == "success":
                    passing_checks.append({
                        "name": check.get("name"),
                        "conclusion": check.get("conclusion"),
                        "started_at": check.get("started_at"),
                        "completed_at": check.get("completed_at")
                    })
            
            return {
                "check_runs": check_runs,
                "statuses": statuses,
                "failing_checks": failing_checks,
                "passing_checks": passing_checks,
                "overall_status": "failure" if failing_checks else "success" if passing_checks else "pending",
                "consistently_failing": len(failing_checks) > 0
            }
        except Exception as e:
            print(f"⚠️  Error fetching CI/CD metadata for #{pr_number}: {e}")
            return {}
    
    async def _fetch_time_cycle_metadata(self, owner: str, repo: str, pr_number: int) -> dict:
        """Fetch time cycle analysis"""
        try:
            # Get PR timeline events
            events_url = f"{self.client.base_url}/repos/{owner}/{repo}/issues/{pr_number}/timeline"
            events_resp = await self.client.get(events_url)
            events = events_resp.json()
            
            # Get commits
            commits_url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/commits"
            commits_resp = await self.client.get(commits_url)
            commits = commits_resp.json()
            
            # Analyze time cycle
            timeline_events = []
            for event in events:
                timeline_events.append({
                    "event": event.get("event"),
                    "created_at": event.get("created_at"),
                    "actor": event.get("actor", {}).get("login") if event.get("actor") else None
                })
            
            return {
                "timeline_events": timeline_events,
                "commits_count": len(commits),
                "commits": [
                    {
                        "sha": commit.get("sha"),
                        "message": commit.get("commit", {}).get("message"),
                        "author": commit.get("commit", {}).get("author", {}).get("name"),
                        "date": commit.get("commit", {}).get("author", {}).get("date")
                    } for commit in commits
                ]
            }
        except Exception as e:
            print(f"⚠️  Error fetching time cycle metadata for #{pr_number}: {e}")
            return {}
    
    async def _fetch_reviewers_metadata(self, owner: str, repo: str, pr_number: int) -> dict:
        """Fetch code reviewers and review status"""
        try:
            # Get review requests
            review_requests_url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers"
            review_requests_resp = await self.client.get(review_requests_url)
            review_requests = review_requests_resp.json()
            
            # Get reviews
            reviews_url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
            reviews_resp = await self.client.get(reviews_url)
            reviews = reviews_resp.json()
            
            # Analyze reviewers
            requested_reviewers = review_requests.get("users", [])
            team_reviewers = review_requests.get("teams", [])
            
            reviewer_status = {}
            for reviewer in requested_reviewers:
                reviewer_status[reviewer.get("login")] = {
                    "requested": True,
                    "reviewed": False,
                    "review_state": None
                }
            
            for review in reviews:
                reviewer = review.get("user", {}).get("login")
                if reviewer in reviewer_status:
                    reviewer_status[reviewer]["reviewed"] = True
                    reviewer_status[reviewer]["review_state"] = review.get("state")
                    reviewer_status[reviewer]["reviewed_at"] = review.get("submitted_at")
            
            return {
                "requested_reviewers": requested_reviewers,
                "team_reviewers": team_reviewers,
                "reviews": reviews,
                "reviewer_status": reviewer_status,
                "total_reviews": len(reviews),
                "approved_reviews": len([r for r in reviews if r.get("state") == "APPROVED"]),
                "changes_requested": len([r for r in reviews if r.get("state") == "CHANGES_REQUESTED"])
            }
        except Exception as e:
            print(f"⚠️  Error fetching reviewers metadata for #{pr_number}: {e}")
            return {}
    
    async def _fetch_file_changes_metadata(self, owner: str, repo: str, pr_number: int) -> dict:
        """Fetch LOC changes for each file"""
        try:
            # Get files changed
            files_url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
            files_resp = await self.client.get(files_url)
            files = files_resp.json()
            
            file_changes = []
            total_additions = 0
            total_deletions = 0
            
            for file in files:
                file_data = {
                    "filename": file.get("filename"),
                    "status": file.get("status"),
                    "additions": file.get("additions", 0),
                    "deletions": file.get("deletions", 0),
                    "changes": file.get("changes", 0),
                    "patch": file.get("patch", ""),
                    "blob_url": file.get("blob_url"),
                    "raw_url": file.get("raw_url")
                }
                file_changes.append(file_data)
                total_additions += file_data["additions"]
                total_deletions += file_data["deletions"]
            
            return {
                "files": file_changes,
                "total_additions": total_additions,
                "total_deletions": total_deletions,
                "total_changes": total_additions + total_deletions,
                "files_count": len(file_changes)
            }
        except Exception as e:
            print(f"⚠️  Error fetching file changes metadata for #{pr_number}: {e}")
            return {}
    
    async def _fetch_linked_issues_metadata(self, owner: str, repo: str, pr_number: int) -> dict:
        """Fetch linked issues (GitHub, Jira, Linear)"""
        try:
            # Get PR details to extract issue links from description
            pr_url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
            pr_resp = await self.client.get(pr_url)
            pr_details = pr_resp.json()
            
            description = pr_details.get("body", "")
            
            # Extract GitHub issue links
            github_issues = re.findall(r'#(\d+)', description)
            
            # Extract Jira links (common patterns)
            jira_issues = re.findall(r'([A-Z]+-\d+)', description)
            
            # Extract Linear links (common patterns)
            linear_issues = re.findall(r'([A-Z]+-\d+)', description)  # Similar to Jira
            
            # Get GitHub issues details
            github_issues_details = []
            for issue_num in github_issues[:5]:  # Limit to 5 issues
                try:
                    issue_url = f"{self.client.base_url}/repos/{owner}/{repo}/issues/{issue_num}"
                    issue_resp = await self.client.get(issue_url)
                    issue_data = issue_resp.json()
                    github_issues_details.append({
                        "number": issue_num,
                        "title": issue_data.get("title"),
                        "state": issue_data.get("state"),
                        "url": issue_data.get("html_url")
                    })
                except:
                    continue
            
            return {
                "github_issues": github_issues_details,
                "jira_issues": jira_issues,
                "linear_issues": linear_issues,
                "total_linked_issues": len(github_issues) + len(jira_issues) + len(linear_issues)
            }
        except Exception as e:
            print(f"⚠️  Error fetching linked issues metadata for #{pr_number}: {e}")
            return {}
    
    async def _fetch_git_blame_metadata(self, owner: str, repo: str, pr_number: int) -> dict:
        """Fetch git blame information for changed files"""
        try:
            # Get files changed
            files_url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
            files_resp = await self.client.get(files_url)
            files = files_resp.json()
            
            blame_data = []
            
            # For each changed file, get blame information
            for file in files[:5]:  # Limit to 5 files to avoid rate limits
                try:
                    filename = file.get("filename")
                    if filename and file.get("status") != "deleted":
                        # Get blame for the file
                        blame_url = f"{self.client.base_url}/repos/{owner}/{repo}/contents/{filename}"
                        blame_resp = await self.client.get(blame_url, params={"ref": "HEAD"})
                        # Note: GitHub API doesn't have direct blame endpoint, 
                        # this is a simplified version
                        blame_data.append({
                            "filename": filename,
                            "status": file.get("status"),
                            "changes": file.get("changes", 0)
                        })
                except:
                    continue
            
            return {
                "files_blame": blame_data,
                "total_files_analyzed": len(blame_data)
            }
        except Exception as e:
            print(f"⚠️  Error fetching git blame metadata for #{pr_number}: {e}")
            return {}
    
    async def _store_comprehensive_pr(self, pr_data: dict) -> PullRequest:
        """Store comprehensive PR data in database"""
        # Get or create user
        user = await self._get_or_create_user(pr_data["user"])
        
        # Check if PR already exists
        try:
            existing_pr = await self.pr_repository.get_by("github_pr_id", pr_data["number"], unique=True)
            if existing_pr:
                # Update existing PR
                existing_pr.title = pr_data["title"]
                existing_pr.description = pr_data["description"]
                existing_pr.status = pr_data["state"]
                existing_pr.labels = pr_data["labels"]
                existing_pr.additions = pr_data["additions"]
                existing_pr.deletions = pr_data["deletions"]
                existing_pr.changed_files = pr_data["changed_files"]
                existing_pr.merged_at = datetime.fromisoformat(pr_data["merged_at"].replace('Z', '+00:00')) if pr_data["merged_at"] else None
                existing_pr.closed_at = datetime.fromisoformat(pr_data["closed_at"].replace('Z', '+00:00')) if pr_data["closed_at"] else None
                
                # Update metadata
                existing_pr.pr_metadata = pr_data.get("pr_metadata", {})
                existing_pr.cicd_metadata = pr_data.get("cicd_metadata", {})
                existing_pr.time_cycle_metadata = pr_data.get("time_cycle_metadata", {})
                existing_pr.reviewers_metadata = pr_data.get("reviewers_metadata", {})
                existing_pr.file_changes_metadata = pr_data.get("file_changes_metadata", {})
                existing_pr.linked_issues_metadata = pr_data.get("linked_issues_metadata", {})
                existing_pr.git_blame_metadata = pr_data.get("git_blame_metadata", {})
                existing_pr.repository_info = pr_data.get("repository_info", {})
                
                return existing_pr
        except Exception:
            pass  # PR doesn't exist, create new one
        
        # Create new PR
        pr = PullRequest(
            github_pr_id=pr_data["number"],
            title=pr_data["title"],
            description=pr_data["description"],
            github_url=pr_data["html_url"],
            status=pr_data["state"],
            labels=pr_data["labels"],
            additions=pr_data["additions"],
            deletions=pr_data["deletions"],
            changed_files=pr_data["changed_files"],
            merged_at=datetime.fromisoformat(pr_data["merged_at"].replace('Z', '+00:00')) if pr_data["merged_at"] else None,
            closed_at=datetime.fromisoformat(pr_data["closed_at"].replace('Z', '+00:00')) if pr_data["closed_at"] else None,
            author_id=user.id,
            pr_metadata=pr_data.get("pr_metadata", {}),
            cicd_metadata=pr_data.get("cicd_metadata", {}),
            time_cycle_metadata=pr_data.get("time_cycle_metadata", {}),
            reviewers_metadata=pr_data.get("reviewers_metadata", {}),
            file_changes_metadata=pr_data.get("file_changes_metadata", {}),
            linked_issues_metadata=pr_data.get("linked_issues_metadata", {}),
            git_blame_metadata=pr_data.get("git_blame_metadata", {}),
            repository_info=pr_data.get("repository_info", {}),
            flow_blockers=self._analyze_flow_blockers(pr_data),
            risk_flags=self._analyze_risk_flags(pr_data),
        )
        
        self.db_session.add(pr)
        return pr
    
    async def _get_or_create_user(self, user_data: Dict[str, Any]) -> User:
        """Get or create user from GitHub data"""
        if not isinstance(user_data, dict) or not user_data.get("id") or not user_data.get("login"):
            user_data = {"login": "unknown", "id": None, "avatar_url": None}
        
        # Try to find by GitHub ID first
        if user_data.get("id"):
            try:
                existing_user = await self.user_repository.get_by("github_id", user_data["id"], unique=True)
                if existing_user:
                    return existing_user
            except Exception:
                pass
        
        # Try to find by username
        if user_data.get("login"):
            try:
                existing_user = await self.user_repository.get_by("username", user_data["login"], unique=True)
                if existing_user:
                    if user_data.get("id"):
                        existing_user.github_id = user_data["id"]
                    if user_data.get("avatar_url"):
                        existing_user.github_avatar_url = user_data["avatar_url"]
                    await self.db_session.commit()
                    return existing_user
            except Exception:
                pass
        
        # Create new user
        user = User(
            username=user_data.get("login", "unknown"),
            email=f"{user_data.get('login', 'unknown')}@github.local",
            password="",
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
        
        if pr_data["state"] == "open":
            created_at = datetime.fromisoformat(pr_data["created_at"].replace('Z', '+00:00'))
            if created_at < datetime.now(timezone.utc) - timedelta(days=7):
                blockers.append(FlowBlocker.IDLE_PR.value)
        
        if pr_data.get("review_comments", 0) > 10:
            blockers.append(FlowBlocker.REVIEW_STALEMATE.value)
        
        if pr_data.get("changed_files", 0) > 5 and not any("test" in label.lower() for label in pr_data.get("labels", [])):
            blockers.append(FlowBlocker.MISSING_TESTS.value)
        
        return blockers
    
    def _analyze_risk_flags(self, pr_data: Dict[str, Any]) -> List[str]:
        """Analyze PR for risk flags"""
        flags = []
        
        lines_changed = pr_data.get("additions", 0) + pr_data.get("deletions", 0)
        
        if lines_changed > 1000:
            flags.append(RiskFlag.LARGE_BLAST_RADIUS.value)
        
        if pr_data.get("changed_files", 0) > 20:
            flags.append(RiskFlag.LARGE_BLAST_RADIUS.value)
        
        critical_files = ["auth", "security", "database", "migration"]
        if any(critical in pr_data.get("title", "").lower() for critical in critical_files):
            flags.append(RiskFlag.CRITICAL_FILE_CHANGE.value)
        
        return flags
