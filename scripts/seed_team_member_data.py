"""
Seed script for Team Member Page demo data.
Creates 1 manager + 2 teammates with ~10 PRs and activity timeline.
"""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, TeamMember, Team, PullRequest, Event
from app.models.role import Role
from app.models.enums import PrimaryStatus
from core.database import standalone_session, session
from core.security.password import PasswordHandler


@standalone_session
async def seed_data():
    """Seed demo data for Team Member Page"""
    
    async with session.begin():
        print("🌱 Starting data seeding...")
        
        # Create Team
        print("Creating team...")
        team = Team(
            uuid=uuid4(),
            name="Engineering Team Alpha",
            description="Main product engineering team"
        )
        session.add(team)
        await session.flush()
        
        # Create Users
        print("Creating users...")
        manager = User(
            uuid=uuid4(),
            username="alice_manager",
            email="alice@logpose.dev",
            password=PasswordHandler.hash("demo123"),
            role=Role.ENGINEERING_MANAGER,
            is_admin=False,
        )
        session.add(manager)
        
        teammate1 = User(
            uuid=uuid4(),
            username="bob_engineer",
            email="bob@logpose.dev",
            password=PasswordHandler.hash("demo123"),
            role=Role.ENGINEER,
            is_admin=False,
            manager=manager,
        )
        session.add(teammate1)
        
        teammate2 = User(
            uuid=uuid4(),
            username="carol_engineer",
            email="carol@logpose.dev",
            password=PasswordHandler.hash("demo123"),
            role=Role.ENGINEER,
            is_admin=False,
            manager=manager,
        )
        session.add(teammate2)
        
        # Flush to get IDs assigned
        await session.flush()
        
        # Assign team manager
        team.manager_id = manager.id
        
        # Flush again to ensure team has ID
        await session.flush()
        
        # Note: Skipping team members association for now due to lazy='raise' constraint
        # This can be added via raw SQL after commit or by adjusting relationship lazy settings
        print("Note: Team membership will be added manually or via admin panel")
        
        # Create TeamMember profiles
        print("Creating team member profiles...")
        manager_profile = TeamMember(
            uuid=uuid4(),
            user_id=manager.id,
            primary_status=PrimaryStatus.BALANCED.value,
            last_active_at=datetime.utcnow() - timedelta(hours=2),
            wip_count=3,
            reviews_pending_count=5,
            unresolved_discussions_count=2,
            merged_prs_last_30_days=12,
            avg_cycle_time_hours=18.5,
            rework_rate_percentage=8.5,
            revert_count=1,
            review_velocity_median_hours=4.2,
            collaboration_reach=7,
            github_username="alice_dev",
            github_avatar_url="https://avatars.githubusercontent.com/u/1",
            work_focus_distribution={
                "feature": 55.0,
                "bug": 30.0,
                "chore": 15.0
            },
            codebase_familiarity_percentage=67.5,
            top_collaborators=[
                {"user_id": teammate1.id, "name": "Bob", "count": 12},
                {"user_id": teammate2.id, "name": "Carol", "count": 8}
            ]
        )
        session.add(manager_profile)
        
        bob_profile = TeamMember(
            uuid=uuid4(),
            user_id=teammate1.id,
            primary_status=PrimaryStatus.OVERLOADED.value,
            last_active_at=datetime.utcnow() - timedelta(minutes=30),
            wip_count=6,
            reviews_pending_count=8,
            unresolved_discussions_count=5,
            merged_prs_last_30_days=8,
            avg_cycle_time_hours=24.2,
            rework_rate_percentage=12.3,
            revert_count=0,
            review_velocity_median_hours=6.8,
            collaboration_reach=4,
            github_username="bob_codes",
            github_avatar_url="https://avatars.githubusercontent.com/u/2",
            work_focus_distribution={
                "feature": 70.0,
                "bug": 20.0,
                "chore": 10.0
            },
            codebase_familiarity_percentage=45.2,
        )
        session.add(bob_profile)
        
        carol_profile = TeamMember(
            uuid=uuid4(),
            user_id=teammate2.id,
            primary_status=PrimaryStatus.FIREFIGHTING.value,
            last_active_at=datetime.utcnow() - timedelta(hours=1),
            wip_count=4,
            reviews_pending_count=3,
            unresolved_discussions_count=1,
            merged_prs_last_30_days=15,
            avg_cycle_time_hours=14.8,
            rework_rate_percentage=5.2,
            revert_count=2,
            review_velocity_median_hours=3.5,
            collaboration_reach=6,
            github_username="carol_dev",
            github_avatar_url="https://avatars.githubusercontent.com/u/3",
            work_focus_distribution={
                "feature": 25.0,
                "bug": 65.0,
                "chore": 10.0
            },
            codebase_familiarity_percentage=82.3,
        )
        session.add(carol_profile)
        
        await session.flush()
        
        # Create PRs
        print("Creating pull requests...")
        now = datetime.utcnow()
        
        prs_data = [
            # Bob's PRs (6 WIP to match overloaded status)
            {
                "author": teammate1,
                "title": "feat: Add real-time notifications system",
                "status": "open",
                "labels": ["feature", "priority: high"],
                "flow_blockers": ["awaiting_review"],
                "risk_flags": ["large_blast_radius"],
                "created_at": now - timedelta(days=3),
                "unresolved_comments": 2,
                "lines_changed": 450,
            },
            {
                "author": teammate1,
                "title": "fix: Refactor auth middleware for SSO",
                "status": "open",
                "labels": ["refactor", "security"],
                "flow_blockers": ["broken_build"],
                "risk_flags": ["critical_file_change"],
                "created_at": now - timedelta(days=2),
                "unresolved_comments": 0,
                "lines_changed": 280,
            },
            {
                "author": teammate1,
                "title": "feat: User dashboard improvements",
                "status": "open",
                "labels": ["feature", "ui"],
                "flow_blockers": [],
                "risk_flags": [],
                "created_at": now - timedelta(days=1),
                "unresolved_comments": 1,
                "lines_changed": 320,
            },
            {
                "author": teammate1,
                "title": "chore: Update dependencies",
                "status": "merged",
                "labels": ["chore"],
                "flow_blockers": [],
                "risk_flags": [],
                "created_at": now - timedelta(days=5),
                "merged_at": now - timedelta(days=4),
                "lines_changed": 150,
            },
            
            # Carol's PRs (bug-heavy to match firefighting status)
            {
                "author": teammate2,
                "title": "fix: Critical payment gateway timeout",
                "status": "merged",
                "labels": ["bug", "critical", "payment"],
                "flow_blockers": [],
                "risk_flags": [],
                "created_at": now - timedelta(days=1),
                "merged_at": now - timedelta(hours=8),
                "lines_changed": 120,
            },
            {
                "author": teammate2,
                "title": "fix: Memory leak in data processor",
                "status": "open",
                "labels": ["bug", "performance"],
                "flow_blockers": ["missing_tests"],
                "risk_flags": ["scope_creep_detected"],
                "created_at": now - timedelta(days=2),
                "unresolved_comments": 3,
                "lines_changed": 200,
            },
            {
                "author": teammate2,
                "title": "fix: Email delivery failures",
                "status": "merged",
                "labels": ["bug"],
                "flow_blockers": [],
                "risk_flags": [],
                "created_at": now - timedelta(days=3),
                "merged_at": now - timedelta(days=2),
                "lines_changed": 85,
            },
            
            # Manager's PRs
            {
                "author": manager,
                "title": "feat: Analytics dashboard v2",
                "status": "open",
                "labels": ["feature", "analytics"],
                "flow_blockers": ["review_stalemate"],
                "risk_flags": ["large_blast_radius"],
                "created_at": now - timedelta(days=4),
                "unresolved_comments": 4,
                "lines_changed": 680,
            },
            {
                "author": manager,
                "title": "fix: API rate limiting bug",
                "status": "merged",
                "labels": ["bug", "api"],
                "flow_blockers": [],
                "risk_flags": [],
                "created_at": now - timedelta(days=6),
                "merged_at": now - timedelta(days=5),
                "lines_changed": 90,
            },
        ]
        
        pr_objects = []
        for pr_data in prs_data:
            pr = PullRequest(
                uuid=uuid4(),
                github_pr_id=100000 + len(pr_objects),
                title=pr_data["title"],
                description=f"This PR implements {pr_data['title'].lower()}",
                github_url=f"https://github.com/logpose/platform/pull/{100000 + len(pr_objects)}",
                status=pr_data["status"],
                author_id=pr_data["author"].id,
                team_id=team.id,
                labels=pr_data["labels"],
                flow_blockers=pr_data["flow_blockers"],
                risk_flags=pr_data["risk_flags"],
                created_at=pr_data["created_at"],
                merged_at=pr_data.get("merged_at"),
                unresolved_comments=pr_data.get("unresolved_comments", 0),
                lines_changed=pr_data["lines_changed"],
                additions=int(pr_data["lines_changed"] * 0.7),
                deletions=int(pr_data["lines_changed"] * 0.3),
                changed_files=int(pr_data["lines_changed"] / 50) + 1,
            )
            session.add(pr)
            pr_objects.append(pr)
        
        await session.flush()
        
        # Create timeline events
        print("Creating timeline events...")
        events_data = [
            # Bob's events
            {
                "member": bob_profile,
                "type": "pr_opened",
                "title": "Opened PR #100000: Add real-time notifications",
                "timestamp": now - timedelta(days=3),
                "pr_id": pr_objects[0].id,
            },
            {
                "member": bob_profile,
                "type": "commit",
                "title": "Pushed 5 commits to notification-system branch",
                "timestamp": now - timedelta(days=3, hours=2),
            },
            {
                "member": bob_profile,
                "type": "pr_opened",
                "title": "Opened PR #100001: Refactor auth middleware",
                "timestamp": now - timedelta(days=2),
                "pr_id": pr_objects[1].id,
            },
            {
                "member": bob_profile,
                "type": "review_submitted",
                "title": "Reviewed PR #119: Add user roles",
                "timestamp": now - timedelta(days=1, hours=6),
            },
            
            # Carol's events
            {
                "member": carol_profile,
                "type": "pr_opened",
                "title": "Opened PR #100004: Fix critical payment timeout",
                "timestamp": now - timedelta(days=1),
                "pr_id": pr_objects[4].id,
            },
            {
                "member": carol_profile,
                "type": "pr_merged",
                "title": "Merged PR #100004: Payment gateway fix",
                "timestamp": now - timedelta(hours=8),
                "pr_id": pr_objects[4].id,
                "event_metadata": {"blast_radius": "high"}
            },
            {
                "member": carol_profile,
                "type": "issue_closed",
                "title": "Closed Jira issue PAY-221 early",
                "timestamp": now - timedelta(hours=7),
            },
            {
                "member": carol_profile,
                "type": "review_submitted",
                "title": "Reviewed 3 PRs (2 merged)",
                "timestamp": now - timedelta(hours=4),
            },
        ]
        
        for event_data in events_data:
            event = Event(
                uuid=uuid4(),
                team_member_id=event_data["member"].id,
                event_type=event_data["type"],
                timestamp=event_data["timestamp"],
                title=event_data["title"],
                description=event_data.get("description"),
                pr_id=event_data.get("pr_id"),
                event_metadata=event_data.get("event_metadata", {})
            )
            session.add(event)
        
        # Data will be committed when session.begin() context exits
        print("✅ Seed data created successfully!")
        print("\n📊 Summary:")
        print(f"   - Team: {team.name}")
        print(f"   - Users: {manager.username} (manager), {teammate1.username}, {teammate2.username}")
        print(f"   - PRs: {len(pr_objects)}")
        print(f"   - Events: {len(events_data)}")
        print("\n🔐 Login credentials:")
        print(f"   Manager: alice_manager / demo123")
        print(f"   Engineer 1: bob_engineer / demo123")
        print(f"   Engineer 2: carol_engineer / demo123")


if __name__ == "__main__":
    asyncio.run(seed_data())

