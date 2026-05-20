"""Edge TTS engine for GirishOS."""
from models import AudioResult
from config import PipelineConfig


class EdgeTTSEngine:
    """Converts text to natural-sounding speech using Microsoft Edge TTS."""

    def __init__(self, config: PipelineConfig):
        self.config = config

    async def synthesize(self, text: str) -> AudioResult:
        """Convert text to speech audio."""
        # TODO: Implement in Task 3.1
        raise NotImplementedError("TTS engine not yet implemented")
