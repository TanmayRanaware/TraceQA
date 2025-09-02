import os
import json
from typing import List, Dict, Any
from ..providers.provider_factory import get_provider
from ..services.rag import RAGService
from ..config import config

class TestGenerator:
    def __init__(self):
        self.llm_provider = get_provider()
        self.rag_service = RAGService()
    
    async def generate_test_cases(
        self,
        journey: str,
        max_cases: int = 10,
        context: str = "",
        source_types: List[str] = None,
        model: str = None,
        temperature: float = None
    ) -> Dict[str, Any]:
        """Generate test cases for a specific journey"""
        try:
            # Use configuration defaults if not specified
            model = model or config.llm.default_model
            temperature = temperature or config.llm.default_temperature
            
            # Search for relevant requirements context
            search_query = f"test requirements specifications {context}".strip()
            context_results = await self.rag_service.search(
                query=search_query,
                top_k=config.top_k,
                metadata_filter={"journey": journey}
            )
            
            if not context_results:
                return {
                    "status": "error",
                    "message": f"No requirements found for journey: {journey}"
                }
            
            # Build context from search results
            context_text = self._build_context(context_results, context)
            
            # Generate test cases using LLM
            test_cases = await self._generate_with_llm(
                journey=journey,
                context=context_text,
                max_cases=max_cases,
                model=model,
                temperature=temperature
            )
            
            return {
                "status": "success",
                "journey": journey,
                "test_cases": test_cases,
                "total_generated": len(test_cases),
                "context_used": context_text[:500] + "..." if len(context_text) > 500 else context_text,
                "model_used": model
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Test generation failed: {str(e)}"
            }
    
    async def generate_batch_tests(
        self,
        journeys: List[str],
        max_cases_per_journey: int = 5,
        context: str = "",
        model: str = None
    ) -> Dict[str, Any]:
        """Generate test cases for multiple journeys in batch"""
        try:
            results = {}
            total_tests = 0
            
            for journey in journeys:
                journey_result = await self.generate_test_cases(
                    journey=journey,
                    max_cases=max_cases_per_journey,
                    context=context,
                    model=model
                )
                
                results[journey] = journey_result
                if journey_result["status"] == "success":
                    total_tests += journey_result["total_generated"]
            
            return {
                "status": "success",
                "journeys_processed": len(journeys),
                "total_tests_generated": total_tests,
                "results": results
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Batch test generation failed: {str(e)}"
            }
    
    def _build_context(self, search_results: List[Dict[str, Any]], additional_context: str) -> str:
        """Build context from search results and additional input"""
        context_parts = []
        
        # Add additional context if provided
        if additional_context.strip():
            context_parts.append(f"Additional Context: {additional_context}")
        
        # Add requirements context
        requirements_context = []
        for i, result in enumerate(search_results[:5]):  # Limit to top 5 results
            requirements_context.append(
                f"Requirement {i+1}:\n{result.get('text', '')[:300]}..."
            )
        
        if requirements_context:
            context_parts.append("Requirements Context:\n" + "\n\n".join(requirements_context))
        
        return "\n\n".join(context_parts)
    
    async def _generate_with_llm(
        self,
        journey: str,
        context: str,
        max_cases: int,
        model: str,
        temperature: float
    ) -> List[Dict[str, Any]]:
        """Generate test cases using LLM"""
        prompt = f"""
        Generate {max_cases} comprehensive test cases for the {journey} journey based on the following requirements context.
        
        Each test case should include:
        1. Test ID (TC001, TC002, etc.)
        2. Test Title (clear, descriptive)
        3. Test Description (what is being tested)
        4. Preconditions (what must be in place)
        5. Test Steps (numbered steps to execute)
        6. Expected Results (what should happen)
        7. Test Data (any specific data needed)
        8. Priority (High/Medium/Low)
        9. Test Type (Functional/Non-Functional/Integration/Regression)
        
        Requirements Context:
        {context}
        
        Generate the test cases in JSON format:
        [
            {{
                "test_id": "TC001",
                "title": "Test Title",
                "description": "Test Description",
                "preconditions": ["Precondition 1", "Precondition 2"],
                "test_steps": ["Step 1", "Step 2", "Step 3"],
                "expected_results": ["Expected Result 1", "Expected Result 2"],
                "test_data": "Specific test data if needed",
                "priority": "High",
                "test_type": "Functional"
            }}
        ]
        
        Focus on:
        - Edge cases and boundary conditions
        - Error scenarios and exception handling
        - Integration points with other systems
        - Compliance and regulatory requirements
        - Performance and security considerations
        """
        
        response = self.llm_provider.complete(
            [{"role": "user", "content": prompt}],
            model=model,
            temperature=temperature
        )
        
        # Try to parse JSON response
        try:
            # Find JSON array in response
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                test_cases = json.loads(json_match.group())
                if isinstance(test_cases, list):
                    return test_cases
        except:
            pass
        
        # Fallback: generate structured test cases manually
        return self._generate_fallback_tests(journey, max_cases, context)
    
    def _generate_fallback_tests(self, journey: str, max_cases: int, context: str) -> List[Dict[str, Any]]:
        """Generate fallback test cases if LLM parsing fails"""
        test_cases = []
        
        # Generate basic test cases based on journey type
        base_tests = [
            {
                "test_id": "TC001",
                "title": f"Basic {journey} Functionality",
                "description": f"Verify basic {journey} functionality works as expected",
                "preconditions": ["System is accessible", "User has proper permissions"],
                "test_steps": ["Navigate to journey", "Execute basic operation", "Verify result"],
                "expected_results": ["Operation completes successfully", "Result is as expected"],
                "test_data": "Standard test data",
                "priority": "High",
                "test_type": "Functional"
            },
            {
                "test_id": "TC002",
                "title": f"{journey} Error Handling",
                "description": f"Verify {journey} handles errors gracefully",
                "preconditions": ["System is accessible", "Error conditions can be triggered"],
                "test_steps": ["Trigger error condition", "Observe system response"],
                "expected_results": ["Error is handled gracefully", "User receives clear error message"],
                "test_data": "Invalid test data",
                "priority": "Medium",
                "test_type": "Functional"
            }
        ]
        
        test_cases.extend(base_tests)
        
        # Add more generic test cases if needed
        if max_cases > 2:
            for i in range(3, min(max_cases + 1, 6)):
                test_cases.append({
                    "test_id": f"TC{i:03d}",
                    "title": f"{journey} Test Case {i}",
                    "description": f"Additional test case for {journey} functionality",
                    "preconditions": ["System is accessible"],
                    "test_steps": ["Execute test operation", "Verify results"],
                    "expected_results": ["Operation completes successfully"],
                    "test_data": "Test data",
                    "priority": "Medium",
                    "test_type": "Functional"
                })
        
        return test_cases[:max_cases]
