"""Groq LLM client for GirishOS."""
import os
import time
from groq import Groq
from config import PipelineConfig
from models import LLMResponse


# Fallback responses when API fails
FALLBACK_RESPONSES = [
    "Interesting question! Let me process that... Actually, my AI circuits are a bit busy. Ask me again in a moment!",
    "Hmm, that's a great one! My neural networks are doing some heavy lifting right now. Try again?",
    "You know what, even AI needs a coffee break sometimes! Let me get back to you on that.",
    "That question deserves a thoughtful answer, and right now my thoughts are... buffering!",
    "Great question! But my AI brain just did a little hiccup. Ask me something else!",
]


class GroqClient:
    """Generates conversational responses with GirishOS personality."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        api_key = config.groq_api_key or os.environ.get("GROQ_API_KEY", "")
        self.client = Groq(api_key=api_key)
        self.history: list[dict] = []
        self._fallback_index = 0

    async def generate_response(self, question: str, max_tokens: int = 150) -> LLMResponse:
        """Generate a response as GirishOS personality."""
        start_time = time.time()

        messages = [
            {"role": "system", "content": self.config.personality_prompt},
        ]

        # Add conversation history (last 5 exchanges)
        for h in self.history[-10:]:
            messages.append(h)

        messages.append({"role": "user", "content": question})

        try:
            response = self.client.chat.completions.create(
                model=self.config.groq_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
            )

            text = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens if response.usage else 0
            latency_ms = (time.time() - start_time) * 1000

            # Update history
            self.history.append({"role": "user", "content": question})
            self.history.append({"role": "assistant", "content": text})

            # Keep history manageable
            if len(self.history) > 10:
                self.history = self.history[-10:]

            return LLMResponse(text=text, tokens_used=tokens_used, latency_ms=latency_ms)

        except Exception as e:
            print(f"⚠️ Groq API error: {e}")
            # Return fallback
            fallback = FALLBACK_RESPONSES[self._fallback_index % len(FALLBACK_RESPONSES)]
            self._fallback_index += 1
            latency_ms = (time.time() - start_time) * 1000
            return LLMResponse(text=fallback, tokens_used=0, latency_ms=latency_ms)
