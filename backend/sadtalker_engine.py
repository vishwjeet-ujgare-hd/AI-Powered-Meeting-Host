"""SadTalker animation engine for GirishOS."""
import os
import sys
import time
import subprocess
import tempfile
from config import PipelineConfig
from models import VideoResult


class SadTalkerEngine:
    """Generates realistic talking-head video from photo + audio."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.model_loaded = False
        self.sadtalker_dir = self._find_sadtalker_dir()

    def _find_sadtalker_dir(self) -> str:
        """Find SadTalker directory."""
        possible_paths = [
            "./SadTalker",
            "../SadTalker",
            "/content/drive/MyDrive/GirishOS/AI-Powered-Meeting-Host/SadTalker",
            "/content/AI-Powered-Meeting-Host/SadTalker",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        return "./SadTalker"

    async def generate_video(self, audio_path: str, output_dir: str = None) -> VideoResult:
        """Generate talking head video from audio + source image."""
        start_time = time.time()

        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="girishos_")

        source_image = self.config.source_image
        # Try to find the photo
        if not os.path.exists(source_image):
            # Search in assets/photos
            photo_dir = "assets/photos"
            if os.path.exists(photo_dir):
                for f in os.listdir(photo_dir):
                    if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                        source_image = os.path.join(photo_dir, f)
                        break

        if not os.path.exists(source_image):
            raise FileNotFoundError(f"Avatar photo not found: {source_image}")

        # Run SadTalker inference
        cmd = [
            sys.executable, "inference.py",
            "--driven_audio", os.path.abspath(audio_path),
            "--source_image", os.path.abspath(source_image),
            "--result_dir", os.path.abspath(output_dir),
            "--size", str(self.config.resolution),
            "--expression_scale", str(self.config.expression_scale),
            "--pose_style", str(self.config.pose_style),
            "--still",  # Minimal head movement for stability
            "--preprocess", "crop",
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.sadtalker_dir,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
            )

            if result.returncode != 0:
                print(f"⚠️ SadTalker stderr: {result.stderr[-500:]}")
                raise RuntimeError(f"SadTalker failed: {result.stderr[-200:]}")

        except subprocess.TimeoutExpired:
            raise RuntimeError("SadTalker timed out (>30s)")

        # Find the output video
        video_path = self._find_output_video(output_dir)
        if not video_path:
            raise RuntimeError(f"No video output found in {output_dir}")

        generation_time = time.time() - start_time

        return VideoResult(
            video_url=video_path,  # Will be converted to URL by server
            duration=0,  # Will be determined by video file
            text_response="",
            generation_time=generation_time,
        )

    def _find_output_video(self, output_dir: str) -> str:
        """Find the generated video file in output directory."""
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                if f.endswith(".mp4"):
                    return os.path.join(root, f)
        return ""

    def warm_up(self) -> bool:
        """Pre-load models by running a quick test."""
        try:
            import torch
            if torch.cuda.is_available():
                _ = torch.zeros(1).cuda()
                print(f"✅ GPU available: {torch.cuda.get_device_name(0)}")
                self.model_loaded = True
                return True
        except Exception as e:
            print(f"⚠️ GPU warmup failed: {e}")
        return False
