"""Response cache for GirishOS."""
from collections import OrderedDict
from typing import Optional
from models import VideoResult
from config import PipelineConfig


class ResponseCache:
    """LRU cache for pipeline responses."""

    def __init__(self, config: PipelineConfig):
        self.max_size = config.cache_size
        self._cache: OrderedDict[str, VideoResult] = OrderedDict()

    def get(self, question: str) -> Optional[VideoResult]:
        """Get cached response for a question."""
        # TODO: Implement in Task 5.1
        return None

    def set(self, question: str, result: VideoResult) -> None:
        """Cache a response."""
        # TODO: Implement in Task 5.1
        pass
