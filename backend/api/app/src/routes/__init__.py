from fastapi import APIRouter

from .endpoints.melody.melody import router as melody_router
from .main import router as main_router

# Create a main router
router = APIRouter()

# Include all sub-routers
router.include_router(main_router)
router.include_router(melody_router, prefix="/melody")
