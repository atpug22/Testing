from fastapi import APIRouter

from .ai import router as ai_router
from .ai.pr_analysis import router as pr_analysis_router
from .auth import router as auth_router
from .github import router as github_router
from .member import router as member_router
from .monitoring import monitoring_router
from .tasks import tasks_router
from .users import users_router

v1_router = APIRouter()
v1_router.include_router(auth_router)  # Auth endpoints have /auth prefix
v1_router.include_router(github_router)  # GitHub endpoints have /github prefix
v1_router.include_router(monitoring_router, prefix="/monitoring")
v1_router.include_router(tasks_router, prefix="/tasks")
v1_router.include_router(users_router, prefix="/users")
# Member endpoints have /member prefix already
v1_router.include_router(member_router)
# AI endpoints have /ai prefix already defined
v1_router.include_router(ai_router)
v1_router.include_router(
    pr_analysis_router
)  # PR Analysis endpoints have /ai/pr-analysis prefix
