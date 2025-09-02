import asyncio
import threading
import time
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from .requirements_manager import RequirementsManager
from .testgen import TestGenerator


class BackgroundProcessor:
    """Handles background processing tasks for large operations."""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks: Dict[str, Dict] = {}
        self.requirements_manager = RequirementsManager()
    
    def submit_task(self, task_type: str, task_id: str, func: Callable, *args, **kwargs) -> str:
        """Submit a task for background processing."""
        if task_id in self.active_tasks:
            raise ValueError(f"Task {task_id} already exists")
        
        future = self.executor.submit(func, *args, **kwargs)
        
        self.active_tasks[task_id] = {
            "type": task_type,
            "future": future,
            "status": "running",
            "started_at": time.time(),
            "progress": 0,
            "result": None,
            "error": None
        }
        
        # Start monitoring thread
        threading.Thread(target=self._monitor_task, args=(task_id,), daemon=True).start()
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get the status of a background task."""
        if task_id not in self.active_tasks:
            return None
        
        task = self.active_tasks[task_id]
        
        # Check if task is complete
        if task["future"].done():
            if task["future"].exception():
                task["status"] = "failed"
                task["error"] = str(task["future"].exception())
            else:
                task["status"] = "completed"
                task["result"] = task["future"].result()
                task["progress"] = 100
        
        return {
            "task_id": task_id,
            "type": task["type"],
            "status": task["status"],
            "started_at": task["started_at"],
            "progress": task["progress"],
            "result": task["result"],
            "error": task["error"]
        }
    
    def list_active_tasks(self) -> List[Dict]:
        """List all active background tasks."""
        return [
            self.get_task_status(task_id)
            for task_id in self.active_tasks.keys()
        ]
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        if task_id not in self.active_tasks:
            return False
        
        task = self.active_tasks[task_id]
        if task["status"] == "running":
            task["future"].cancel()
            task["status"] = "cancelled"
            return True
        
        return False
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Clean up completed tasks older than specified hours."""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        to_remove = []
        for task_id, task in self.active_tasks.items():
            if task["status"] in ["completed", "failed", "cancelled"]:
                age = current_time - task["started_at"]
                if age > max_age_seconds:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.active_tasks[task_id]
    
    def _monitor_task(self, task_id: str):
        """Monitor a task and update its progress."""
        task = self.active_tasks[task_id]
        
        while not task["future"].done():
            # Simulate progress updates for long-running tasks
            if task["type"] == "batch_test_generation":
                elapsed = time.time() - task["started_at"]
                if elapsed > 30:  # After 30 seconds, show progress
                    task["progress"] = min(90, int(elapsed / 60 * 100))
            
            time.sleep(1)
        
        # Task is complete
        if task["future"].exception():
            task["status"] = "failed"
            task["error"] = str(task["future"].exception())
        else:
            task["status"] = "completed"
            task["result"] = task["future"].result()
            task["progress"] = 100


# Global background processor instance
background_processor = BackgroundProcessor()


def submit_batch_test_generation(journey: str, max_cases: int = 500, 
                                context_top_k: int = 50, provider: str = None) -> str:
    """Submit a batch test generation task."""
    task_id = f"test_gen_{journey}_{int(time.time())}"
    
    def generate_batch_tests():
        """Generate tests in batches to handle large numbers."""
        async def _async_generate():
            all_tests = []
            batch_size = 50
            test_generator = TestGenerator()
            
            for i in range(0, max_cases, batch_size):
                current_batch_size = min(batch_size, max_cases - i)
                result = await test_generator.generate_test_cases(
                    journey=journey,
                    max_cases=current_batch_size,
                    context=context or "",
                    source_types=None,
                    model=provider,
                    temperature=0.2
                )
                batch_tests = result.get("test_cases", [])
                all_tests.extend(batch_tests)
                
                # Small delay between batches to avoid overwhelming the LLM
                time.sleep(1)
            
            return {
                "journey": journey,
                "total_tests": len(all_tests),
                "tests": all_tests
            }
        
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_async_generate())
        finally:
            loop.close()
    
    return background_processor.submit_task(
        "batch_test_generation",
        task_id,
        generate_batch_tests
    )


def submit_document_cleanup(journey: str, older_than_days: int = 90) -> str:
    """Submit a document cleanup task to remove old versions."""
    task_id = f"cleanup_{journey}_{int(time.time())}"
    
    def cleanup_old_documents():
        """Clean up old document versions and their associated data."""
        # This would implement cleanup logic for old documents
        # For now, return a placeholder
        return {
            "journey": journey,
            "cleanup_type": "document_cleanup",
            "older_than_days": older_than_days,
            "status": "completed"
        }
    
    return background_processor.submit_task(
        "document_cleanup",
        task_id,
        cleanup_old_documents
    )


def submit_impact_analysis(journey: str, from_version: str, to_version: str) -> str:
    """Submit an impact analysis task for requirement changes."""
    task_id = f"impact_{journey}_{int(time.time())}"
    
    def analyze_impact():
        """Analyze the impact of requirement changes."""
        return background_processor.requirements_manager.analyze_changes(
            journey=journey,
            from_version=from_version,
            to_version=to_version
        )
    
    return background_processor.submit_task(
        "impact_analysis",
        task_id,
        analyze_impact
    )
