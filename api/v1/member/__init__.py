from fastapi import APIRouter

from .member import router as member_router

router = APIRouter()
router.include_router(member_router, tags=["Team Member"])
