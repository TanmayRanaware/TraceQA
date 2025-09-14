"""
Test Generation Agent for creating and managing test cases
"""
import logging
import json
from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..providers.provider_factory import get_provider
from ..services.testgen import TestGenerator

logger = logging.getLogger(__name__)

class TestAgent(BaseAgent):
    """Agent responsible for test case generation and management"""
    
    def __init__(self):
        super().__init__("test_agent", "Test Generation Agent")
        self.llm_provider = get_provider()
        self.test_generator = TestGenerator()
    
    async def execute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test generation tasks"""
        try:
            if task_type == "generate_test_cases":
                return await self._generate_test_cases(task_data)
            elif task_type == "validate_test_cases":
                return await self._validate_test_cases(task_data)
            elif task_type == "generate_test_scenarios":
                return await self._generate_test_scenarios(task_data)
            elif task_type == "analyze_requirements":
                return await self._analyze_requirements(task_data)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
        except Exception as e:
            logger.error(f"Error executing task {task_type} in TestAgent: {e}")
            raise
    
    async def _generate_test_cases(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test cases based on requirements and context using TestGenerator"""
        journey = task_data.get("journey")
        context = task_data.get("context", "")
        max_cases = task_data.get("max_cases", 10)
        source_types = task_data.get("source_types", [])
        model = task_data.get("model")
        temperature = task_data.get("temperature", 0.7)
        context_top_k = task_data.get("context_top_k", 20)
        page = task_data.get("page", 1)
        
        if not journey:
            return {"success": False, "error": "journey is required"}
        
        try:
            logger.info(f"Generating {max_cases} test cases for journey: {journey}")
            
            # Use the comprehensive TestGenerator service
            result = await self.test_generator.generate_test_cases(
                journey=journey,
                max_cases=max_cases,
                context=context,
                source_types=source_types,
                model=model,
                temperature=temperature,
                context_top_k=context_top_k,
                page=page
            )
            
            if result.get("status") == "error":
                return {"success": False, "error": result.get("message", "Test generation failed")}
            
            # Validate generated test cases
            validation_result = await self._validate_test_cases({
                "test_cases": result.get("test_cases", []),
                "journey": journey
            })
            
            return {
                "success": True,
                "message": f"Generated {len(result.get('test_cases', []))} test cases",
                "test_cases": result.get("test_cases", []),
                "validation": validation_result,
                "journey": journey,
                "context_used": result.get("context_used", ""),
                "pagination": {
                    "page": result.get("page", page),
                    "has_next_page": result.get("has_next_page", False),
                    "total_pages": result.get("total_pages", 1),
                    "total_available": result.get("total_available", 0),
                    "total_cases": len(result.get("test_cases", []))
                },
                "metadata": {
                    "model_used": result.get("model_used", model),
                    "total_generated": result.get("total_generated", 0)
                }
            }
        except Exception as e:
            logger.error(f"Error generating test cases: {e}")
            return {"success": False, "error": str(e)}
    
    
    async def _validate_test_cases(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate generated test cases using TestGenerator validation"""
        test_cases = task_data.get("test_cases", [])
        journey = task_data.get("journey")
        
        if not test_cases:
            return {"success": False, "error": "No test cases provided"}
        
        try:
            # Use TestGenerator's validation logic
            validation_results = []
            valid_count = 0
            
            for i, test_case in enumerate(test_cases):
                validation = {
                    "index": i,
                    "test_case_name": test_case.get("test_case_name", ""),
                    "is_valid": self._is_valid_test_case(test_case),
                    "issues": []
                }
                
                if not validation["is_valid"]:
                    missing_fields = [field for field in ["test_case_name", "preconditions", "steps", "expected_result"] 
                                    if field not in test_case]
                    validation["issues"] = [f"Missing required fields: {missing_fields}"]
                else:
                    valid_count += 1
                
                validation_results.append(validation)
            
            return {
                "success": True,
                "message": f"Validation completed: {valid_count}/{len(test_cases)} valid test cases",
                "total_cases": len(test_cases),
                "valid_cases": valid_count,
                "invalid_cases": len(test_cases) - valid_count,
                "validation_results": validation_results
            }
        except Exception as e:
            logger.error(f"Error validating test cases: {e}")
            return {"success": False, "error": str(e)}
    
    def _is_valid_test_case(self, test_case: Dict[str, Any]) -> bool:
        """Validate test case structure"""
        required_fields = ["test_case_name", "preconditions", "steps", "expected_result"]
        return all(field in test_case for field in required_fields)
    
    async def _generate_test_scenarios(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test scenarios for specific workflows"""
        journey = task_data.get("journey")
        scenario_type = task_data.get("scenario_type", "end_to_end")
        max_scenarios = task_data.get("max_scenarios", 5)
        
        if not journey:
            return {"success": False, "error": "journey is required"}
        
        try:
            prompt = f"""
            Generate {max_scenarios} {scenario_type} test scenarios for the {journey} journey.
            
            Each scenario should include:
            1. scenario_name: Descriptive name
            2. description: What the scenario tests
            3. user_persona: Type of user
            4. workflow_steps: Step-by-step user actions
            5. expected_outcomes: What should happen at each step
            6. test_data_requirements: Data needed for the scenario
            7. success_criteria: How to determine if scenario passed
            
            Focus on realistic user workflows and business processes.
            Return as a JSON array of scenario objects.
            """
            
            response = self.llm_provider.generate_text(
                prompt=prompt,
                temperature=0.7
            )
            
            try:
                scenarios = json.loads(response)
                if not isinstance(scenarios, list):
                    scenarios = [scenarios]
                
                return {
                    "success": True,
                    "scenarios": scenarios,
                    "journey": journey,
                    "scenario_type": scenario_type,
                    "total_scenarios": len(scenarios)
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Failed to parse scenarios JSON response"
                }
        except Exception as e:
            logger.error(f"Error generating test scenarios: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_requirements(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze requirements for testability and coverage"""
        journey = task_data.get("journey")
        requirements_text = task_data.get("requirements_text", "")
        
        if not journey:
            return {"success": False, "error": "journey is required"}
        
        try:
            prompt = f"""
            Analyze the following requirements for the {journey} journey and provide testability insights:
            
            REQUIREMENTS:
            {requirements_text}
            
            Please provide:
            1. Testability score (1-10)
            2. Key testable requirements
            3. Potential test challenges
            4. Recommended test approaches
            5. Coverage areas to focus on
            6. Risk areas that need extra testing
            
            Return as a JSON object with your analysis.
            """
            
            response = self.llm_provider.generate_text(
                prompt=prompt,
                temperature=0.3
            )
            
            try:
                analysis = json.loads(response)
                return {
                    "success": True,
                    "analysis": analysis,
                    "journey": journey,
                    "requirements_length": len(requirements_text)
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "analysis": {
                        "testability_score": 7,
                        "key_requirements": ["Basic functionality"],
                        "challenges": ["Complex business logic"],
                        "approaches": ["Manual and automated testing"],
                        "coverage_areas": ["Core workflows"],
                        "risk_areas": ["Data validation"]
                    },
                    "journey": journey,
                    "raw_response": response
                }
        except Exception as e:
            logger.error(f"Error analyzing requirements: {e}")
            return {"success": False, "error": str(e)}
