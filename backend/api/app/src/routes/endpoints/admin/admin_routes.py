from fastapi import APIRouter, Depends

from app.src.dependencies import get_current_user

router = APIRouter()


@router.get("/test")
async def test(current_user=Depends(get_current_user)):
    return "Welcome to the Admin API."
