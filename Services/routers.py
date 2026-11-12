from fastapi import APIRouter
from .CRUD_Jobs import router as jobs_router
from .apply_jobs import router as apply_router
from .user_profile import router as user_profile_router

router = APIRouter()

router.include_router(jobs_router)
router.include_router(apply_router)
router.include_router(user_profile_router)