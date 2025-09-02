from fastapi import APIRouter, HTTPException
from ..services.background_processor import (
    background_processor,
    submit_batch_test_generation,
    submit_document_cleanup,
    submit_impact_analysis
)

router = APIRouter()


@router.post("/background/batch-test-generation")
async def start_batch_test_generation(journey: str, max_cases: int = 500, 
                                    context_top_k: int = 50, provider: str = None):
    """Start a background task to generate a large number of test cases."""
    try:
        task_id = submit_batch_test_generation(
            journey=journey,
            max_cases=max_cases,
            context_top_k=context_top_k,
            provider=provider
        )
        return {
            "task_id": task_id,
            "journey": journey,
            "max_cases": max_cases,
            "status": "submitted"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")


@router.post("/background/document-cleanup")
async def start_document_cleanup(journey: str, older_than_days: int = 90):
    """Start a background task to clean up old document versions."""
    try:
        task_id = submit_document_cleanup(
            journey=journey,
            older_than_days=older_than_days
        )
        return {
            "task_id": task_id,
            "journey": journey,
            "older_than_days": older_than_days,
            "status": "submitted"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")


@router.post("/background/impact-analysis")
async def start_impact_analysis(journey: str, from_version: str, to_version: str):
    """Start a background task to analyze the impact of requirement changes."""
    try:
        task_id = submit_impact_analysis(
            journey=journey,
            from_version=from_version,
            to_version=to_version
        )
        return {
            "task_id": task_id,
            "journey": journey,
            "from_version": from_version,
            "to_version": to_version,
            "status": "submitted"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")


@router.get("/background/tasks")
async def list_background_tasks():
    """List all active background tasks."""
    try:
        tasks = background_processor.list_active_tasks()
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.get("/background/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a specific background task."""
    try:
        status = background_processor.get_task_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail="Task not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.delete("/background/tasks/{task_id}")
async def cancel_background_task(task_id: str):
    """Cancel a running background task."""
    try:
        cancelled = background_processor.cancel_task(task_id)
        if not cancelled:
            raise HTTPException(status_code=400, detail="Task cannot be cancelled or not found")
        return {"task_id": task_id, "status": "cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.post("/background/cleanup-completed")
async def cleanup_completed_tasks(max_age_hours: int = 24):
    """Clean up completed tasks older than specified hours."""
    try:
        background_processor.cleanup_completed_tasks(max_age_hours)
        return {"status": "cleanup_completed", "max_age_hours": max_age_hours}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup tasks: {str(e)}")
