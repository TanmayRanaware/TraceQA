from typing import List, Optional, Any
from pydantic import BaseModel
from enum import Enum


class TestCaseType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    EDGE = "edge"


class TestCase(BaseModel):
    # Required structured format for Objective A
    test_case_name: str  # Test Case Name
    preconditions: str  # Preconditions
    steps: str  # Steps
    expected_result: str  # Expected Result
    actual_result: Optional[str] = None  # Actual Result (for execution tracking)
    
    # Additional metadata
    test_case_id: Optional[str] = None  # Unique identifier
    test_type: Optional[TestCaseType] = None  # positive, negative, edge
    priority: Optional[str] = "Medium"  # High/Medium/Low
    journey: Optional[str] = None  # Associated journey
    requirement_reference: Optional[str] = None  # Reference to specific requirement
    created_date: Optional[str] = None
    last_updated: Optional[str] = None
    status: Optional[str] = "Draft"  # Draft/Ready/Executed/Outdated
    
    # Legacy fields for backward compatibility
    key: Optional[str] = None
    name: Optional[str] = None
    status_legacy: Optional[str] = "Draft"
    precondition_objective: Optional[str] = None
    folder: Optional[str] = None
    component_labels: Optional[List[str]] = None
    owner: Optional[str] = None
    estimated_time: Optional[str] = None
    coverage: Optional[str] = None
    test_script: Optional[str] = None
    test_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    preconditions_legacy: Optional[List[str]] = None
    test_steps: Optional[List[str]] = None
    expected_results: Optional[List[str]] = None
    expected: Optional[str] = None
    test_data: Optional[Any] = None
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


class ChangeManagementRequest(BaseModel):
    journey: str
    document_uri: str
    source_type: str
    action: str  # "add", "update", "remove"


class TestCaseUpdateRequest(BaseModel):
    journey: str
    test_case_id: str
    status: Optional[str] = None
    actual_result: Optional[str] = None
    notes: Optional[str] = None


class TestCaseValidationRequest(BaseModel):
    journey: str
    validate_outdated: bool = True
    remove_outdated: bool = False


