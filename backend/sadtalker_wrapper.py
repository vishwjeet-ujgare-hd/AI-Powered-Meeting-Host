"""Wrapper script that patches numpy before running SadTalker inference.
This script is called as a subprocess to ensure numpy compatibility."""
import sys
import os

# Patch numpy BEFORE any other imports
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
if not hasattr(np, 'str'):
    np.str = np.str_

# Patch torchvision
import types
try:
    import torchvision.transforms.functional as F
    fake_module = types.ModuleType('torchvision.transforms.functional_tensor')
    fake_module.rgb_to_grayscale = F.rgb_to_grayscale
    sys.modules['torchvision.transforms.functional_tensor'] = fake_module
except Exception:
    pass

# Patch warnings
import warnings
warnings.filterwarnings("ignore")

# Now run SadTalker inference
# Add SadTalker to path
sadtalker_dir = os.path.dirname(os.path.abspath(__file__))
if sadtalker_dir not in sys.path:
    sys.path.insert(0, sadtalker_dir)

# Find the actual SadTalker directory
for possible in [
    os.path.join(os.getcwd(), "SadTalker"),
    "/content/drive/MyDrive/GirishOS/AI-Powered-Meeting-Host/SadTalker",
    "/content/AI-Powered-Meeting-Host/SadTalker",
]:
    if os.path.exists(possible):
        os.chdir(possible)
        sys.path.insert(0, possible)
        break

# Import and run inference
if __name__ == "__main__":
    # Get args (skip script name)
    inference_args = sys.argv[1:]
    
    # Modify sys.argv for inference.py
    sys.argv = ["inference.py"] + inference_args
    
    # Run inference
    exec(open("inference.py").read())
