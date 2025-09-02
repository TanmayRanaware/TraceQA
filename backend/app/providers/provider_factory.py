import os
from .ollama_provider import OllamaProvider
from .gemini_provider import GeminiProvider
try:
	from .openai_provider import OpenAIProvider
except Exception:
	OpenAIProvider = None


def get_provider(preferred: str | None = None):
	provider = (preferred or os.environ.get("LLM_PROVIDER", "gemini")).lower()
	if provider == "openai" and OpenAIProvider is not None:
		return OpenAIProvider()
	elif provider == "ollama":
		return OllamaProvider()
	elif provider == "gemini":
		return GeminiProvider()
	else:
		# Default to Gemini if available, otherwise fallback to Ollama
		try:
			return GeminiProvider()
		except Exception:
			return OllamaProvider()
