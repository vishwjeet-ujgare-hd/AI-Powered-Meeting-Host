"""Groq LLM client for GirishOS."""
from models import LLMResponse
from config import PipelineConfig


class GroqClient:
    """Generates conversational responses with GirishOS personality."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.history = []

    async def generate_response(self, question: str, max_tokens: int = 150) -> LLMResponse:
        """Generate a response as GirishOS personality."""
        # TODO: Implement in Task 2.1
        raise NotImplementedError("Groq client not yet implemented")
