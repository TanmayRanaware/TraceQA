from typing import List, Optional, Any
from pydantic import BaseModel


class TestCase(BaseModel):
    key: Optional[str] = None  # Unique test case key
    name: str  # Test case name
    status: Optional[str] = "Draft"  # Test case status
    precondition_objective: Optional[str] = None  # Precondition objective
    folder: Optional[str] = None  # Folder/category
    priority: Optional[str] = None  # Priority (High/Medium/Low)
    component_labels: Optional[List[str]] = None  # Component labels
    owner: Optional[str] = None  # Test case owner
    estimated_time: Optional[str] = None  # Estimated execution time
    coverage: Optional[str] = None  # Test coverage
    test_script: Optional[str] = None  # Test script/steps
    
    # Additional fields for backward compatibility
    test_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    preconditions: Optional[List[str]] = None
    test_steps: Optional[List[str]] = None
    steps: Optional[List[str]] = None
    expected_results: Optional[List[str]] = None
    expected: Optional[str] = None
    test_data: Optional[Any] = None
    test_type: Optional[str] = None
    tags: Optional[List[str]] = None


class TestGenerationRequest(BaseModel):
    journey: str
    max_cases: int = 100
    context_top_k: int = 20
    provider: Optional[str] = None  # override env if set
    model: Optional[str] = None


class TestGenerationResponse(BaseModel):
    journey: str
    tests: List[TestCase]


