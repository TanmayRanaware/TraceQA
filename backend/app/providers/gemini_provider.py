import os
import json
import requests
import time
import random
from typing import List, Dict, Any
from .llm_base import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self):
        # Get API key from environment variable for security
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
    def _retry_request(self, func, max_retries=3, base_delay=1):
        """Retry wrapper for API requests with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return func()
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    # Last attempt, re-raise the exception
                    raise e
                
                # Check if it's a retryable error (5xx, 429, or connection errors)
                if (hasattr(e, 'response') and e.response is not None and 
                    (e.response.status_code >= 500 or e.response.status_code == 429)) or \
                   isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
                    
                    # Calculate delay with exponential backoff and jitter
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Gemini API error (attempt {attempt + 1}/{max_retries}): {str(e)}. Retrying in {delay:.2f}s...")
                    time.sleep(delay)
                else:
                    # Non-retryable error, re-raise immediately
                    raise e
    
    def complete(self, messages: List[Dict[str, str]], model: str = "gemini-2.0-flash", temperature: float = 0.2, tools=None) -> str:
        """Generate text completion using Gemini API"""
        try:
            # Convert messages to Gemini format
            contents = []
            for message in messages:
                if message.get("role") == "user":
                    contents.append({
                        "parts": [{"text": message.get("content", "")}]
                    })
                elif message.get("role") == "assistant":
                    contents.append({
                        "parts": [{"text": message.get("content", "")}]
                    })
                elif message.get("role") == "system":
                    # Gemini doesn't support system messages, prepend to user message
                    if contents and contents[-1].get("parts"):
                        contents[-1]["parts"][0]["text"] = f"{message.get('content', '')}\n\n{contents[-1]['parts'][0]['text']}"
            
            # If no contents, create a default user message
            if not contents:
                contents = [{"parts": [{"text": "Hello"}]}]
            
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": 4000,
                    "topP": 0.8,
                    "topK": 40
                }
            }
            
            # Add safety settings for enterprise use
            payload["safetySettings"] = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
            
            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": self.api_key
            }
            
            url = f"{self.base_url}/models/{model}:generateContent"
            
            # Use retry wrapper for the API request
            def make_request():
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                return response
            
            response = self._retry_request(make_request)
            
            result = response.json()
            
            # Extract generated text
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    return candidate["content"]["parts"][0].get("text", "")
            
            # Fallback if response structure is unexpected
            return "Generated response (structure parsing failed)"
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Gemini API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Gemini completion failed: {str(e)}")
    
    def embed(self, texts: List[str], model: str = "embedding-001") -> List[List[float]]:
        """Generate embeddings using Gemini API"""
        try:
            embeddings = []
            
            for text in texts:
                payload = {
                    "content": {
                        "parts": [{"text": text}]
                    }
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "X-goog-api-key": self.api_key
                }
                
                url = f"{self.base_url}/models/{model}:embedContent"
                
                # Use retry wrapper for the API request
                def make_embed_request():
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                    response.raise_for_status()
                    return response
                
                response = self._retry_request(make_embed_request)
                
                result = response.json()
                
                if "embedding" in result and "values" in result["embedding"]:
                    embeddings.append(result["embedding"]["values"])
                else:
                    # Fallback: return zero vector
                    embeddings.append([0.0] * 768)
            
            return embeddings
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Gemini embedding API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Gemini embedding failed: {str(e)}")
    
    def rerank(self, query: str, candidates: List[str], model: str = "gemini-2.0-flash") -> List[int]:
        """Rerank candidates using Gemini API"""
        try:
            # For Gemini, we'll use the completion API to rank candidates
            # This is a simplified approach - in production you might want a dedicated reranking model
            
            prompt = f"""
            Given the query: "{query}"
            
            Rank the following candidates by relevance (most relevant first):
            {chr(10).join([f"{i+1}. {candidate}" for i, candidate in enumerate(candidates)])}
            
            Return only the numbers in order of relevance, separated by commas.
            """
            
            response = self.complete([{"role": "user", "content": prompt}], model=model, temperature=0.1)
            
            # Parse the response to extract ranking
            try:
                # Look for numbers in the response
                import re
                numbers = re.findall(r'\d+', response)
                if numbers:
                    # Convert to 0-based indices
                    ranked_indices = [int(num) - 1 for num in numbers if 0 <= int(num) - 1 < len(candidates)]
                    # Add any missing indices
                    for i in range(len(candidates)):
                        if i not in ranked_indices:
                            ranked_indices.append(i)
                    return ranked_indices[:len(candidates)]
            except:
                pass
            
            # Fallback: return original order
            return list(range(len(candidates)))
            
        except Exception as e:
            # Fallback: return original order
            return list(range(len(candidates)))
