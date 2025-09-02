from fastapi import APIRouter
from ..services.versioning import list_versions

router = APIRouter()

@router.get("/versions")
async def get_versions():
	return {"versions": list_versions()}
