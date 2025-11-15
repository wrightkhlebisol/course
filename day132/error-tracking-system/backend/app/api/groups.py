"""Error group management API endpoints"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_groups():
    return {"message": "Error groups endpoint"}
