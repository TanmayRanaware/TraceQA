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
        """Answer questions and fact-check claims against uploaded requirements documents"""
        try:
            # Search for relevant evidence from uploaded documents
            # Use multiple search strategies to find comprehensive information
            search_queries = [
                claim,  # Original question
                f"{journey} {claim}",  # Journey-specific search
                # Extract key terms for broader search
                " ".join([word for word in claim.split() if len(word) > 3])
            ]
            
            all_evidence = []
            seen_chunks = set()
            
            for query in search_queries:
                results = await self.rag_service.search(
                    query=query,
                    top_k=5,  # Get more results per query
                    metadata_filter={"journey": journey}
                )
                
                # Deduplicate results based on text content
                for result in results:
                    text_hash = hash(result.get('text', '')[:200])  # Hash first 200 chars
                    if text_hash not in seen_chunks:
                        seen_chunks.add(text_hash)
                        all_evidence.append(result)
            
            # Limit total results and sort by relevance
            evidence_results = all_evidence[:config.top_k]
            
            if not evidence_results:
                return {
                    "status": "success",
                    "journey": journey,
                    "claim": claim,
                    "answer": "No relevant information found in the uploaded documents for this journey. Please ensure you have uploaded the appropriate requirement documents.",
                    "evidence": [],
                    "confidence": 0.0,
                    "sources_used": 0
                }
            
            # Generate comprehensive answer based on evidence
            answer = await self._generate_answer_from_evidence(claim, evidence_results, journey)
            
            # Analyze evidence strength for confidence scoring
            evidence_analysis = await self._analyze_evidence(claim, evidence_results)
            
            return {
                "status": "success",
                "journey": journey,
                "claim": claim,
                "answer": answer,
                "evidence": evidence_results,
                "confidence": evidence_analysis.get("confidence", 0.5),
                "sources_used": len(evidence_results),
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
            versions = list_versions(journey)
            
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
    
    async def _generate_answer_from_evidence(
        self,
        question: str,
        evidence_results: List[Dict[str, Any]],
        journey: str
    ) -> str:
        """Generate comprehensive answer based on evidence from uploaded documents"""
        
        # Organize evidence by document source
        doc_evidence = {}
        for result in evidence_results:
            metadata = result.get('metadata', {})
            doc_key = f"{metadata.get('source_type', 'Unknown')} - {metadata.get('version', 'Unknown')}"
            if doc_key not in doc_evidence:
                doc_evidence[doc_key] = {
                    'source_type': metadata.get('source_type', 'Unknown'),
                    'version': metadata.get('version', 'Unknown'),
                    'summary': metadata.get('summary', 'No summary available'),
                    'chunks': []
                }
            doc_evidence[doc_key]['chunks'].append(result.get('text', ''))
        
        # Build structured evidence context
        evidence_context = f"=== UPLOADED REQUIREMENTS DOCUMENTS FOR {journey.upper()} ===\n\n"
        
        for i, (doc_key, doc_info) in enumerate(doc_evidence.items(), 1):
            evidence_context += f"Document {i}: {doc_info['source_type'].upper()}\n"
            evidence_context += f"Version: {doc_info['version']}\n"
            evidence_context += f"Summary: {doc_info['summary']}\n"
            evidence_context += "Relevant Content:\n"
            
            for j, chunk in enumerate(doc_info['chunks'][:3], 1):  # Limit to 3 chunks per document
                evidence_context += f"  {j}. {chunk[:800]}...\n"
            
            evidence_context += "-" * 60 + "\n\n"
        
        prompt = f"""
        You are an expert analyst answering questions based STRICTLY on uploaded requirement documents.
        
        QUESTION: {question}
        
        JOURNEY: {journey}
        
        UPLOADED DOCUMENTS CONTENT:
        {evidence_context}
        
        INSTRUCTIONS:
        1. Answer the question based ONLY on the information provided in the uploaded documents above
        2. If the documents contain specific details (numbers, amounts, percentages, conditions), include them in your answer
        3. If the question asks about specific calculations or amounts, provide the exact figures if available in the documents
        4. If the information is not available in the uploaded documents, clearly state that
        5. Cite which document type (FSD, Addendum, etc.) contains the information
        6. Be specific and detailed in your response
        7. If there are multiple scenarios or conditions mentioned in the documents, explain them clearly
        
        FORMAT YOUR ANSWER AS:
        
        **Answer:** [Your detailed answer based on the uploaded documents]
        
        **Source:** [Which document(s) contain this information]
        
        **Additional Details:** [Any relevant context, conditions, or calculations from the documents]
        
        **Note:** [Any limitations or missing information]
        
        Remember: Answer ONLY based on what is explicitly stated in the uploaded requirement documents provided above.
        """
        
        response = self.llm_provider.complete(
            [{"role": "user", "content": prompt}],
            model=config.llm.default_model,
            temperature=0.1  # Lower temperature for more factual responses
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
        
        response = self.llm_provider.complete(
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
        
        response = self.llm_provider.complete(
            [{"role": "user", "content": prompt}],
            model=config.llm.default_model,
            temperature=config.llm.default_temperature
        )
        
        return {
            "analysis": response.strip(),
            "journey": journey,
            "timestamp": datetime.utcnow().isoformat()
        }
