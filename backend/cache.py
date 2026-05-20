"""Response cache for GirishOS."""
from collections import OrderedDict
from typing import Optional
from models import VideoResult
from config import PipelineConfig
import hashlib


class ResponseCache:
    """LRU cache for pipeline responses."""

    def __init__(self, config: PipelineConfig):
        self.max_size = config.cache_size
        self._cache: OrderedDict[str, VideoResult] = OrderedDict()

    def _make_key(self, question: str) -> str:
        """Normalize question to cache key."""
        normalized = question.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()

    def get(self, question: str) -> Optional[VideoResult]:
        """Get cached response for a question."""
        key = self._make_key(question)
        if key in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def set(self, question: str, result: VideoResult) -> None:
        """Cache a response. Evicts oldest if full."""
        key = self._make_key(question)
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)  # Remove oldest
        self._cache[key] = result

    def clear(self):
        """Clear all cached responses."""
        self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)
