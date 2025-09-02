from fastapi import APIRouter, HTTPException
from ..services.testgen import TestGenerator
from ..schemas import TestGenerationRequest, TestGenerationResponse

router = APIRouter(prefix="/api/tests", tags=["test-generation"])

@router.post("/generate")
async def generate_tests(payload: TestGenerationRequest):
    try:
        test_generator = TestGenerator()
        result = await test_generator.generate_test_cases(
            journey=payload.journey,
            max_cases=payload.max_cases,
            context="",  # Context will be built from RAG search
            source_types=None,  # Use all source types
            model=payload.model,
            temperature=None  # Use default temperature
        )
        return {
            "journey": payload.journey,
            "tests": result.get("test_cases", []),
            "metadata": result.get("metadata", {}),
            "debug": {
                "status": result.get("status", "unknown"),
                "message": result.get("message", ""),
                "total_generated": result.get("total_generated", 0),
                "context_used": result.get("context_used", "")[:200] + "..." if result.get("context_used") else ""
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate tests: {str(e)}")
