from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..services.journey_manager import JourneyManager
from pydantic import BaseModel

router = APIRouter(prefix="/api/journeys", tags=["journey-management"])

class JourneyCreateRequest(BaseModel):
    name: str
    description: str = ""
    color: str = "primary"

class JourneyUpdateRequest(BaseModel):
    old_name: str
    new_name: str = None
    description: str = None
    color: str = None

class JourneyDeleteRequest(BaseModel):
    name: str

@router.get("/")
async def get_all_journeys() -> Dict[str, Any]:
    """Get all available journeys"""
    try:
        journey_manager = JourneyManager()
        journeys = journey_manager.get_all_journeys()
        return {
            "status": "success",
            "journeys": journeys,
            "total": len(journeys)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get journeys: {str(e)}")

@router.get("/names")
async def get_journey_names() -> Dict[str, Any]:
    """Get list of journey names"""
    try:
        journey_manager = JourneyManager()
        names = journey_manager.get_journey_names()
        return {
            "status": "success",
            "journey_names": names,
            "total": len(names)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get journey names: {str(e)}")

@router.post("/create")
async def create_journey(req: JourneyCreateRequest) -> Dict[str, Any]:
    """Create a new journey"""
    try:
        journey_manager = JourneyManager()
        result = journey_manager.add_journey(
            name=req.name,
            description=req.description,
            color=req.color
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create journey: {str(e)}")

@router.put("/update")
async def update_journey(req: JourneyUpdateRequest) -> Dict[str, Any]:
    """Update an existing journey"""
    try:
        journey_manager = JourneyManager()
        result = journey_manager.update_journey(
            old_name=req.old_name,
            new_name=req.new_name,
            description=req.description,
            color=req.color
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update journey: {str(e)}")

@router.delete("/delete")
async def delete_journey(req: JourneyDeleteRequest) -> Dict[str, Any]:
    """Delete a journey"""
    try:
        journey_manager = JourneyManager()
        result = journey_manager.delete_journey(name=req.name)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete journey: {str(e)}")
