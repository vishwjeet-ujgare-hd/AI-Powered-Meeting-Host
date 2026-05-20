"""Data models for GirishOS pipeline."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid
import time


class PipelineStage(str, Enum):
    """Stages of the processing pipeline."""
    LLM = "llm"
    TTS = "tts"
    ANIMATION = "animation"
    ENCODING = "encoding"


class MeetingStage(str, Enum):
    """Stages of the demo meeting."""
    INTRO = "intro"
    AGENDA = "agenda"
    GAME = "game"
    QA = "qa"
    CLOSING = "closing"


class FallbackLevel(int, Enum):
    """Fallback degradation levels."""
    LIVE_VIDEO = 1       # Full pipeline working
    AUDIO_ONLY = 2       # SadTalker failed, audio + static image
    TEXT_ONLY = 3        # TTS also failed, text + filler video
    PREGENERATED = 4     # Everything failed, pre-generated clip


@dataclass
class PipelineRequest:
    """A request to process through the pipeline."""
    question_text: str
    question_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    meeting_stage: MeetingStage = MeetingStage.QA
    priority: str = "normal"  # "normal" or "high"


@dataclass
class VideoResult:
    """Result of a successful pipeline execution."""
    video_url: str
    duration: float
    text_response: str
    generation_time: float
    question_id: str = ""


@dataclass
class AudioResult:
    """Result of TTS synthesis."""
    audio_bytes: bytes = b""
    duration_seconds: float = 0.0
    sample_rate: int = 24000
    format: str = "wav"


@dataclass
class LLMResponse:
    """Result of LLM generation."""
    text: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0


@dataclass
class HealthStatus:
    """Health status of all pipeline components."""
    groq_available: bool = False
    tts_available: bool = False
    sadtalker_ready: bool = False
    gpu_memory_free: float = 0.0
    uptime_seconds: float = 0.0


@dataclass
class FallbackResult:
    """Result when pipeline fails and fallback is used."""
    level: FallbackLevel
    text: str = ""
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    use_static_avatar: bool = False
    show_text_overlay: bool = False
