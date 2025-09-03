import os
import json
from typing import List, Dict, Any
from fastapi import HTTPException
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
            
            # Search for relevant requirements context - ONLY from uploaded documents for this journey
            # Use a more specific search that focuses on the actual requirements content
            if context:
                search_query = context
            else:
                # Search for core requirement content in the journey documents
                search_query = f"{journey} requirements functional specifications business rules"
            
            context_results = await self.rag_service.search(
                query=search_query,
                top_k=config.top_k,
                metadata_filter={"journey": journey}  # Strictly filter by journey
            )
            
            if not context_results:
                raise HTTPException(
                    status_code=400, 
                    detail=f"No requirements documents found for journey '{journey}'. Please upload requirement documents for this journey before generating test cases."
                )
            
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
            
        except HTTPException:
            # Re-raise HTTP exceptions to be handled by FastAPI
            raise
        except Exception as e:
            error_message = str(e)
            
            # Provide more user-friendly error messages for common API issues
            if "503 Server Error" in error_message or "Service Unavailable" in error_message:
                error_message = "The AI service is temporarily unavailable due to high demand. Please try again in a few moments."
            elif "429" in error_message or "rate limit" in error_message.lower():
                error_message = "Rate limit exceeded. Please wait a moment before trying again."
            elif "timeout" in error_message.lower():
                error_message = "The AI service is taking longer than expected to respond. Please try again."
            elif "connection" in error_message.lower():
                error_message = "Unable to connect to the AI service. Please check your internet connection and try again."
            
            return {
                "status": "error",
                "message": f"Test generation failed: {error_message}",
                "retry_suggested": True
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
        """Build context from search results - strictly from uploaded documents"""
        context_parts = []
        
        # Add document information header
        context_parts.append("=== UPLOADED REQUIREMENTS DOCUMENTS ===")
        
        # Group results by document source for better organization
        doc_groups = {}
        for result in search_results[:10]:  # Use more results for comprehensive context
            metadata = result.get('metadata', {})
            doc_uri = metadata.get('document_uri', 'Unknown')
            source_type = metadata.get('source_type', 'Unknown')
            version = metadata.get('version', 'Unknown')
            
            doc_key = f"{source_type}_{doc_uri}_{version}"
            if doc_key not in doc_groups:
                doc_groups[doc_key] = {
                    'source_type': source_type,
                    'document_uri': doc_uri,
                    'version': version,
                    'summary': metadata.get('summary', 'No summary available'),
                    'chunks': []
                }
            doc_groups[doc_key]['chunks'].append(result.get('text', ''))
        
        # Build structured context from documents
        for i, (doc_key, doc_info) in enumerate(doc_groups.items(), 1):
            context_parts.append(f"\nDocument {i}: {doc_info['source_type'].upper()}")
            context_parts.append(f"Summary: {doc_info['summary']}")
            context_parts.append(f"Version: {doc_info['version']}")
            context_parts.append("Content Excerpts:")
            
            # Add document chunks (limit to prevent overwhelming the LLM)
            for j, chunk in enumerate(doc_info['chunks'][:3], 1):
                context_parts.append(f"  {j}. {chunk[:500]}...")
            
            context_parts.append("-" * 50)
        
        # Add additional context if provided
        if additional_context.strip():
            context_parts.append(f"\nAdditional Context: {additional_context}")
        
        return "\n".join(context_parts)
    
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
        You are a QA Engineer creating test cases STRICTLY based on the uploaded requirements documents provided below. 
        
        IMPORTANT CONSTRAINTS:
        - Generate test cases ONLY from the specific requirements, specifications, and business rules found in the uploaded documents
        - DO NOT create generic test cases or assumptions beyond what is documented
        - Each test case must be traceable to specific requirements mentioned in the documents
        - If insufficient information is available in the documents, generate fewer but more accurate test cases
        
        Generate {max_cases} comprehensive test cases for the {journey} journey based EXCLUSIVELY on the following uploaded documents:
        
        {context}
        
        Each test case should include:
        1. Key (unique identifier like TC001, TC002, etc.)
        2. Name (clear, descriptive test case name based on specific requirements)
        3. Status (always "Draft" for new test cases)
        4. Precondition Objective (what must be established before testing, based on document requirements)
        5. Folder (category/module name from the {journey} journey)
        6. Priority (High/Medium/Low based on requirement criticality in documents)
        7. Component Labels (system components mentioned in the documents)
        8. Owner (QA Team)
        9. Estimated Time (estimated execution time in minutes)
        10. Coverage (specific functionality coverage as described in documents)
        11. Test Script (detailed test steps derived from documented workflows and business rules)
        
        Generate the test cases in JSON format:
        [
            {{
                "key": "TC001",
                "name": "[Test name derived from specific requirement]",
                "status": "Draft",
                "precondition_objective": "[Based on documented prerequisites]",
                "folder": "{journey}",
                "priority": "[Based on requirement criticality]",
                "component_labels": ["[Components mentioned in documents]"],
                "owner": "QA Team",
                "estimated_time": "[X] minutes",
                "coverage": "[Specific functionality from documents]",
                "test_script": "[Step-by-step procedure based on documented workflows]"
            }}
        ]
        
        Focus ONLY on what is explicitly documented:
        - Functional requirements and business rules mentioned in the documents
        - Workflows and processes described in the uploaded requirements
        - Validation rules and error conditions specified in the documents
        - Integration points and dependencies mentioned in the requirements
        - Compliance and regulatory requirements explicitly stated in the documents
        
        REMEMBER: Generate test cases only from the uploaded document content provided above. Do not add generic test scenarios.
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
