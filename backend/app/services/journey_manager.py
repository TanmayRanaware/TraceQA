import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..config import JourneyConfig

class JourneyManager:
    def __init__(self):
        self.journeys_file = os.path.join(os.environ.get("BASE_DIR", "object_store"), "journeys.json")
        self._ensure_journeys_file()
    
    def _ensure_journeys_file(self):
        """Ensure the journeys file exists with default journeys"""
        if not os.path.exists(self.journeys_file):
            os.makedirs(os.path.dirname(self.journeys_file), exist_ok=True)
            
            # Create default journeys
            default_journeys = [
                {
                    "name": "Point of Settlement",
                    "description": "Banking settlement and clearing processes",
                    "color": "primary",
                    "created_date": datetime.now().isoformat(),
                    "is_default": True
                },
                {
                    "name": "Payment Processing", 
                    "description": "Payment transaction workflows",
                    "color": "secondary",
                    "created_date": datetime.now().isoformat(),
                    "is_default": True
                },
                {
                    "name": "Account Management",
                    "description": "Customer account operations", 
                    "color": "success",
                    "created_date": datetime.now().isoformat(),
                    "is_default": True
                }
            ]
            
            with open(self.journeys_file, 'w') as f:
                json.dump(default_journeys, f, indent=2)
    
    def get_all_journeys(self) -> List[Dict[str, Any]]:
        """Get all journeys"""
        try:
            with open(self.journeys_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            return []
    
    def get_journey_names(self) -> List[str]:
        """Get list of journey names"""
        journeys = self.get_all_journeys()
        return [journey["name"] for journey in journeys]
    
    def add_journey(self, name: str, description: str = "", color: str = "primary") -> Dict[str, Any]:
        """Add a new journey"""
        try:
            journeys = self.get_all_journeys()
            
            # Check if journey already exists
            if any(j["name"].lower() == name.lower() for j in journeys):
                return {
                    "status": "error",
                    "message": f"Journey '{name}' already exists"
                }
            
            # Add new journey
            new_journey = {
                "name": name,
                "description": description or f"Custom journey: {name}",
                "color": color,
                "created_date": datetime.now().isoformat(),
                "is_default": False
            }
            
            journeys.append(new_journey)
            
            # Save back to file
            with open(self.journeys_file, 'w') as f:
                json.dump(journeys, f, indent=2)
            
            return {
                "status": "success",
                "journey": new_journey,
                "message": f"Journey '{name}' added successfully"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to add journey: {str(e)}"
            }
    
    def update_journey(self, old_name: str, new_name: str = None, description: str = None, color: str = None) -> Dict[str, Any]:
        """Update an existing journey"""
        try:
            journeys = self.get_all_journeys()
            
            # Find the journey
            journey_index = None
            for i, journey in enumerate(journeys):
                if journey["name"] == old_name:
                    journey_index = i
                    break
            
            if journey_index is None:
                return {
                    "status": "error",
                    "message": f"Journey '{old_name}' not found"
                }
            
            # Update journey
            if new_name:
                journeys[journey_index]["name"] = new_name
            if description is not None:
                journeys[journey_index]["description"] = description
            if color:
                journeys[journey_index]["color"] = color
            
            journeys[journey_index]["last_updated"] = datetime.now().isoformat()
            
            # Save back to file
            with open(self.journeys_file, 'w') as f:
                json.dump(journeys, f, indent=2)
            
            return {
                "status": "success",
                "journey": journeys[journey_index],
                "message": f"Journey updated successfully"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to update journey: {str(e)}"
            }
    
    def delete_journey(self, name: str) -> Dict[str, Any]:
        """Delete a journey (only if not default)"""
        try:
            journeys = self.get_all_journeys()
            
            # Find the journey
            journey_index = None
            for i, journey in enumerate(journeys):
                if journey["name"] == name:
                    journey_index = i
                    break
            
            if journey_index is None:
                return {
                    "status": "error",
                    "message": f"Journey '{name}' not found"
                }
            
            # Check if it's a default journey
            if journeys[journey_index].get("is_default", False):
                return {
                    "status": "error",
                    "message": f"Cannot delete default journey '{name}'"
                }
            
            # Remove journey
            deleted_journey = journeys.pop(journey_index)
            
            # Save back to file
            with open(self.journeys_file, 'w') as f:
                json.dump(journeys, f, indent=2)
            
            return {
                "status": "success",
                "journey": deleted_journey,
                "message": f"Journey '{name}' deleted successfully"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to delete journey: {str(e)}"
            }
