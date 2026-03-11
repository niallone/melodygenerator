import os
import shutil

from fastapi import APIRouter, Depends, Request

from app.src.dependencies import get_db

router = APIRouter()


@router.get("/health")
async def health_check(request: Request, db=Depends(get_db)):
    health = {"status": "healthy"}

    # Database
    try:
        result = await db.fetchval("SELECT 1")
        health["database"] = "connected" if result == 1 else "error"
    except Exception:
        health["database"] = "error"
        health["status"] = "degraded"

    # Models
    models_loaded = getattr(request.app.state, "models_loaded", False)
    model_count = len(getattr(request.app.state, "models", {}))
    health["models"] = {"loaded": models_loaded, "count": model_count}
    if not models_loaded or model_count == 0:
        health["status"] = "degraded"

    # Disk space for output dir
    settings = request.app.state.settings
    if os.path.isdir(settings.output_dir):
        usage = shutil.disk_usage(settings.output_dir)
        free_gb = usage.free / (1024**3)
        health["disk_free_gb"] = round(free_gb, 1)
        if free_gb < 1.0:
            health["status"] = "degraded"

    return health


@router.get("/")
async def index():
    return "Welcome to the Melodygenerator API."
