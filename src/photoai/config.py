"""Application paths, device selection and VRAM limits (design §2, §1.1).

Everything here is 100% local: no web server, no Redis, no cloud API. Optional
GPU/OpenCV/Qt dependencies are detected here so the rest of the package can
degrade gracefully to pure NumPy/Pillow implementations.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RECIPES_DIR = Path(os.environ.get("PHOTOAI_RECIPES_DIR", PROJECT_ROOT / "recipes"))
PROMPTS_DIR = PROJECT_ROOT / "prompts"
MODELS_DIR = Path(os.environ.get("PHOTOAI_MODELS_DIR", PROJECT_ROOT / "models_weights"))
ASSETS_DIR = PROJECT_ROOT / "assets"

WORKSPACE_ROOT = Path(
    os.environ.get("PHOTOAI_WORKSPACE", Path.home() / ".photo-ai-desktop" / "workspace")
)
WORKSPACE_UPLOADS = WORKSPACE_ROOT / "uploads"
WORKSPACE_RESULTS = WORKSPACE_ROOT / "results"
WORKSPACE_CACHE = WORKSPACE_ROOT / "cache"

DB_PATH = Path(os.environ.get("PHOTOAI_DB_PATH", WORKSPACE_ROOT / "photoai.db"))

# Design §3.1: never keep more than this many models resident on the GPU.
MAX_VRAM_ACTIVE_MODELS = int(os.environ.get("PHOTOAI_MAX_ACTIVE_MODELS", "2"))
CACHE_TTL_HOURS = int(os.environ.get("PHOTOAI_CACHE_TTL_HOURS", "72"))

# Target long edge (px): restore at 4K per design §4; upscale capped to protect VRAM.
RESTORE_MAX_LONG_EDGE = 4096
UPSCALE_MAX_LONG_EDGE = 8192


def _module_available(name: str) -> bool:
    """True when ``name`` can be imported (cheap, does not import it)."""
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):  # pragma: no cover - broken partial installs
        return False


# Optional accelerators / model runtimes. The app runs on CPU without any of them.
HAS_TORCH = _module_available("torch")
HAS_CV2 = _module_available("cv2")
HAS_PYSIDE6 = _module_available("PySide6")


def device() -> str:
    """Return the inference device string used in logs/UI (``cuda``/``mps``/``cpu``)."""
    if not HAS_TORCH:
        return "cpu"
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def ensure_workspace_dirs() -> None:
    for path in (WORKSPACE_UPLOADS, WORKSPACE_RESULTS, WORKSPACE_CACHE):
        path.mkdir(parents=True, exist_ok=True)
