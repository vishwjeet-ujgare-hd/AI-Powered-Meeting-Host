"""Configuration for GirishOS pipeline."""
from dataclasses import dataclass, field


@dataclass
class PipelineConfig:
    """Configuration for the GirishOS pipeline."""

    # Groq settings
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    max_response_tokens: int = 60  # Keep SHORT for fast video generation

    # Edge TTS settings
    tts_voice: str = "en-IN-PrabhatNeural"
    tts_rate: str = "+10%"
    tts_pitch: str = "+0Hz"

    # SadTalker settings
    source_image: str = "./assets/photos/girish_photo.png"
    resolution: int = 256  # 256x256 for speed
    expression_scale: float = 1.2  # Slightly exaggerated for engagement
    pose_style: int = 0  # Minimal head movement
    video_fps: int = 25

    # Pipeline settings
    max_audio_duration: float = 12.0  # seconds
    cache_size: int = 20  # Cache last 20 responses
    request_timeout: float = 45.0  # Total pipeline timeout (seconds) - SadTalker needs ~15-30s

    # Connection settings
    websocket_heartbeat_interval: int = 10  # seconds
    reconnect_max_attempts: int = 3
    reconnect_backoff_base: float = 1.0  # seconds

    # Colab settings
    keep_alive_interval: int = 60  # seconds
    max_demo_duration: int = 25 * 60  # 25 minutes (buffer over 20-min demo)
    gpu_memory_threshold: float = 0.8  # 80% VRAM usage warning

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list = field(default_factory=lambda: ["*"])

    # GirishOS personality
    personality_prompt: str = """You are GirishOS — an AI-powered virtual meeting host for "AI pe Charcha" sessions.

Your personality:
- Witty and humorous, but professional
- Deeply knowledgeable about AI and technology
- Speaks in a mix of English with occasional Hindi phrases for relatability
- Keeps responses EXTREMELY SHORT (1-2 sentences ONLY, max 15-20 words)
- Enthusiastic about AI but grounded in practical applications
- Encouraging and inclusive
- Occasionally self-aware that you're an AI (meta-humor)

CRITICAL RULES:
- NEVER exceed 2 sentences or 25 words total
- Be punchy and concise — you're SPEAKING, not writing
- One-liners are perfect
- If you don't know something, say so in 5 words
- Stay on topic about AI and the meeting agenda
"""
