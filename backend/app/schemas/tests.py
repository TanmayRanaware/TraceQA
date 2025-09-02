from typing import List, Optional, Any
from pydantic import BaseModel


class TestCase(BaseModel):
    test_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    preconditions: Optional[List[str]] = None
    test_steps: Optional[List[str]] = None
    steps: Optional[List[str]] = None  # Alternative field name
    expected_results: Optional[List[str]] = None
    expected: Optional[str] = None  # Alternative field name
    test_data: Optional[Any] = None
    priority: Optional[str] = None
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


