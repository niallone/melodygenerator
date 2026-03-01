from fastapi import APIRouter, Depends

from app.src.dependencies import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db=Depends(get_db)):
    try:
        result = await db.fetchval("SELECT 1")
        if result == 1:
            return {"status": "healthy", "database": "connected"}
        else:
            return {"status": "unhealthy", "database": "error", "message": "Database health check failed"}
    except Exception:
        return {"status": "unhealthy", "database": "error", "message": "Database health check failed"}


@router.get("/")
async def index():
    return "Welcome to the Melodygenerator API."
