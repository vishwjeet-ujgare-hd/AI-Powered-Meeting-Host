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
            photo_dir = "assets/photos"
            if os.path.exists(photo_dir):
                for f in os.listdir(photo_dir):
                    if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                        source_image = os.path.join(photo_dir, f)
                        break

        if not os.path.exists(source_image):
            raise FileNotFoundError(f"Avatar photo not found: {source_image}")

        # Build a Python command that patches numpy then runs inference
        abs_audio = os.path.abspath(audio_path)
        abs_image = os.path.abspath(source_image)
        abs_output = os.path.abspath(output_dir)

        python_code = f'''
import sys, os, types, warnings
warnings.filterwarnings("ignore")

# Patch numpy
import numpy as np
if not hasattr(np, "float"): np.float = np.float64
if not hasattr(np, "int"): np.int = np.int64
if not hasattr(np, "object"): np.object = object
if not hasattr(np, "bool"): np.bool = np.bool_
if not hasattr(np, "complex"): np.complex = np.complex128

# Patch torchvision
try:
    import torchvision.transforms.functional as F
    fake = types.ModuleType("torchvision.transforms.functional_tensor")
    fake.rgb_to_grayscale = F.rgb_to_grayscale
    sys.modules["torchvision.transforms.functional_tensor"] = fake
except: pass

# Run SadTalker
sys.argv = ["inference.py",
    "--driven_audio", "{abs_audio}",
    "--source_image", "{abs_image}",
    "--result_dir", "{abs_output}",
    "--size", "{self.config.resolution}",
    "--expression_scale", "{self.config.expression_scale}",
    "--pose_style", "{self.config.pose_style}",
    "--still",
    "--preprocess", "crop"
]

os.chdir("{self.sadtalker_dir}")
sys.path.insert(0, "{self.sadtalker_dir}")
exec(open("inference.py").read())
'''

        try:
            result = subprocess.run(
                [sys.executable, "-c", python_code],
                capture_output=True,
                text=True,
                timeout=120,  # 120 seconds for first run (model loading)
            )

            if result.returncode != 0:
                print(f"⚠️ SadTalker stderr: {result.stderr[-500:]}")
                raise RuntimeError(f"SadTalker failed: {result.stderr[-200:]}")

        except subprocess.TimeoutExpired:
            raise RuntimeError("SadTalker timed out (>120s)")

        # Find the output video
        video_path = self._find_output_video(output_dir)
        if not video_path:
            raise RuntimeError(f"No video output found in {output_dir}")

        generation_time = time.time() - start_time

        return VideoResult(
            video_url=video_path,
            duration=0,
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
