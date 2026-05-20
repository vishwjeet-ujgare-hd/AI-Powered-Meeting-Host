"""SadTalker animation engine for GirishOS - In-process version for speed."""
import os
import sys
import time
import tempfile
import asyncio
from config import PipelineConfig
from models import VideoResult


class SadTalkerEngine:
    """Generates realistic talking-head video from photo + audio.
    
    Runs SadTalker IN-PROCESS (not subprocess) to avoid model reload on every request.
    Models are loaded once at startup and kept in GPU memory.
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.model_loaded = False
        self.sadtalker_dir = self._find_sadtalker_dir()
        self._animate_from_coeff = None
        self._preprocess_model = None
        self._sadtalker_paths = None

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

    def _patch_numpy(self):
        """Patch numpy for compatibility."""
        import numpy as np
        if not hasattr(np, 'float'):
            np.float = np.float64
        if not hasattr(np, 'int'):
            np.int = np.int64
        if not hasattr(np, 'object'):
            np.object = object
        if not hasattr(np, 'bool'):
            np.bool = np.bool_
        if not hasattr(np, 'complex'):
            np.complex = np.complex128

    def _patch_torchvision(self):
        """Patch torchvision for compatibility."""
        import types
        try:
            import torchvision.transforms.functional as F
            fake = types.ModuleType('torchvision.transforms.functional_tensor')
            fake.rgb_to_grayscale = F.rgb_to_grayscale
            sys.modules['torchvision.transforms.functional_tensor'] = fake
        except Exception:
            pass

    def warm_up(self) -> bool:
        """Load SadTalker models into GPU memory. Call once at startup."""
        try:
            import torch
            if not torch.cuda.is_available():
                print("⚠️ No GPU available")
                return False

            print(f"✅ GPU available: {torch.cuda.get_device_name(0)}")

            # Apply patches
            self._patch_numpy()
            self._patch_torchvision()

            # Add SadTalker to path
            if self.sadtalker_dir not in sys.path:
                sys.path.insert(0, self.sadtalker_dir)

            # Import SadTalker components
            from src.utils.preprocess import CropAndExtract
            from src.test_audio2coeff import Audio2Coeff
            from src.facerender.animate import AnimateFromCoeff
            from src.generate_batch import get_data
            from src.generate_facerender_batch import get_facerender_data

            # Setup model paths using SadTalker's own init_path function
            checkpoint_dir = os.path.join(self.sadtalker_dir, 'checkpoints')
            config_dir = os.path.join(self.sadtalker_dir, 'src', 'config')
            
            from src.utils.init_path import init_path
            sadtalker_paths = init_path(
                checkpoint_dir, config_dir,
                self.config.resolution, False, 'crop'
            )

            # Load models
            device = 'cuda'
            
            print("  Loading face preprocessing model...")
            self._preprocess_model = CropAndExtract(sadtalker_paths, device)
            
            print("  Loading audio2coeff model...")
            self._audio2coeff = Audio2Coeff(sadtalker_paths, device)
            
            print("  Loading face renderer...")
            self._animate_from_coeff = AnimateFromCoeff(sadtalker_paths, device)

            self._sadtalker_paths = sadtalker_paths
            self._get_data = get_data
            self._get_facerender_data = get_facerender_data
            self.model_loaded = True
            
            print("✅ SadTalker models loaded into GPU!")
            return True

        except Exception as e:
            print(f"⚠️ SadTalker warm_up failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def generate_video(self, audio_path: str, output_dir: str = None) -> VideoResult:
        """Generate talking head video from audio + source image."""
        if not self.model_loaded:
            raise RuntimeError("SadTalker models not loaded. Call warm_up() first.")

        start_time = time.time()

        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="girishos_")
        os.makedirs(output_dir, exist_ok=True)

        source_image = self.config.source_image
        if not os.path.exists(source_image):
            photo_dir = "assets/photos"
            if os.path.exists(photo_dir):
                for f in os.listdir(photo_dir):
                    if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                        source_image = os.path.join(photo_dir, f)
                        break

        if not os.path.exists(source_image):
            raise FileNotFoundError(f"Avatar photo not found: {source_image}")

        # Run inference in a thread to not block the event loop
        video_path = await asyncio.get_event_loop().run_in_executor(
            None,
            self._run_inference,
            source_image,
            audio_path,
            output_dir
        )

        generation_time = time.time() - start_time

        return VideoResult(
            video_url=video_path,
            duration=0,
            text_response="",
            generation_time=generation_time,
        )

    def _run_inference(self, source_image: str, audio_path: str, output_dir: str) -> str:
        """Run SadTalker inference (blocking, runs in thread)."""
        import torch
        import numpy as np
        from src.utils.preprocess import CropAndExtract
        from src.generate_batch import get_data
        from src.generate_facerender_batch import get_facerender_data

        device = 'cuda'
        
        # Step 1: Preprocess source image (extract 3D face coefficients)
        first_frame_dir = os.path.join(output_dir, 'first_frame')
        os.makedirs(first_frame_dir, exist_ok=True)
        
        first_coeff_path, crop_pic_path, crop_info = self._preprocess_model.generate(
            source_image, first_frame_dir, 'crop',
            source_image_flag=True, pic_size=self.config.resolution
        )

        if first_coeff_path is None:
            raise RuntimeError("Failed to extract face from image. Check photo quality.")

        # Step 2: Audio to coefficients
        batch = get_data(
            first_coeff_path, audio_path, device,
            ref_eyeblink_coeff_path=None, still=True
        )
        coeff_path = self._audio2coeff.generate(
            batch, output_dir, pose_style=self.config.pose_style
        )

        # Step 3: Render video
        data = get_facerender_data(
            coeff_path, crop_pic_path, first_coeff_path, audio_path,
            batch_size=2, input_yaw_list=None, input_pitch_list=None, input_roll_list=None,
            expression_scale=self.config.expression_scale, still_mode=True,
            preprocess='crop'
        )

        result = self._animate_from_coeff.generate(
            data, output_dir,
            source_image, crop_info,
            enhancer=None, background_enhancer=None,
            preprocess='crop', img_size=self.config.resolution
        )

        # Find output video
        video_path = self._find_output_video(output_dir)
        if not video_path:
            raise RuntimeError(f"No video output found in {output_dir}")

        return video_path

    def _find_output_video(self, output_dir: str) -> str:
        """Find the generated video file in output directory."""
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                if f.endswith(".mp4"):
                    return os.path.join(root, f)
        return ""
