import os
from typing import List, Dict
from .llm_base import LLMProvider

try:
	from openai import OpenAI
except Exception:
	OpenAI = None

class OpenAIProvider(LLMProvider):
	def __init__(self):
		if OpenAI is None:
			raise RuntimeError("OpenAI SDK not installed")
		self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

	def complete(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.2, tools=None) -> str:
		resp = self.client.chat.completions.create(model=model, messages=messages, temperature=temperature)
		return resp.choices[0].message.content

	def embed(self, texts: List[str], model: str):
		resp = self.client.embeddings.create(model=model, input=texts)
		return [d.embedding for d in resp.data]

	def rerank(self, query: str, candidates: List[str], model: str):
		return list(range(len(candidates)))
