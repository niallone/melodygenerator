from fastapi import APIRouter

from .endpoints.admin.admin_routes import router as admin_router
from .endpoints.auth.auth_routes import router as auth_router
from .endpoints.melody.melody import router as melody_router
from .endpoints.user.user_account_routes import router as user_account_router
from .main import router as main_router

# Create a main router
router = APIRouter()

# Include all sub-routers
router.include_router(main_router)
router.include_router(auth_router, prefix="/auth")
router.include_router(admin_router, prefix="/admin")
router.include_router(user_account_router)
router.include_router(melody_router, prefix="/melody")
