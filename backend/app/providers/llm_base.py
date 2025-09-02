from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMProvider(ABC):
	@abstractmethod
	def complete(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.2, tools: Any = None) -> str:
		...

	@abstractmethod
	def embed(self, texts: List[str], model: str) -> List[List[float]]:
		...

	@abstractmethod
	def rerank(self, query: str, candidates: List[str], model: str) -> List[int]:
		...
