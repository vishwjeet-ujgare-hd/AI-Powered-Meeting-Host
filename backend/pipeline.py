"""Pipeline orchestrator for GirishOS."""
import os
import time
import tempfile
import asyncio
from typing import Optional, Callable

from models import PipelineRequest, VideoResult, FallbackResult, PipelineStage, FallbackLevel, AudioResult
from config import PipelineConfig
from groq_client import GroqClient
from tts_engine import EdgeTTSEngine
from sadtalker_engine import SadTalkerEngine
from cache import ResponseCache


class PipelineOrchestrator:
    """Coordinates the full pipeline: Question → LLM → TTS → SadTalker → Video."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.groq_client = GroqClient(config)
        self.tts_engine = EdgeTTSEngine(config)
        self.sadtalker = SadTalkerEngine(config)
        self.cache = ResponseCache(config)
        self._notify_callback: Optional[Callable] = None
        self._video_serve_dir = tempfile.mkdtemp(prefix="girishos_videos_")

    def set_notify_callback(self, callback: Callable):
        """Set callback for notifying client of pipeline stage."""
        self._notify_callback = callback

    async def _notify(self, question_id: str, stage: str):
        """Notify client of current pipeline stage."""
        if self._notify_callback:
            await self._notify_callback(question_id, stage)

    async def process_question(self, question: str, question_id: str) -> VideoResult:
        """Process a question through the full pipeline."""
        start_time = time.time()

        # Check cache first
        cached = self.cache.get(question)
        if cached:
            cached.question_id = question_id
            cached.generation_time = time.time() - start_time
            return cached

        # Stage 1: LLM
        await self._notify(question_id, "llm")
        llm_response = await self.groq_client.generate_response(question)
        print(f"  📝 LLM ({llm_response.latency_ms:.0f}ms): {llm_response.text[:80]}...")

        # Stage 2: TTS
        await self._notify(question_id, "tts")
        audio_path = os.path.join(self._video_serve_dir, f"{question_id}.mp3")
        duration = await self.tts_engine.save_to_file(llm_response.text, audio_path)
        print(f"  🔊 TTS: {duration:.1f}s audio generated")

        # Stage 3: Animation
        await self._notify(question_id, "animation")
        video_output_dir = os.path.join(self._video_serve_dir, question_id)
        os.makedirs(video_output_dir, exist_ok=True)

        video_result = await self.sadtalker.generate_video(audio_path, video_output_dir)
        print(f"  🎬 Video ({video_result.generation_time:.1f}s): {video_result.video_url}")

        # Build final result
        result = VideoResult(
            video_url=video_result.video_url,
            duration=duration,
            text_response=llm_response.text,
            generation_time=time.time() - start_time,
            question_id=question_id,
        )

        # Cache it
        self.cache.set(question, result)

        return result

    async def process_question_safe(self, question: str, question_id: str) -> VideoResult | FallbackResult:
        """Process with fallback handling. Never throws."""
        try:
            return await asyncio.wait_for(
                self.process_question(question, question_id),
                timeout=self.config.request_timeout
            )
        except asyncio.TimeoutError:
            print(f"  ⏱️ Pipeline timeout for: {question[:50]}")
            return await self._fallback(question, question_id, "timeout")
        except Exception as e:
            print(f"  ❌ Pipeline error: {e}")
            return await self._fallback(question, question_id, str(e))

    async def _fallback(self, question: str, question_id: str, error: str) -> FallbackResult:
        """Generate fallback response."""
        # Try to at least get LLM response
        try:
            llm_response = await self.groq_client.generate_response(question)
            text = llm_response.text
        except Exception:
            text = "Hmm, let me think about that differently... Give me a moment!"

        return FallbackResult(
            level=FallbackLevel.TEXT_ONLY,
            text=text,
            show_text_overlay=True,
        )

    async def health_check(self) -> dict:
        """Check all pipeline components."""
        status = {
            "groq": False,
            "tts": False,
            "sadtalker": False,
            "gpu": False,
        }

        # Check Groq
        try:
            resp = await self.groq_client.generate_response("test", max_tokens=5)
            status["groq"] = bool(resp.text)
        except Exception:
            pass

        # Check TTS
        try:
            result = await self.tts_engine.synthesize("test")
            status["tts"] = bool(result.audio_bytes)
        except Exception:
            pass

        # Check GPU
        try:
            import torch
            status["gpu"] = torch.cuda.is_available()
            status["sadtalker"] = os.path.exists(self.sadtalker.sadtalker_dir)
        except Exception:
            pass

        return status

    async def warm_up(self) -> bool:
        """Pre-load models and warm caches."""
        self.sadtalker.warm_up()
        return True
