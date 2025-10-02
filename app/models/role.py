from enum import Enum


class Role(str, Enum):
    """
    User roles in the LogPose platform.
    Hierarchy (from highest to lowest access):
    - CTO: Access to all teams
    - Engineering Head: Access to specific teams
    - Engineering Manager: Access to their own team
    - Engineer: No team management access (can only view their own PRs)
    """

    CTO = "cto"
    ENGINEERING_HEAD = "engineering_head"
    ENGINEERING_MANAGER = "engineering_manager"
    ENGINEER = "engineer"

    @property
    def display_name(self) -> str:
        """Return a human-readable name for the role."""
        return self.value.replace("_", " ").title()

    @classmethod
    def get_leadership_roles(cls) -> list["Role"]:
        """Returns roles that have team management capabilities."""
        return [cls.CTO, cls.ENGINEERING_HEAD, cls.ENGINEERING_MANAGER]

    def can_manage_all_teams(self) -> bool:
        """Check if this role can manage all teams."""
        return self == Role.CTO

    def can_manage_specific_teams(self) -> bool:
        """Check if this role can manage specific assigned teams."""
        return self in [Role.CTO, Role.ENGINEERING_HEAD, Role.ENGINEERING_MANAGER]

