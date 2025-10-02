"""
PR Risk Analyzer
This module implements the comprehensive PR risk analysis engine.
"""

import re
import json
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Any
from pathlib import Path

import httpx

from .pr_risk_models import (
    PRRiskAnalysis,
    StucknessMetrics,
    BlastRadiusMetrics,
    DynamicsMetrics,
    BusinessImpactMetrics,
    CompositeRiskScore,
    RepositoryRiskReport,
    PRState,
    PRRiskDatabase,
    # New detailed models
    PRDetailedInfo,
    FileChange,
    CICheckRun,
    PRComment,
    PRLabel,
    LinkedIssue,
    PRTimelineMetrics,
    PRReviewSummary
)
from .github_fetcher import GitHubAPIClient

# Configure logging
import os

# Ensure logs directory exists
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Get log level from environment variable (default to WARNING for clean output)
log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
log_level_value = getattr(logging, log_level, logging.WARNING)

# Configure logger for this module only (don't mess with root logger)
logger = logging.getLogger(__name__)
logger.setLevel(log_level_value)

# Only add handlers if not already configured
if not logger.handlers:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler only (no console spam)
    file_handler = logging.FileHandler(logs_dir / 'pr_risk_analyzer.log')
    file_handler.setLevel(log_level_value)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# Suppress ALL verbose HTTP client logs
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)

# Prevent propagation to root logger
logger.propagate = False


class PRRiskAnalyzer:
    """Main class for analyzing PR risks"""
    
    def __init__(self, token: Optional[str] = None, storage_dir: Optional[str] = None):
        self.client = GitHubAPIClient(token)
        self.storage_dir = Path(storage_dir) if storage_dir else Path(__file__).parent / "pr_risk_data"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Critical paths configuration (can be customized per repo)
        self.critical_paths = [
            "/auth/", "/security/", "/payment/", "/api/", "/core/",
            "package.json", "requirements.txt", "Dockerfile", ".github/workflows/"
        ]
        
        # External dependencies patterns
        self.external_api_patterns = [
            r'https?://[^\s/$.?#].[^\s]*',  # HTTP URLs
            r'api\..*\.com',  # Common API patterns
            r'\.googleapis\.com',
            r'\.amazonaws\.com',
            r'\.azure\.com'
        ]
    
    def _get_database_path(self) -> Path:
        """Get path to the PR risk database file"""
        return self.storage_dir / "pr_risk_database.json"
    
    def _load_database(self) -> PRRiskDatabase:
        """Load PR risk database from file"""
        db_path = self._get_database_path()
        if db_path.exists():
            try:
                with open(db_path, 'r') as f:
                    data = json.load(f)
                return PRRiskDatabase.model_validate(data)
            except Exception as e:
                logger.warning(f"Could not load database: {e}")
        
        return PRRiskDatabase()
    
    def _save_database(self, db: PRRiskDatabase):
        """Save PR risk database to file"""
        db_path = self._get_database_path()
        with open(db_path, 'w') as f:
            json.dump(json.loads(db.model_dump_json()), f, indent=2)
    
    async def _get_pr_timeline(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get PR timeline events"""
        url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/timeline"
        resp = await self.client.get(url, headers={"Accept": "application/vnd.github.v3+json"})
        return resp.json() if resp.status_code == 200 else []
    
    async def _get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get PR reviews"""
        url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        resp = await self.client.get(url)
        return resp.json() if resp.status_code == 200 else []
    
    async def _get_pr_review_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get PR review comments"""
        url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        resp = await self.client.get(url)
        return resp.json() if resp.status_code == 200 else []
    
    async def _get_pr_commits(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get PR commits"""
        url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/commits"
        resp = await self.client.get(url)
        return resp.json() if resp.status_code == 200 else []
    
    async def _get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get PR file changes"""
        url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        resp = await self.client.get(url)
        return resp.json() if resp.status_code == 200 else []
    
    async def _get_pr_issue_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get issue comments (general PR comments)"""
        url = f"{self.client.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        resp = await self.client.get(url)
        return resp.json() if resp.status_code == 200 else []
    
    async def _get_linked_issues(self, owner: str, repo: str, issue_numbers: List[int]) -> List[Dict]:
        """Get details for linked issues"""
        issues = []
        for issue_num in issue_numbers:
            try:
                url = f"{self.client.base_url}/repos/{owner}/{repo}/issues/{issue_num}"
                resp = await self.client.get(url)
                if resp.status_code == 200:
                    issues.append(resp.json())
            except Exception as e:
                logger.warning(f"Failed to fetch issue #{issue_num}: {e}")
        return issues
    
    async def _collect_detailed_pr_info(self, owner: str, repo: str, pr_data: Dict, 
                                       files: List[Dict], commits: List[Dict],
                                       reviews: List[Dict], review_comments: List[Dict],
                                       issue_comments: List[Dict], check_runs: List[Dict]) -> PRDetailedInfo:
        """Collect comprehensive detailed information about a PR"""
        
        # Parse file changes
        file_changes = []
        total_additions = 0
        total_deletions = 0
        
        for file_info in files:
            additions = file_info.get("additions", 0)
            deletions = file_info.get("deletions", 0)
            total_additions += additions
            total_deletions += deletions
            
            file_changes.append(FileChange(
                filename=file_info.get("filename", ""),
                status=file_info.get("status", "unknown"),
                additions=additions,
                deletions=deletions,
                changes=file_info.get("changes", additions + deletions),
                patch=file_info.get("patch"),
                blob_url=file_info.get("blob_url"),
                previous_filename=file_info.get("previous_filename")
            ))
        
        # Parse CI/CD checks
        ci_checks = []
        passed_checks = 0
        failed_checks = 0
        
        for check in check_runs:
            conclusion = check.get("conclusion")
            if conclusion == "success":
                passed_checks += 1
            elif conclusion in ["failure", "timed_out", "action_required"]:
                failed_checks += 1
            
            started_at = None
            if check.get("started_at"):
                try:
                    started_at = datetime.fromisoformat(check["started_at"].replace("Z", "+00:00"))
                except:
                    pass
            
            completed_at = None
            if check.get("completed_at"):
                try:
                    completed_at = datetime.fromisoformat(check["completed_at"].replace("Z", "+00:00"))
                except:
                    pass
            
            ci_checks.append(CICheckRun(
                name=check.get("name", "Unknown"),
                status=check.get("status", "unknown"),
                conclusion=conclusion,
                started_at=started_at,
                completed_at=completed_at,
                html_url=check.get("html_url"),
                details_url=check.get("details_url")
            ))
        
        # Determine overall CI status
        if not ci_checks:
            ci_status = "unknown"
        elif failed_checks > 0:
            ci_status = "failure"
        elif any(c.status != "completed" for c in ci_checks):
            ci_status = "pending"
        elif passed_checks > 0:
            ci_status = "success"
        else:
            ci_status = "unknown"
        
        # Calculate timeline metrics
        pr_created = datetime.fromisoformat(pr_data["created_at"].replace("Z", "+00:00"))
        pr_merged = None
        if pr_data.get("merged_at"):
            pr_merged = datetime.fromisoformat(pr_data["merged_at"].replace("Z", "+00:00"))
        
        time_to_first_review = None
        time_to_first_approval = None
        time_to_merge = None
        
        if reviews:
            first_review_time = min(
                datetime.fromisoformat(r["submitted_at"].replace("Z", "+00:00")) 
                for r in reviews if r.get("submitted_at")
            )
            time_to_first_review = (first_review_time - pr_created).total_seconds() / 3600
            
            approved_reviews = [r for r in reviews if r.get("state") == "APPROVED"]
            if approved_reviews:
                first_approval_time = min(
                    datetime.fromisoformat(r["submitted_at"].replace("Z", "+00:00")) 
                    for r in approved_reviews if r.get("submitted_at")
                )
                time_to_first_approval = (first_approval_time - pr_created).total_seconds() / 3600
        
        if pr_merged:
            time_to_merge = (pr_merged - pr_created).total_seconds() / 3600
        
        # First and last commit times
        first_commit_at = None
        last_commit_at = None
        commit_authors = set()
        
        if commits:
            commit_dates = []
            for commit in commits:
                commit_date_str = commit.get("commit", {}).get("author", {}).get("date")
                if commit_date_str:
                    try:
                        commit_date = datetime.fromisoformat(commit_date_str.replace("Z", "+00:00"))
                        commit_dates.append(commit_date)
                    except:
                        pass
                
                # Collect commit authors
                author = commit.get("author", {}).get("login") or commit.get("commit", {}).get("author", {}).get("name")
                if author:
                    commit_authors.add(author)
            
            if commit_dates:
                first_commit_at = min(commit_dates)
                last_commit_at = max(commit_dates)
        
        time_from_first_to_last_commit = None
        if first_commit_at and last_commit_at:
            time_from_first_to_last_commit = (last_commit_at - first_commit_at).total_seconds() / 3600
        
        timeline_metrics = PRTimelineMetrics(
            time_to_first_review_hours=time_to_first_review,
            time_to_first_approval_hours=time_to_first_approval,
            time_to_merge_hours=time_to_merge,
            first_commit_at=first_commit_at,
            last_commit_at=last_commit_at,
            time_from_first_to_last_commit_hours=time_from_first_to_last_commit,
            number_of_review_cycles=len(reviews)
        )
        
        # Parse comments
        all_comments = []
        
        # Issue comments (general PR comments)
        for comment in issue_comments:
            try:
                all_comments.append(PRComment(
                    id=comment.get("id", 0),
                    author=comment.get("user", {}).get("login", "unknown"),
                    body=comment.get("body", ""),
                    created_at=datetime.fromisoformat(comment["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(comment["updated_at"].replace("Z", "+00:00")) if comment.get("updated_at") else None,
                    comment_type="issue_comment"
                ))
            except Exception as e:
                logger.warning(f"Failed to parse issue comment: {e}")
        
        # Review comments (inline code comments)
        for comment in review_comments:
            try:
                all_comments.append(PRComment(
                    id=comment.get("id", 0),
                    author=comment.get("user", {}).get("login", "unknown"),
                    body=comment.get("body", ""),
                    created_at=datetime.fromisoformat(comment["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(comment["updated_at"].replace("Z", "+00:00")) if comment.get("updated_at") else None,
                    comment_type="review_comment",
                    in_reply_to_id=comment.get("in_reply_to_id"),
                    path=comment.get("path"),
                    line=comment.get("line") or comment.get("original_line")
                ))
            except Exception as e:
                logger.warning(f"Failed to parse review comment: {e}")
        
        # Review summaries as comments
        review_comment_list = []
        for review in reviews:
            if review.get("body"):
                try:
                    review_comment = PRComment(
                        id=review.get("id", 0),
                        author=review.get("user", {}).get("login", "unknown"),
                        body=review.get("body", ""),
                        created_at=datetime.fromisoformat(review["submitted_at"].replace("Z", "+00:00")) if review.get("submitted_at") else pr_created,
                        comment_type="review"
                    )
                    all_comments.append(review_comment)
                    review_comment_list.append(review_comment)
                except Exception as e:
                    logger.warning(f"Failed to parse review: {e}")
        
        # Parse labels
        pr_labels = []
        for label in pr_data.get("labels", []):
            pr_labels.append(PRLabel(
                name=label.get("name", ""),
                color=label.get("color", ""),
                description=label.get("description")
            ))
        
        # Extract and fetch linked issues
        pr_body = pr_data.get("body", "") or ""
        comment_bodies = [c.body for c in all_comments]
        issue_numbers = self._extract_linked_issues(pr_body, comment_bodies)
        
        linked_issues_data = []
        if issue_numbers:
            logger.debug(f"   Found {len(issue_numbers)} linked issues: {issue_numbers}")
            issue_details = await self._get_linked_issues(owner, repo, issue_numbers)
            for issue in issue_details:
                try:
                    linked_issues_data.append(LinkedIssue(
                        number=issue.get("number", 0),
                        title=issue.get("title", ""),
                        state=issue.get("state", "unknown"),
                        url=issue.get("html_url", ""),
                        created_at=datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00")),
                        closed_at=datetime.fromisoformat(issue["closed_at"].replace("Z", "+00:00")) if issue.get("closed_at") else None,
                        labels=[l.get("name", "") for l in issue.get("labels", [])]
                    ))
                except Exception as e:
                    logger.warning(f"Failed to parse linked issue: {e}")
        
        # Review summary
        reviewers = list(set(r.get("user", {}).get("login", "") for r in reviews if r.get("user")))
        review_summary = PRReviewSummary(
            total_reviews=len(reviews),
            approved_count=len([r for r in reviews if r.get("state") == "APPROVED"]),
            changes_requested_count=len([r for r in reviews if r.get("state") == "CHANGES_REQUESTED"]),
            commented_count=len([r for r in reviews if r.get("state") == "COMMENTED"]),
            reviewers=reviewers,
            review_comments=review_comment_list
        )
        
        # Requested reviewers and assignees
        requested_reviewers = [r.get("login", "") for r in pr_data.get("requested_reviewers", [])]
        assignees = [a.get("login", "") for a in pr_data.get("assignees", [])]
        
        return PRDetailedInfo(
            description=pr_data.get("body"),
            body_text=pr_data.get("body"),
            files=file_changes,
            total_additions=total_additions,
            total_deletions=total_deletions,
            total_changes=total_additions + total_deletions,
            ci_checks=ci_checks,
            ci_status=ci_status,
            timeline_metrics=timeline_metrics,
            comments=all_comments,
            total_comments=len(all_comments),
            labels=pr_labels,
            linked_issues=linked_issues_data,
            review_summary=review_summary,
            commit_count=len(commits),
            commits_authors=list(commit_authors),
            mergeable=pr_data.get("mergeable"),
            mergeable_state=pr_data.get("mergeable_state"),
            draft=pr_data.get("draft", False),
            requested_reviewers=requested_reviewers,
            assignees=assignees
        )
    
    async def _get_check_runs(self, owner: str, repo: str, sha: str) -> List[Dict]:
        """Get check runs for a commit"""
        url = f"{self.client.base_url}/repos/{owner}/{repo}/commits/{sha}/check-runs"
        resp = await self.client.get(url)
        if resp.status_code == 200:
            return resp.json().get("check_runs", [])
        return []
    
    async def _get_author_pr_history(self, owner: str, repo: str, author: str, limit: int = 100) -> List[Dict]:
        """Get author's PR history in the repository"""
        url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls"
        resp = await self.client.get(url, params={
            "state": "all",
            "sort": "created",
            "direction": "desc",
            "per_page": limit
        })
        if resp.status_code == 200:
            all_prs = resp.json()
            return [pr for pr in all_prs if pr.get("user", {}).get("login") == author]
        return []
    
    def _calculate_author_experience(self, author_prs: List[Dict], current_pr_date: datetime) -> float:
        """Calculate author experience score (0-100)"""
        if not author_prs:
            return 0.0
        
        merged_prs = [pr for pr in author_prs if pr.get("merged_at")]
        total_prs = len(author_prs)
        
        # Experience factors
        merge_rate = len(merged_prs) / total_prs if total_prs > 0 else 0
        pr_count_score = min(total_prs * 5, 50)  # Cap at 50 for 10+ PRs
        
        # Recent activity bonus
        recent_prs = [
            pr for pr in author_prs 
            if datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00")) > 
            current_pr_date - timedelta(days=90)
        ]
        recency_score = min(len(recent_prs) * 10, 30)
        
        # Average PR size (smaller PRs = more experience)
        avg_size = 0
        if merged_prs:
            sizes = [pr.get("additions", 0) + pr.get("deletions", 0) for pr in merged_prs]
            avg_size = sum(sizes) / len(sizes) if sizes else 0
        
        size_score = 20 if avg_size < 100 else 15 if avg_size < 500 else 10 if avg_size < 1000 else 0
        
        total_score = (merge_rate * 30) + pr_count_score + recency_score + size_score
        return min(total_score, 100)
    
    def _count_external_dependencies(self, files_content: str, comments_content: str) -> int:
        """Count external API dependencies mentioned in code or comments"""
        combined_text = f"{files_content} {comments_content}"
        count = 0
        
        for pattern in self.external_api_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            count += len(set(matches))  # Unique matches only
        
        return count
    
    def _check_critical_paths(self, changed_files: List[str]) -> bool:
        """Check if any critical paths are touched"""
        for file_path in changed_files:
            for critical_path in self.critical_paths:
                if critical_path in file_path:
                    return True
        return False
    
    def _extract_linked_issues(self, pr_body: str, comments: List[str]) -> List[int]:
        """Extract linked issue numbers from PR body and comments"""
        all_text = f"{pr_body} {' '.join(comments)}"
        
        # Common issue linking patterns
        patterns = [
            r'(?:closes|fixes|resolves|close|fix|resolve)\s+#(\d+)',
            r'#(\d+)',
        ]
        
        issue_numbers = set()
        for pattern in patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            issue_numbers.update(int(match) for match in matches)
        
        return list(issue_numbers)
    
    async def _calculate_stuckness_metrics(self, pr_data: Dict, timeline: List[Dict], 
                                         reviews: List[Dict], comments: List[Dict],
                                         commits: List[Dict], check_runs: List[Dict]) -> StucknessMetrics:
        """Calculate stuckness metrics for a PR"""
        now = datetime.now(timezone.utc)
        pr_created = datetime.fromisoformat(pr_data["created_at"].replace("Z", "+00:00"))
        pr_updated = datetime.fromisoformat(pr_data["updated_at"].replace("Z", "+00:00"))
        
        # Time since last activity
        time_since_last_activity_hours = (now - pr_updated).total_seconds() / 3600
        
        # Unresolved review threads
        unresolved_threads = 0
        for comment in comments:
            if comment.get("in_reply_to_id") is None:  # Top-level comment
                # Count as unresolved if no resolution indicator
                unresolved_threads += 1
        
        # Failed CI checks
        failed_ci_checks = len([run for run in check_runs if run.get("conclusion") == "failure"])
        
        # Time waiting for reviewer
        time_waiting_for_reviewer_hours = 0.0
        last_author_activity = pr_updated
        
        # Find last activity by author
        for event in sorted(timeline, key=lambda x: x.get("created_at", "")):
            if event.get("actor", {}).get("login") == pr_data["user"]["login"]:
                event_time = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
                if event_time > last_author_activity:
                    last_author_activity = event_time
        
        time_waiting_for_reviewer_hours = (now - last_author_activity).total_seconds() / 3600
        
        # PR age
        pr_age_days = (now - pr_created).total_seconds() / (24 * 3600)
        
        # Rebase/force push count
        rebase_count = 0
        for commit in commits:
            # Look for force push indicators in commit messages
            message = commit.get("commit", {}).get("message", "").lower()
            if any(indicator in message for indicator in ["rebase", "force", "amend"]):
                rebase_count += 1
        
        # Comment velocity decay (simplified)
        comment_velocity_decay = 0.0
        if comments:
            recent_comments = [
                c for c in comments 
                if datetime.fromisoformat(c["created_at"].replace("Z", "+00:00")) > 
                now - timedelta(days=3)
            ]
            comment_velocity_decay = 1.0 - (len(recent_comments) / len(comments))
        
        # Linked issue stale time (simplified - would need issue API calls)
        linked_issue_stale_time_hours = 0.0  # Placeholder
        
        return StucknessMetrics(
            time_since_last_activity_hours=time_since_last_activity_hours,
            unresolved_review_threads=unresolved_threads,
            failed_ci_checks=failed_ci_checks,
            time_waiting_for_reviewer_hours=time_waiting_for_reviewer_hours,
            pr_age_days=pr_age_days,
            rebase_force_push_count=rebase_count,
            comment_velocity_decay=comment_velocity_decay,
            linked_issue_stale_time_hours=linked_issue_stale_time_hours
        )
    
    async def _calculate_blast_radius_metrics(self, pr_data: Dict, files: List[Dict],
                                            commits: List[Dict], pr_stats: Dict) -> BlastRadiusMetrics:
        """Calculate blast radius metrics for a PR"""
        
        # Use enhanced PR statistics when available
        lines_added = pr_stats.get("additions", pr_data.get("additions", 0))
        lines_removed = pr_stats.get("deletions", pr_data.get("deletions", 0))
        files_changed = pr_stats.get("changed_files", pr_data.get("changed_files", 0))
        
        # Critical path check
        changed_file_paths = [f.get("filename", "") for f in files]
        critical_path_touched = self._check_critical_paths(changed_file_paths)
        
        # Enhanced downstream dependencies analysis
        downstream_dependencies = 0
        if files_changed > 0:
            # More sophisticated dependency calculation
            for file_info in files:
                filename = file_info.get("filename", "")
                if any(ext in filename for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go']):
                    # Code files have higher dependency impact
                    downstream_dependencies += 2
                elif any(ext in filename for ext in ['.json', '.yaml', '.yml', '.toml', '.lock']):
                    # Config files have medium impact
                    downstream_dependencies += 1
                else:
                    # Other files have lower impact
                    downstream_dependencies += 0.5
            
            # Cap at reasonable maximum
            downstream_dependencies = min(downstream_dependencies, 50)
        
        # Test coverage delta (enhanced - analyze test files)
        test_coverage_delta = 0.0
        test_files = [f for f in files if any(test_indicator in f.get("filename", "").lower() 
                                             for test_indicator in ['test', 'spec', '__tests__'])]
        if test_files:
            test_coverage_delta = (len(test_files) / files_changed) * 100 if files_changed > 0 else 0
        
        # Historical regression risk (enhanced - analyze commit patterns)
        historical_regression_risk = 0.0
        if commits:
            # Look for patterns that might indicate regression risk
            risk_indicators = 0
            for commit in commits:
                message = commit.get("commit", {}).get("message", "").lower()
                if any(indicator in message for indicator in ['fix', 'bug', 'regression', 'revert', 'rollback']):
                    risk_indicators += 1
            
            historical_regression_risk = min(risk_indicators * 10, 100)
        
        return BlastRadiusMetrics(
            downstream_dependencies=downstream_dependencies,
            critical_path_touched=critical_path_touched,
            lines_added=lines_added,
            lines_removed=lines_removed,
            files_changed=files_changed,
            test_coverage_delta=test_coverage_delta,
            historical_regression_risk=historical_regression_risk
        )
    
    async def _calculate_dynamics_metrics(self, pr_data: Dict, reviews: List[Dict],
                                        author_prs: List[Dict], assignees: List[Dict]) -> DynamicsMetrics:
        """Calculate author/reviewer dynamics metrics"""
        
        pr_created = datetime.fromisoformat(pr_data["created_at"].replace("Z", "+00:00"))
        
        # Author experience
        author_experience_score = self._calculate_author_experience(author_prs, pr_created)
        
        # Enhanced reviewer load analysis
        requested_reviewers = pr_data.get("requested_reviewers", [])
        actual_assignees = pr_data.get("assignees", [])
        
        # Calculate total reviewer load
        reviewer_load = len(requested_reviewers) + len(actual_assignees)
        
        # If no explicit reviewers, estimate based on team size
        if reviewer_load == 0:
            # Estimate based on PR size and complexity
            pr_size = pr_data.get("additions", 0) + pr_data.get("deletions", 0)
            if pr_size > 1000:
                reviewer_load = 3  # Large PRs need more reviewers
            elif pr_size > 500:
                reviewer_load = 2  # Medium PRs need 2 reviewers
            else:
                reviewer_load = 1  # Small PRs need 1 reviewer
        
        # Approval ratio with enhanced logic
        total_reviews = len(reviews)
        approved_reviews = len([r for r in reviews if r.get("state") == "APPROVED"])
        changes_requested = len([r for r in reviews if r.get("state") == "CHANGES_REQUESTED"])
        
        if total_reviews > 0:
            approval_ratio = approved_reviews / total_reviews
            # Penalize for changes requested
            if changes_requested > 0:
                approval_ratio *= 0.8
        else:
            approval_ratio = 1.0  # No reviews yet
        
        # Enhanced average review time calculation
        avg_review_time_hours = 0.0
        if reviews:
            review_times = []
            for review in reviews:
                if review.get("submitted_at"):
                    review_time = datetime.fromisoformat(review["submitted_at"].replace("Z", "+00:00"))
                    time_diff = (review_time - pr_created).total_seconds() / 3600
                    if time_diff > 0:  # Only count positive time differences
                        review_times.append(time_diff)
            
            if review_times:
                avg_review_time_hours = sum(review_times) / len(review_times)
        
        # Enhanced author merge history
        author_merge_history = 0
        if author_prs:
            merged_prs = [pr for pr in author_prs if pr.get("merged_at")]
            author_merge_history = len(merged_prs)
        
        return DynamicsMetrics(
            author_experience_score=author_experience_score,
            reviewer_load=reviewer_load,
            approval_ratio=approval_ratio,
            author_merge_history=author_merge_history,
            avg_review_time_hours=avg_review_time_hours
        )
    
    async def _calculate_business_impact_metrics(self, pr_data: Dict, files: List[Dict], 
                                               labels: List[Dict], milestone: Optional[Dict], 
                                               dependencies: Dict) -> BusinessImpactMetrics:
        """Calculate business impact metrics"""
        
        # Enhanced label analysis
        pr_labels = pr_data.get("labels", [])
        label_names = [label.get("name", "").lower() for label in pr_labels]
        
        # Check for release milestone/labels with enhanced logic
        linked_to_release = any(
            any(release_indicator in label for release_indicator in 
                ["release", "milestone", "version", "v", "hotfix", "patch"])
            for label in label_names
        )
        
        # Enhanced priority label detection
        priority_label = None
        priority_keywords = ["critical", "high", "medium", "low", "priority", "urgent", "blocker"]
        for label in label_names:
            if any(priority in label for priority in priority_keywords):
                priority_label = label
                break
        
        # Enhanced external dependencies analysis
        files_content = " ".join([f.get("patch", "") for f in files])
        pr_body = pr_data.get("body", "")
        
        # Count external dependencies from multiple sources
        external_dependencies = self._count_external_dependencies(files_content, pr_body)
        
        # Add dependencies from enhanced analysis
        if dependencies:
            external_dependencies += dependencies.get("dependency_count", 0)
            external_dependencies += len(dependencies.get("third_party_services", []))
        
        # Enhanced core functionality detection
        core_indicators = ["core", "api", "auth", "security", "payment", "database", "infrastructure"]
        affects_core_functionality = any(
            any(indicator in label for indicator in core_indicators) 
            for label in label_names
        )
        
        # Additional business impact factors
        # Check for security-related changes
        security_impact = any(
            any(security_indicator in label for security_indicator in 
                ["security", "vulnerability", "cve", "security-fix"])
            for label in label_names
        )
        
        # Check for performance-related changes
        performance_impact = any(
            any(perf_indicator in label for perf_indicator in 
                ["performance", "optimization", "speed", "memory", "cpu"])
            for label in label_names
        )
        
        # Check for user-facing changes
        user_impact = any(
            any(user_indicator in label for user_indicator in 
                ["ui", "ux", "frontend", "user-facing", "feature"])
            for label in label_names
        )
        
        return BusinessImpactMetrics(
            linked_to_release=linked_to_release,
            external_dependencies=external_dependencies,
            priority_label=priority_label,
            affects_core_functionality=affects_core_functionality
        )
    
    async def analyze_pr(self, owner: str, repo: str, pr_data: Dict) -> PRRiskAnalysis:
        """Analyze a single PR for risks"""
        
        pr_number = pr_data["number"]
        logger.info(f"   Analyzing PR #{pr_number}: {pr_data['title']}")
        
        # Fetch detailed PR data - enhanced with additional endpoints
        logger.debug(f"   Fetching detailed data for PR #{pr_number}")
        timeline, reviews, comments, commits, files, check_runs, labels, assignees, milestone, issue_comments = await asyncio.gather(
            self._get_pr_timeline(owner, repo, pr_number),
            self._get_pr_reviews(owner, repo, pr_number),
            self._get_pr_review_comments(owner, repo, pr_number),
            self._get_pr_commits(owner, repo, pr_number),
            self._get_pr_files(owner, repo, pr_number),
            self._get_pr_check_runs(owner, repo, pr_number),  # Enhanced check runs
            self._get_pr_labels(owner, repo, pr_number),      # New: Get detailed labels
            self._get_pr_assignees(owner, repo, pr_number),   # New: Get assignees
            self._get_pr_milestone(owner, repo, pr_number),   # New: Get milestone info
            self._get_pr_issue_comments(owner, repo, pr_number),  # New: Get issue comments
            return_exceptions=True
        )
        
        # Handle any exceptions
        timeline = timeline if isinstance(timeline, list) else []
        reviews = reviews if isinstance(reviews, list) else []
        comments = comments if isinstance(comments, list) else []
        commits = commits if isinstance(commits, list) else []
        files = files if isinstance(files, list) else []
        check_runs = check_runs if isinstance(check_runs, list) else []
        labels = labels if isinstance(labels, list) else []
        assignees = assignees if isinstance(assignees, list) else []
        milestone = milestone if not isinstance(milestone, Exception) else None
        issue_comments = issue_comments if isinstance(issue_comments, list) else []
        
        logger.debug(f"   PR #{pr_number}: Got {len(timeline)} timeline events, {len(reviews)} reviews, {len(comments)} comments, {len(commits)} commits, {len(files)} files")
        
        # Get author PR history
        author = pr_data["user"]["login"]
        logger.debug(f"   PR #{pr_number}: Getting PR history for author @{author}")
        author_prs = await self._get_author_pr_history(owner, repo, author)
        
        # Get PR statistics (additions, deletions, changed_files)
        logger.debug(f"   PR #{pr_number}: Fetching PR statistics")
        pr_stats = await self._get_pr_statistics(owner, repo, pr_number)
        logger.debug(f"   PR #{pr_number}: Statistics - +{pr_stats.get('additions', 0)}/-{pr_stats.get('deletions', 0)} lines, {pr_stats.get('changed_files', 0)} files")
        
        # Get external dependencies analysis
        logger.debug(f"   PR #{pr_number}: Analyzing external dependencies")
        dependencies = await self._analyze_external_dependencies(files, pr_data.get("body", ""))
        
        # Collect detailed PR info
        logger.debug(f"   PR #{pr_number}: Collecting detailed PR info")
        detailed_pr_info = await self._collect_detailed_pr_info(
            owner, repo, pr_data, files, commits, reviews, comments, issue_comments, check_runs
        )
        
        # Calculate all metrics with enhanced data
        logger.debug(f"   PR #{pr_number}: Calculating stuckness metrics")
        stuckness_metrics = await self._calculate_stuckness_metrics(
            pr_data, timeline, reviews, comments, commits, check_runs
        )
        
        logger.debug(f"   PR #{pr_number}: Calculating blast radius metrics")
        blast_radius_metrics = await self._calculate_blast_radius_metrics(
            pr_data, files, commits, pr_stats
        )
        
        logger.debug(f"   PR #{pr_number}: Calculating dynamics metrics")
        dynamics_metrics = await self._calculate_dynamics_metrics(
            pr_data, reviews, author_prs, assignees
        )
        
        logger.debug(f"   PR #{pr_number}: Calculating business impact metrics")
        business_impact_metrics = await self._calculate_business_impact_metrics(
            pr_data, files, labels, milestone, dependencies
        )
        
        # Calculate composite scores
        logger.debug(f"   PR #{pr_number}: Calculating composite scores")
        composite_scores = CompositeRiskScore(
            stuckness_score=stuckness_metrics.calculate_score(),
            blast_radius_score=blast_radius_metrics.calculate_score(),
            dynamics_score=dynamics_metrics.calculate_score(),
            business_impact_score=business_impact_metrics.calculate_score()
        )
        
        # Calculate overall delivery risk score
        delivery_risk_score = composite_scores.delivery_risk_score
        
        # Generate AI summary (simplified)
        ai_summary = self._generate_ai_summary(composite_scores, stuckness_metrics, blast_radius_metrics)
        
        logger.info(f"   PR #{pr_number}: Analysis complete - Risk score: {delivery_risk_score:.1f}")
        
        return PRRiskAnalysis(
            pr_number=pr_number,
            title=pr_data["title"],
            author=author,
            state=PRState(pr_data["state"]),
            created_at=datetime.fromisoformat(pr_data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(pr_data["updated_at"].replace("Z", "+00:00")),
            url=pr_data["html_url"],
            stuckness_metrics=stuckness_metrics,
            blast_radius_metrics=blast_radius_metrics,
            dynamics_metrics=dynamics_metrics,
            business_impact_metrics=business_impact_metrics,
            composite_scores=composite_scores,
            detailed_info=detailed_pr_info,
            ai_summary=ai_summary,
            analyzed_at=datetime.now()
        )
    
    def _generate_ai_summary(self, scores: CompositeRiskScore, 
                           stuckness: StucknessMetrics, 
                           blast_radius: BlastRadiusMetrics) -> str:
        """Generate AI-like summary of PR risks"""
        risk_level = scores.delivery_risk_score
        
        summary_parts = []
        
        if risk_level >= 80:
            summary_parts.append("🚨 CRITICAL RISK")
        elif risk_level >= 60:
            summary_parts.append("⚠️ HIGH RISK")
        elif risk_level >= 40:
            summary_parts.append("⚡ MEDIUM RISK")
        else:
            summary_parts.append("✅ LOW RISK")
        
        # Stuckness issues
        if stuckness.time_since_last_activity_hours > 72:
            summary_parts.append("Stalled for 3+ days")
        elif stuckness.unresolved_review_threads > 5:
            summary_parts.append("Many unresolved review threads")
        elif stuckness.failed_ci_checks > 0:
            summary_parts.append("Failed CI checks")
        
        # Blast radius issues
        if blast_radius.critical_path_touched:
            summary_parts.append("Touches critical paths")
        elif blast_radius.lines_added + blast_radius.lines_removed > 1000:
            summary_parts.append("Large code changes")
        
        return " • ".join(summary_parts)
    
    async def analyze_repository(self, owner: str, repo: str, 
                               include_closed_prs: bool = False,
                               max_prs: int = 50,
                               force_refresh: bool = False) -> RepositoryRiskReport:
        """Analyze all PRs in a repository for risks"""
        
        logger.info(f"🔍 Analyzing PR risks for {owner}/{repo}")
        logger.info(f"   Settings: include_closed_prs={include_closed_prs}, max_prs={max_prs}, force_refresh={force_refresh}")
        
        # Check if we have cached data
        db = self._load_database()
        existing_report = db.get_repo_report(owner, repo)

        if existing_report and not force_refresh:
            # Check if data is recent (less than 1 hour old)
            age = datetime.now() - existing_report.analyzed_at
            if age.total_seconds() < 3600:
                logger.info(f"   📋 Using cached data (age: {age})")
                return existing_report
            else:
                logger.info(f"   📋 Cached data is stale (age: {age}), refreshing...")
        
        # Fetch PRs
        state = "all" if include_closed_prs else "open"
        logger.info(f"   Fetching {state} PRs from GitHub...")
        url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls"
        resp = await self.client.get(url, params={
            "state": state,
            "sort": "updated",
            "direction": "desc",
            "per_page": min(max_prs, 100)
        })
        
        if resp.status_code != 200:
            error_msg = f"Failed to fetch PRs: {resp.status_code}"
            logger.error(f"   ❌ {error_msg}")
            raise Exception(error_msg)
        
        prs = resp.json()
        logger.info(f"   📊 Found {len(prs)} PRs to analyze")
        
        # Analyze each PR
        pr_analyses = []
        successful_analyses = 0
        failed_analyses = 0
        prs = prs[:10]
        for i, pr_data in enumerate(prs, 1):
            logger.info(f"   Progress: {i}/{len(prs)} - Analyzing PR #{pr_data['number']}")
            try:
                analysis = await self.analyze_pr(owner, repo, pr_data)
                pr_analyses.append(analysis)
                successful_analyses += 1
                logger.debug(f"   ✅ PR #{pr_data['number']} analysis successful")
            except Exception as e:
                failed_analyses += 1
                logger.warning(f"   ⚠️ Error analyzing PR #{pr_data['number']}: {e}")
                continue
        
        logger.info(f"   📊 Analysis Summary: {successful_analyses} successful, {failed_analyses} failed")
        
        # Calculate aggregate metrics
        if pr_analyses:
            avg_delivery_risk_score = sum(p.delivery_risk_score for p in pr_analyses) / len(pr_analyses)
            high_risk_pr_count = len([p for p in pr_analyses if p.delivery_risk_score >= 60])
            critical_risk_pr_count = len([p for p in pr_analyses if p.delivery_risk_score >= 80])
            
            logger.info(f"   📈 Risk Distribution:")
            logger.info(f"      - Average Risk Score: {avg_delivery_risk_score:.1f}")
            logger.info(f"      - High Risk PRs: {high_risk_pr_count}")
            logger.info(f"      - Critical Risk PRs: {critical_risk_pr_count}")
        else:
            avg_delivery_risk_score = 0.0
            high_risk_pr_count = 0
            critical_risk_pr_count = 0
            logger.warning("   ⚠️ No PRs were successfully analyzed")
        
        # Team velocity impact (simplified)
        team_velocity_impact = min(avg_delivery_risk_score + (critical_risk_pr_count * 10), 100)
        
        # Release risk assessment
        if critical_risk_pr_count > 0:
            release_risk = "High risk - critical PRs need immediate attention"
        elif high_risk_pr_count > len(pr_analyses) * 0.3:
            release_risk = "Medium risk - many high-risk PRs"
        else:
            release_risk = "Low risk - most PRs are healthy"
        
        logger.info(f"   🚀 Release Risk Assessment: {release_risk}")
        
        report = RepositoryRiskReport(
            owner=owner,
            repo=repo,
            analyzed_at=datetime.now(),
            total_prs_analyzed=len(pr_analyses),
            pr_analyses=pr_analyses,
            avg_delivery_risk_score=avg_delivery_risk_score,
            high_risk_pr_count=high_risk_pr_count,
            critical_risk_pr_count=critical_risk_pr_count,
            team_velocity_impact=team_velocity_impact,
            release_risk_assessment=release_risk
        )
        
        # Save to database
        logger.info(f"   💾 Saving analysis results to database...")
        db.add_or_update_repo(report)
        self._save_database(db)
        
        logger.info(f"   ✅ Analysis complete. Risk score: {avg_delivery_risk_score:.1f}")
        return report

    async def _get_pr_check_runs(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get check runs for a PR (enhanced version)"""
        try:
            # Get the latest commit SHA for the PR
            commits = await self._get_pr_commits(owner, repo, pr_number)
            if not commits:
                return []
            
            latest_commit = commits[-1]
            return await self._get_check_runs(owner, repo, latest_commit["sha"])
        except Exception as e:
            logger.error(f"    Error getting PR check runs: {e}")
            return []

    async def _get_pr_labels(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get detailed labels for a PR"""
        try:
            # The labels are already in pr_data, but we can enhance them with additional info
            # For now, return the labels from the main PR data
            return []
        except Exception as e:
            logger.error(f"    Error getting PR labels: {e}")
            return []

    async def _get_pr_assignees(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Get assignees for a PR"""
        try:
            # The assignees are already in pr_data, but we can enhance them
            # For now, return empty list as assignees are in main PR data
            return []
        except Exception as e:
            logger.error(f"    Error getting PR assignees: {e}")
            return []

    async def _get_pr_milestone(self, owner: str, repo: str, pr_number: int) -> Optional[Dict]:
        """Get milestone information for a PR"""
        try:
            # The milestone is already in pr_data, but we can enhance it
            # For now, return None as milestone info is in main PR data
            return None
        except Exception as e:
            logger.error(f"    Error getting PR milestone: {e}")
            return None

    async def _get_pr_statistics(self, owner: str, repo: str, pr_number: int) -> Dict:
        """Get PR statistics including additions, deletions, and changed files"""
        try:
            # Get the PR details which include statistics
            url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
            resp = await self.client.get(url)
            if resp.status_code == 200:
                pr_details = resp.json()
                return {
                    "additions": pr_details.get("additions", 0),
                    "deletions": pr_details.get("deletions", 0),
                    "changed_files": pr_details.get("changed_files", 0)
                }
            else:
                logger.warning(f"    Failed to get PR statistics: {resp.status_code}")
                return {"additions": 0, "deletions": 0, "changed_files": 0}
        except Exception as e:
            logger.error(f"    Error getting PR statistics: {e}")
            return {"additions": 0, "deletions": 0, "changed_files": 0}

    async def _analyze_external_dependencies(self, files: List[Dict], pr_body: str) -> Dict:
        """Analyze external dependencies from files and PR description"""
        try:
            dependencies = {
                "external_packages": [],
                "api_endpoints": [],
                "third_party_services": [],
                "dependency_count": 0
            }
            
            # Analyze files for package imports
            for file_info in files:
                filename = file_info.get("filename", "")
                if filename.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go')):
                    # This is a code file, could contain dependencies
                    dependencies["dependency_count"] += 1
            
            # Analyze PR body for mentions of external services
            body_lower = pr_body.lower()
            external_indicators = [
                "api", "service", "library", "package", "dependency", "integration",
                "aws", "azure", "gcp", "firebase", "stripe", "twilio", "sendgrid"
            ]
            
            for indicator in external_indicators:
                if indicator in body_lower:
                    dependencies["third_party_services"].append(indicator)
            
            return dependencies
        except Exception as e:
            logger.error(f"    Error analyzing external dependencies: {e}")
            return {"external_packages": [], "api_endpoints": [], "third_party_services": [], "dependency_count": 0}


# Convenience function for easy usage
async def analyze_pr_risks(owner: str, repo: str, token: Optional[str] = None, 
                          max_prs: int = 50, force_refresh: bool = False) -> RepositoryRiskReport:
    """Convenience function to analyze PR risks for a repository"""
    analyzer = PRRiskAnalyzer(token=token)
    return await analyzer.analyze_repository(owner, repo, max_prs=max_prs, force_refresh=force_refresh)