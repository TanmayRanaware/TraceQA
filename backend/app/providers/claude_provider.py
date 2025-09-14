import os
import json
import requests
import time
import random
from typing import List, Dict, Any
from .llm_base import LLMProvider

class ClaudeProvider(LLMProvider):
    def __init__(self):
        # Get API key from environment variable for security
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
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
                    print(f"Claude API error (attempt {attempt + 1}/{max_retries}): {str(e)}. Retrying in {delay:.2f}s...")
                    time.sleep(delay)
                else:
                    # Non-retryable error, re-raise immediately
                    raise e
    
    def complete(self, messages: List[Dict[str, str]], model: str = "claude-3-5-haiku-20241022", temperature: float = 0.2, tools=None) -> str:
        """Generate text completion using Claude API"""
        try:
            # Convert messages to Claude format
            # Claude expects messages in a specific format with system, user, and assistant roles
            claude_messages = []
            system_message = None
            
            for message in messages:
                role = message.get("role", "")
                content = message.get("content", "")
                
                if role == "system":
                    system_message = content
                elif role == "user":
                    claude_messages.append({"role": "user", "content": content})
                elif role == "assistant":
                    claude_messages.append({"role": "assistant", "content": content})
            
            # If no messages, create a default user message
            if not claude_messages:
                claude_messages = [{"role": "user", "content": "Hello"}]
            
            payload = {
                "model": model,
                "max_tokens": 4000,
                "temperature": temperature,
                "messages": claude_messages
            }
            
            # Add system message if present
            if system_message:
                payload["system"] = system_message
            
            # Add tools if provided
            if tools:
                payload["tools"] = tools
            
            def make_request():
                response = requests.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                return response.json()
            
            result = self._retry_request(make_request)
            
            # Extract the response content
            if "content" in result and len(result["content"]) > 0:
                return result["content"][0]["text"]
            else:
                return "No response generated"
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Claude API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Claude completion failed: {str(e)}")
    
    def embed(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        """Generate embeddings using Claude API (fallback to OpenAI embeddings)"""
        try:
            # Claude doesn't have a native embedding API, so we'll use OpenAI's embedding API
            # This is a common pattern when using Claude for completions but needing embeddings
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY is required for embeddings when using Claude")
            
            openai_headers = {
                "Authorization": f"Bearer {openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "input": texts,
                "model": model
            }
            
            def make_request():
                response = requests.post(
                    "https://api.openai.com/v1/embeddings",
                    headers=openai_headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                return response.json()
            
            result = self._retry_request(make_request)
            
            # Extract embeddings
            embeddings = [item["embedding"] for item in result["data"]]
            return embeddings
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Claude embedding API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Claude embedding failed: {str(e)}")
    
    def generate_text(self, prompt: str, model: str = "claude-3-5-haiku-20241022", temperature: float = 0.2) -> str:
        """Generate text using Claude API (alias for complete method)"""
        messages = [{"role": "user", "content": prompt}]
        return self.complete(messages, model=model, temperature=temperature)
    
    def rerank(self, query: str, candidates: List[str], model: str = "claude-3-5-sonnet-20241022") -> List[int]:
        """Rerank candidates using Claude API"""
        try:
            # For Claude, we'll use the completion API to rank candidates
            # by asking Claude to evaluate and rank them
            ranking_prompt = f"""Please rank the following candidates based on their relevance to the query: "{query}"

Candidates:
{chr(10).join([f"{i+1}. {candidate}" for i, candidate in enumerate(candidates)])}

Please respond with only the ranking numbers in order of relevance (most relevant first), separated by commas. For example: 3,1,2,4"""
            
            messages = [{"role": "user", "content": ranking_prompt}]
            response = self.complete(messages, model=model, temperature=0.1)
            
            # Parse the response to extract ranking
            try:
                # Extract numbers from the response
                import re
                numbers = re.findall(r'\d+', response)
                if len(numbers) >= len(candidates):
                    # Convert to 0-based indices
                    ranking = [int(num) - 1 for num in numbers[:len(candidates)]]
                    return ranking
                else:
                    # Fallback to original order if parsing fails
                    return list(range(len(candidates)))
            except:
                # Fallback to original order if parsing fails
                return list(range(len(candidates)))
                
        except Exception as e:
            # Fallback to original order if reranking fails
            return list(range(len(candidates)))
