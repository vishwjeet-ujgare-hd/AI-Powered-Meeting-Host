"""Edge TTS engine for GirishOS."""
import edge_tts
import tempfile
import os
import time
import wave
import io
from config import PipelineConfig
from models import AudioResult


class EdgeTTSEngine:
    """Converts text to natural-sounding speech using Microsoft Edge TTS."""

    def __init__(self, config: PipelineConfig):
        self.config = config

    async def synthesize(self, text: str) -> AudioResult:
        """Convert text to speech audio. Returns WAV audio bytes."""
        start_time = time.time()

        # Create temp file for output
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_path = temp_file.name
        temp_file.close()

        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.config.tts_voice,
                rate=self.config.tts_rate,
                pitch=self.config.tts_pitch,
            )
            await communicate.save(temp_path)

            # Read the audio file
            with open(temp_path, "rb") as f:
                audio_bytes = f.read()

            # Estimate duration (rough: ~150 words per minute for this voice)
            word_count = len(text.split())
            estimated_duration = word_count / 2.5  # ~2.5 words per second

            return AudioResult(
                audio_bytes=audio_bytes,
                duration_seconds=min(estimated_duration, self.config.max_audio_duration),
                sample_rate=24000,
                format="mp3"
            )

        except Exception as e:
            print(f"⚠️ Edge TTS error: {e}")
            raise

        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def save_to_file(self, text: str, output_path: str) -> float:
        """Synthesize and save directly to file. Returns duration."""
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.config.tts_voice,
            rate=self.config.tts_rate,
            pitch=self.config.tts_pitch,
        )
        await communicate.save(output_path)

        word_count = len(text.split())
        return word_count / 2.5
