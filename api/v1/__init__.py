from fastapi import APIRouter

from .auth import router as auth_router
from .github import router as github_router
from .integrations.integrations import integration_router
from .invitations.invitations import invitation_router
from .member import router as member_router
from .monitoring import monitoring_router
from .organizations.organizations import organization_router
from .tasks import tasks_router
from .users import users_router

v1_router = APIRouter()
v1_router.include_router(auth_router)  # Auth endpoints have /auth prefix
v1_router.include_router(github_router)  # GitHub endpoints have /github prefix
v1_router.include_router(monitoring_router, prefix="/monitoring")
v1_router.include_router(tasks_router, prefix="/tasks")
v1_router.include_router(users_router, prefix="/users")
v1_router.include_router(member_router)  # Member endpoints have /member prefix already
v1_router.include_router(organization_router, prefix="/organizations")
v1_router.include_router(integration_router, prefix="/integrations")
v1_router.include_router(invitation_router, prefix="/invitations")
