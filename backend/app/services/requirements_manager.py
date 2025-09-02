import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..providers.provider_factory import get_provider
from ..services.storage import save_object
from ..services.versioning import record_version, list_versions, diff_versions, load_version_text
from ..services.rag import RAGService
from ..services.document_processor import extract_text_from_file
from ..config import config

class RequirementsManager:
    def __init__(self):
        self.rag_service = RAGService()
        self.llm_provider = get_provider()
    
    async def ingest_requirement(
        self,
        file_path: str,
        journey: str,
        source_type: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Ingest a new requirement document"""
        try:
            # Extract text from document
            text = extract_text_from_file(file_path)
            if not text:
                raise ValueError("Could not extract text from document")
            
            # Generate summary using LLM
            summary = await self._generate_summary(text, journey, source_type)
            
            # Save document to storage
            with open(file_path, 'rb') as f:
                file_content = f.read()
            file_uri = save_object(
                content=file_content,
                filename=os.path.basename(file_path)
            )
            
            # Record version
            version_id = record_version(
                journey=journey,
                source_type=source_type,
                document_uri=file_uri,
                summary=summary,
                effective_date=metadata.get('effective_date') if metadata else None
            )
            
            # Index in RAG
            rag_metadata = {
                "journey": journey,
                "source_type": source_type,
                "version": version_id,
                "document_uri": file_uri,
                "summary": summary
            }
            if metadata:
                rag_metadata.update(metadata)
            
            await self.rag_service.index_text(
                text=text,
                metadata=rag_metadata
            )
            
            return {
                "status": "success",
                "version": version_id,
                "summary": summary,
                "document_uri": file_uri,
                "message": f"Requirement ingested successfully for {journey}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to ingest requirement: {str(e)}"
            }
    
    async def search_requirements(
        self,
        journey: str,
        query: str,
        top_k: int = None,
        source_types: List[str] = None
    ) -> Dict[str, Any]:
        """Search requirements using RAG"""
        try:
            top_k = top_k or config.top_k
            
            # Build metadata filter
            metadata_filter = {"journey": journey}
            if source_types:
                metadata_filter["source_type"] = {"$in": source_types}
            
            # Search using RAG
            results = await self.rag_service.search(
                query=query,
                top_k=top_k,
                metadata_filter=metadata_filter
            )
            
            return {
                "status": "success",
                "results": results,
                "query": query,
                "journey": journey,
                "total_results": len(results)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Search failed: {str(e)}"
            }
    
    async def fact_check(
        self,
        journey: str,
        claim: str
    ) -> Dict[str, Any]:
        """Fact-check a claim against requirements"""
        try:
            # Search for relevant evidence
            evidence_results = await self.rag_service.search(
                query=claim,
                top_k=config.top_k,
                metadata_filter={"journey": journey}
            )
            
            if not evidence_results:
                return {
                    "status": "success",
                    "journey": journey,
                    "claim": claim,
                    "evidence": [],
                    "evidence_analysis": {
                        "strength": "very_weak",
                        "confidence": 0.0,
                        "sources": 0,
                        "total_evidence": 0
                    }
                }
            
            # Analyze evidence using LLM
            evidence_analysis = await self._analyze_evidence(claim, evidence_results)
            
            return {
                "status": "success",
                "journey": journey,
                "claim": claim,
                "evidence": evidence_results,
                "evidence_analysis": evidence_analysis
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Fact-check failed: {str(e)}"
            }
    
    async def analyze_changes(
        self,
        journey: str,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """Analyze changes between two versions"""
        try:
            # Get version diffs
            diff_result = await diff_versions(journey, version1, version2)
            
            if not diff_result:
                return {
                    "status": "error",
                    "message": "Could not generate diff between versions"
                }
            
            # Analyze semantic changes using LLM
            semantic_analysis = await self._analyze_semantic_changes(
                diff_result["diff_text"],
                journey
            )
            
            return {
                "status": "success",
                "journey": journey,
                "version1": version1,
                "version2": version2,
                "diff": diff_result,
                "semantic_analysis": semantic_analysis
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Change analysis failed: {str(e)}"
            }
    
    async def get_timeline(self, journey: str) -> Dict[str, Any]:
        """Get timeline of requirement changes for a journey"""
        try:
            versions = await list_versions(journey)
            
            timeline = []
            for version in versions:
                timeline.append({
                    "version": version["version"],
                    "source_type": version["source_type"],
                    "summary": version["summary"],
                    "effective_date": version["effective_date"],
                    "created_at": version["created_at"]
                })
            
            return {
                "status": "success",
                "journey": journey,
                "timeline": timeline,
                "total_versions": len(timeline)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get timeline: {str(e)}"
            }
    
    async def _generate_summary(
        self,
        text: str,
        journey: str,
        source_type: str
    ) -> str:
        """Generate summary using LLM"""
        prompt = f"""
        Generate a concise summary (2-3 sentences) of the following {source_type} document for the {journey} journey.
        
        Document text:
        {text[:2000]}...
        
        Summary:
        """
        
        response = self.llm_provider.complete(
            [{"role": "user", "content": prompt}],
            model=config.llm.default_model,
            temperature=config.llm.default_temperature
        )
        
        return response.strip()
    
    async def _analyze_evidence(
        self,
        claim: str,
        evidence_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze evidence strength and confidence"""
        evidence_text = "\n\n".join([
            f"Evidence {i+1}: {result['text'][:500]}..."
            for i, result in enumerate(evidence_results)
        ])
        
        prompt = f"""
        Analyze the following claim against the provided evidence and rate:
        1. Evidence strength: very_weak, weak, moderate, strong
        2. Confidence: 0.0 to 1.0
        3. Number of relevant sources
        4. Total evidence count
        
        Claim: {claim}
        
        Evidence:
        {evidence_text}
        
        Provide your analysis in JSON format:
        {{
            "strength": "moderate",
            "confidence": 0.7,
            "sources": 3,
            "total_evidence": 5
        }}
        """
        
        response = await self.llm_provider.complete(
            [{"role": "user", "content": prompt}],
            model=config.llm.default_model,
            temperature=config.llm.default_temperature
        )
        
        try:
            # Try to parse JSON response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback to default analysis
        return {
            "strength": "moderate",
            "confidence": 0.5,
            "sources": len(evidence_results),
            "total_evidence": len(evidence_results)
        }
    
    async def _analyze_semantic_changes(
        self,
        diff_text: str,
        journey: str
    ) -> Dict[str, Any]:
        """Analyze semantic impact of changes"""
        prompt = f"""
        Analyze the following changes to requirements for the {journey} journey.
        Identify:
        1. Major changes (new features, removed functionality)
        2. Minor changes (clarifications, formatting)
        3. Impact on existing test cases
        4. Recommendations for test case updates
        
        Changes:
        {diff_text}
        
        Provide your analysis in a structured format.
        """
        
        response = await self.llm_provider.complete(
            [{"role": "user", "content": prompt}],
            model=config.llm.default_model,
            temperature=config.llm.default_temperature
        )
        
        return {
            "analysis": response.strip(),
            "journey": journey,
            "timestamp": datetime.utcnow().isoformat()
        }
