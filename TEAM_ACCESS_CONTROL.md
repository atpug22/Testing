# Team-Based Access Control Implementation

## Overview

This document describes the hierarchical team-based access control system implemented for LogPose. The system allows for fine-grained access control based on user roles and team membership.

## Role Hierarchy

The system implements a four-tier role hierarchy:

1. **CTO** - Full access to all teams and PRs across the organization
2. **Engineering Head** - Access to specific teams they manage
3. **Engineering Manager** - Access to their assigned team and all its members
4. **Engineer** - Access only to their own PRs

## Database Schema

### New Models

#### `Role` Enum
Located in `app/models/role.py`, defines the four role types with helper methods:
- `can_manage_all_teams()` - Returns True for CTO
- `can_manage_specific_teams()` - Returns True for leadership roles
- `get_leadership_roles()` - Returns list of roles with team management capabilities

#### `Team` Model
Located in `app/models/team.py`:
- **Fields:**
  - `name` - Unique team name
  - `description` - Team description
  - `manager_id` - Foreign key to User (Engineering Manager)
  
- **Relationships:**
  - `manager` - One-to-one with User
  - `members` - Many-to-many with User (via `team_members` table)
  - `pull_requests` - One-to-many with PullRequest

#### `PullRequest` Model
Located in `app/models/pull_request.py`:
- **Fields:**
  - `github_pr_id` - Unique GitHub PR identifier
  - `title`, `description`, `github_url`
  - `status` - PR status (open, closed, merged)
  - `author_id` - Foreign key to User
  - `team_id` - Foreign key to Team

- **Domain Enums:**
  - `PrimaryStatus` - Engineer's current state (Balanced, Overloaded, Blocked, etc.)
  - `FlowBlocker` - Reasons a PR is stuck (Awaiting Review, Broken Build, etc.)
  - `RiskFlag` - Risk indicators (Critical File Change, Vulnerability Detected, etc.)

#### `User` Model Updates
Extended in `app/models/user.py`:
- **New Fields:**
  - `role` - User's role in the hierarchy
  - `manager_id` - Self-referential foreign key for reporting structure

- **New Relationships:**
  - `manager` - One-to-one with User (self-referential)
  - `direct_reports` - One-to-many with User (self-referential)
  - `teams` - Many-to-many with Team (as member)
  - `managed_teams` - One-to-many with Team (as manager)
  - `pull_requests` - One-to-many with PullRequest

## Access Control System

### Principals

The access control system uses principals to represent user identity and permissions:

- **UserPrincipal** - User's unique ID
- **RolePrincipal** - User's role (cto, engineering_head, engineering_manager, engineer)
- **TeamPrincipal** - Teams the user is a member of or manages
- **SystemPrincipals** - Everyone, Authenticated

### How Access Control Works

Located in `core/fastapi/dependencies/permissions.py`, the `get_user_principals()` function builds a list of principals for each user:

```python
principals = [
    Everyone,
    Authenticated,
    UserPrincipal(user.id),
    RolePrincipal(user.role.value),
    TeamPrincipal(team.id) for each team in user.teams,
    TeamPrincipal(team.id) for each team in user.managed_teams
]
```

### PR Access Rules

Defined in `PullRequest.__acl__()`:

1. **PR Author** - Full permissions (READ, EDIT, DELETE) on their own PRs
2. **Admin/CTO** - Full permissions on all PRs
3. **Team Members** - READ permission on all PRs in their team(s)

The system automatically grants access based on:
- If user is the PR author → Full access
- If user is CTO or Admin → Full access
- If user has TeamPrincipal matching PR's team_id → READ access

## Repositories

### TeamRepository
Located in `app/repositories/team.py`:

**Key Methods:**
- `get_by_name(name)` - Get team by name
- `get_teams_for_user(user_id)` - Get all teams where user is member or manager
- `get_managed_teams(manager_id)` - Get teams managed by user
- `add_member(team, user)` - Add user to team
- `remove_member(team, user)` - Remove user from team

**Available Joins:**
- `manager` - Load team's manager
- `members` - Load all team members
- `pull_requests` - Load team's PRs

### PullRequestRepository
Located in `app/repositories/pull_request.py`:

**Key Methods:**
- `get_by_github_id(github_pr_id)` - Get PR by GitHub ID
- `get_by_author(author_id)` - Get all PRs by author
- `get_by_team(team_id)` - Get all PRs for a team
- `get_by_status(status)` - Get PRs by status

**Available Joins:**
- `author` - Load PR author
- `team` - Load PR's team

### UserRepository Updates
Extended in `app/repositories/user.py`:

**New Join Methods:**
- `_join_teams` - Load user's teams
- `_join_managed_teams` - Load teams user manages
- `_join_manager` - Load user's manager
- `_join_direct_reports` - Load user's direct reports

## Controllers

### TeamController
Located in `app/controllers/team.py` - Wraps TeamRepository methods

### PullRequestController
Located in `app/controllers/pull_request.py` - Wraps PullRequestRepository methods

## Factory Pattern

Updated in `core/factory/factory.py` to include:
- `get_team_controller()`
- `get_pull_request_controller()`

## Usage Examples

### Example 1: Check if user can access a PR

```python
from fastapi import Depends
from core.fastapi.dependencies.permissions import Permissions
from app.models import PRPermission

@router.get("/prs/{pr_id}")
async def get_pr(
    pr_id: int,
    pr_controller: PullRequestController = Depends(Factory().get_pull_request_controller),
    assert_access=Depends(Permissions(PRPermission.READ)),
):
    pr = await pr_controller.get_by_id(pr_id, join_={"author", "team"})
    assert_access(pr)  # Will raise 403 if user doesn't have access
    return pr
```

### Example 2: Get all PRs accessible to current user

```python
# For CTO - gets all PRs
# For Engineering Manager - gets PRs from their team(s)
# For Engineer - gets only their own PRs

@router.get("/my-prs")
async def get_my_prs(
    current_user: User = Depends(get_current_user),
    pr_controller: PullRequestController = Depends(Factory().get_pull_request_controller),
    team_controller: TeamController = Depends(Factory().get_team_controller),
):
    if current_user.role == Role.CTO or current_user.is_admin:
        # Get all PRs
        return await pr_controller.get_all()
    
    elif current_user.role in [Role.ENGINEERING_HEAD, Role.ENGINEERING_MANAGER]:
        # Get PRs from all teams user manages
        teams = await team_controller.get_teams_for_user(
            current_user.id, join_={"pull_requests"}
        )
        prs = []
        for team in teams:
            prs.extend(team.pull_requests)
        return prs
    
    else:
        # Engineers get only their own PRs
        return await pr_controller.get_by_author(current_user.id)
```

### Example 3: Create a team with manager

```python
from app.models import Team, Role

@router.post("/teams")
async def create_team(
    team_data: dict,
    team_controller: TeamController = Depends(Factory().get_team_controller),
    user_controller: UserController = Depends(Factory().get_user_controller),
    current_user: User = Depends(get_current_user),
):
    # Only CTO or Engineering Head can create teams
    if current_user.role not in [Role.CTO, Role.ENGINEERING_HEAD]:
        raise HTTPException(403, "Insufficient permissions")
    
    # Get the designated manager
    manager = await user_controller.get_by_id(team_data["manager_id"])
    
    # Create team
    team = await team_controller.create({
        "name": team_data["name"],
        "description": team_data["description"],
        "manager_id": manager.id,
    })
    
    return team
```

### Example 4: Add member to team

```python
@router.post("/teams/{team_id}/members/{user_id}")
async def add_team_member(
    team_id: int,
    user_id: int,
    team_controller: TeamController = Depends(Factory().get_team_controller),
    user_controller: UserController = Depends(Factory().get_user_controller),
    assert_access=Depends(Permissions(TeamPermission.MANAGE_MEMBERS)),
):
    team = await team_controller.get_by_id(team_id, join_={"members"})
    assert_access(team)  # Check if current user can manage this team
    
    user = await user_controller.get_by_id(user_id)
    await team_controller.add_member(team, user)
    
    return {"message": "User added to team"}
```

## Database Migration

Run the migration to create the new tables:

```bash
alembic upgrade head
```

This will:
1. Add `role` and `manager_id` columns to `users` table
2. Create `teams` table
3. Create `team_members` association table
4. Create `pull_requests` table

To rollback:

```bash
alembic downgrade -1
```

## Testing the Access Control

You can test the access control system by:

1. Creating users with different roles
2. Creating teams and assigning managers
3. Adding members to teams
4. Creating PRs for different teams
5. Attempting to access PRs as different users

The system will automatically enforce access rules based on the user's principals and the resource's ACL.

## Security Considerations

1. **Least Privilege**: Engineers can only see their own PRs by default
2. **Team Isolation**: Team members can view PRs within their team
3. **Hierarchical Access**: Managers can view all PRs in their teams
4. **Audit Trail**: All access is controlled through the ACL system, making it easy to audit
5. **Flexible Permissions**: New permission types can be added to the enums as needed

## Next Steps

To fully utilize this system for LogPose:

1. **GitHub Integration**: Sync PRs from GitHub to populate `pull_requests` table
2. **Team Sync**: Sync teams from your organization structure
3. **Analytics Endpoints**: Create endpoints that respect access control for team analytics
4. **Frontend Integration**: Build UI components that respect role-based visibility
5. **Metrics & Insights**: Implement the Flow Blockers, Risk Flags, and Primary Status logic

