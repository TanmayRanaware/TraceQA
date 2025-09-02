from fastapi import APIRouter, HTTPException
from ..schemas import RequirementIngestRequest, RequirementSearchRequest, RequirementDiffRequest, FactCheckRequest
from ..services.requirements_manager import RequirementsManager
from ..providers.provider_factory import get_provider

router = APIRouter()
requirements_manager = RequirementsManager()


@router.get("/requirements/provider-info")
async def get_provider_info():
	"""Get information about the currently active LLM provider."""
	try:
		provider = get_provider()
		provider_info = {
			"provider_type": provider.__class__.__name__,
			"provider_class": str(provider.__class__),
			"is_gemini": "gemini" in provider.__class__.__name__.lower(),
			"is_openai": "openai" in provider.__class__.__name__.lower(),
			"is_ollama": "ollama" in provider.__class__.__name__.lower(),
		}
		return provider_info
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to get provider info: {str(e)}")


@router.post("/requirements/test-gemini")
async def test_gemini_integration():
	"""Test the Gemini integration with a simple prompt."""
	try:
		provider = get_provider()
		if "gemini" not in provider.__class__.__name__.lower():
			return {"message": "Gemini is not the active provider", "active_provider": provider.__class__.__name__}
		
		# Test with a simple prompt
		test_prompt = "Explain how AI works in a few words"
		response = provider.complete([{"role": "user", "content": test_prompt}], model="gemini-2.0-flash")
		
		return {
			"message": "Gemini integration test successful",
			"test_prompt": test_prompt,
			"response": response,
			"provider": provider.__class__.__name__
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Gemini test failed: {str(e)}")


@router.post("/requirements/ingest")
async def ingest_requirement(req: RequirementIngestRequest):
	"""Ingest a new requirement document and index it for search."""
	try:
		result = await requirements_manager.ingest_requirement(
			file_path=req.document_uri,
			journey=req.journey,
			source_type=req.source_type,
			metadata={
				"effective_date": req.effective_date,
				"notes": req.notes
			}
		)
		return result
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to ingest requirement: {str(e)}")


@router.post("/requirements/search")
async def search_requirements(req: RequirementSearchRequest):
	"""Search requirements using RAG."""
	try:
		results = await requirements_manager.search_requirements(
			journey=req.journey,
			query=req.query,
			top_k=req.top_k
		)
		return {
			"journey": req.journey,
			"query": req.query,
			"results": results,
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/requirements/analyze-changes")
async def analyze_requirement_changes(req: RequirementDiffRequest):
	"""Analyze changes between two versions with semantic analysis and test impact assessment."""
	try:
		analysis = await requirements_manager.analyze_changes(
			journey=req.journey,
			from_version=req.from_version,
			to_version=req.to_version
		)
		return analysis
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Change analysis failed: {str(e)}")


@router.post("/requirements/diff")
async def diff_requirements(req: RequirementDiffRequest):
	"""Get basic diff between two versions."""
	try:
		from ..services.versioning import diff_versions
		diff = diff_versions(req.journey, req.from_version, req.to_version)
		return {"journey": req.journey, "diff": diff}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Diff failed: {str(e)}")


@router.get("/requirements/versions")
async def requirement_versions(journey: str | None = None):
	"""Get versions for a journey or all journeys."""
	try:
		from ..services.versioning import list_versions
		versions = list_versions(journey)
		return {"versions": versions}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to get versions: {str(e)}")


@router.get("/requirements/timeline/{journey}")
async def requirement_timeline(journey: str):
	"""Get complete timeline with change analysis for a journey."""
	try:
		timeline = await requirements_manager.get_requirement_timeline(journey)
		return {"journey": journey, "timeline": timeline}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")


@router.post("/requirements/fact-check")
async def fact_check(req: FactCheckRequest):
	"""Fact-check a claim against stored requirements."""
	try:
		result = await requirements_manager.fact_check_claim(
			journey=req.journey,
			claim=req.claim,
			top_k=req.top_k
		)
		return result
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Fact-check failed: {str(e)}")


@router.get("/requirements/supported-formats")
async def get_supported_formats():
	"""Get list of supported document formats."""
	try:
		from ..services.document_processor import get_supported_formats
		formats = get_supported_formats()
		return {"supported_formats": formats}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to get formats: {str(e)}")


