"""Groq LLM client for GirishOS."""
import os
import time
from groq import Groq
from config import PipelineConfig
from models import LLMResponse


# Fallback responses when API fails
FALLBACK_RESPONSES = [
    "Interesting question! Let me think about that differently.",
    "My AI circuits are warming up, ask me again!",
    "Even AI needs a moment sometimes. Try again?",
    "Buffering... just kidding! Ask me something else.",
    "Great question! Let me get back to you on that.",
]


class GroqClient:
    """Generates conversational responses with GirishOS personality."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        api_key = config.groq_api_key or os.environ.get("GROQ_API_KEY", "")
        self.client = Groq(api_key=api_key)
        self.history: list[dict] = []
        self._fallback_index = 0
        self._context = self._load_context()

    def _load_context(self) -> str:
        """Load meeting context and agenda files."""
        context_parts = []

        # Load meeting context
        context_file = os.path.join("context", "meeting_context.md")
        if not os.path.exists(context_file):
            context_file = os.path.join("backend", "context", "meeting_context.md")
        if os.path.exists(context_file):
            with open(context_file, "r") as f:
                context_parts.append(f.read())

        # Load agenda
        agenda_file = os.path.join("context", "agenda.md")
        if not os.path.exists(agenda_file):
            agenda_file = os.path.join("backend", "context", "agenda.md")
        if os.path.exists(agenda_file):
            with open(agenda_file, "r") as f:
                context_parts.append(f.read())

        if context_parts:
            print(f"  📋 Loaded {len(context_parts)} context files")
            return "\n\n---\n\n".join(context_parts)
        return ""

    def reload_context(self):
        """Reload context files (call when agenda changes)."""
        self._context = self._load_context()

    async def generate_response(self, question: str, max_tokens: int = None) -> LLMResponse:
        """Generate a response as GirishOS personality."""
        if max_tokens is None:
            max_tokens = self.config.max_response_tokens

        start_time = time.time()

        # Build system prompt with context
        system_prompt = self.config.personality_prompt
        if self._context:
            system_prompt += f"\n\n--- MEETING CONTEXT ---\n{self._context}"

        messages = [
            {"role": "system", "content": system_prompt},
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
            fallback = FALLBACK_RESPONSES[self._fallback_index % len(FALLBACK_RESPONSES)]
            self._fallback_index += 1
            latency_ms = (time.time() - start_time) * 1000
            return LLMResponse(text=fallback, tokens_used=0, latency_ms=latency_ms)
