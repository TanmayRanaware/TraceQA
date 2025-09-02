from typing import List, Optional
from pydantic import BaseModel


class RequirementIngestRequest(BaseModel):
    journey: str
    document_uri: str
    source_type: str  # fsd | addendum | annexure | email
    effective_date: Optional[str] = None  # ISO date string
    notes: Optional[str] = None


class RequirementSearchRequest(BaseModel):
    journey: str
    query: str
    top_k: int = 10


class RequirementDiffRequest(BaseModel):
    journey: str
    from_version: str
    to_version: str


class FactCheckRequest(BaseModel):
    journey: str
    claim: str
    top_k: int = 10


