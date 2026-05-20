"""Input validation for GirishOS pipeline."""
import re
import time
from typing import Optional


class InputValidator:
    """Validates and sanitizes user input."""

    def __init__(self, rate_limit_seconds: float = 5.0):
        self.rate_limit_seconds = rate_limit_seconds
        self._last_request_time: dict[str, float] = {}
        self._processed_ids: set[str] = set()

    def validate_question(self, text: str, question_id: str, client_id: str = "default") -> Optional[str]:
        """
        Validate a question. Returns error message if invalid, None if valid.
        - Text must be 1-500 chars, not empty/whitespace
        - HTML tags are stripped
        - Rate limit: 1 question per 5 seconds per client
        - Duplicate question IDs rejected
        """
        # Check empty/whitespace
        if not text or not text.strip():
            return "Question cannot be empty"

        # Check length
        if len(text) > 500:
            return "Question too long (max 500 characters)"

        # Check duplicate ID
        if question_id in self._processed_ids:
            return "Duplicate question ID"

        # Check rate limit
        now = time.time()
        last_time = self._last_request_time.get(client_id, 0)
        if now - last_time < self.rate_limit_seconds:
            return f"Rate limited. Wait {self.rate_limit_seconds - (now - last_time):.1f}s"

        return None

    def sanitize(self, text: str) -> str:
        """Strip HTML tags from text."""
        return re.sub(r'<[^>]+>', '', text).strip()

    def mark_processed(self, question_id: str, client_id: str = "default"):
        """Mark a question as processed (for dedup and rate limiting)."""
        self._processed_ids.add(question_id)
        self._last_request_time[client_id] = time.time()
