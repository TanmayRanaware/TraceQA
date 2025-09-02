import os
import requests
from typing import List, Dict
from .llm_base import LLMProvider

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

class OllamaProvider(LLMProvider):
	def complete(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.2, tools=None) -> str:
		resp = requests.post(f"{OLLAMA_HOST}/v1/chat/completions", json={
			"model": model,
			"messages": messages,
			"temperature": temperature,
		})
		resp.raise_for_status()
		return resp.json()["choices"][0]["message"]["content"]

	def embed(self, texts: List[str], model: str):
		resp = requests.post(f"{OLLAMA_HOST}/embeddings", json={"model": model, "input": texts})
		resp.raise_for_status()
		data = resp.json()
		return data.get("data", [{}])[0].get("embedding", [])

	def rerank(self, query: str, candidates: List[str], model: str):
		# Placeholder: simple cosine via embeddings; replace with real reranker
		return list(range(len(candidates)))
