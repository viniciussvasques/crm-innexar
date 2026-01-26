
from fastapi import APIRouter

# Stub to replace overwritten file and prevent ImportErrors
router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/")
async def list_projects():
    return []
