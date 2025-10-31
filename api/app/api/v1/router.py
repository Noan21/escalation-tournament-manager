from fastapi import APIRouter

from app.api.v1 import stages

router = APIRouter()
router.include_router(stages.router, prefix="/stages", tags=["stages"])
