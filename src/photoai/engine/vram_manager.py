"""On-demand GPU model loading with LRU offload (design §3.1).

Never loads every model at once: at most ``max_active_models`` stay resident on
the device (FP16 on CUDA/MPS, FP32 on CPU) and the least-recently-added model is
evicted to make room. This is what keeps mid-range 8-12 GB GPUs from hitting
``CUDA Out of Memory``.

When PyTorch is not installed the manager still works as a plain cache, so the
classical CV fallback pipeline runs unchanged on CPU-only machines.
"""
from __future__ import annotations

import gc
from typing import Any, Callable, Dict, Optional

from contextlib import contextmanager

try:
    import torch
except ImportError:  # pragma: no cover - CPU-only installs
    torch = None  # type: ignore[assignment]

# Enable CuDNN auto-tuner for constant-size tiled tensors on CUDA
if torch is not None and torch.cuda.is_available():
    torch.backends.cudnn.benchmark = True


@contextmanager
def inference_scope():
    """High-throughput inference scope with zero autograd tracking overhead."""
    if torch is not None and hasattr(torch, "inference_mode"):
        with torch.inference_mode():
            yield
    elif torch is not None:
        with torch.no_grad():
            yield
    else:
        yield


def optimal_tile_size(vram_mb: Optional[int] = None) -> int:
    """Calculate optimal tile size (384, 512, 1024) balancing throughput vs memory pressure."""
    if torch is not None and torch.cuda.is_available():
        try:
            total_vram_mb = vram_mb or (torch.cuda.get_device_properties(0).total_memory // (1024 * 1024))
            if total_vram_mb >= 15000:
                return 1024
            elif total_vram_mb >= 7000:
                return 512
            else:
                return 384
        except Exception:
            return 512
    return 256  # CPU-friendly tile


def vram_stats() -> dict[str, Any]:
    """Report active VRAM allocation, cached memory and device name."""
    if torch is not None and torch.cuda.is_available():
        return {
            "device": torch.cuda.get_device_name(0),
            "allocated_mb": round(torch.cuda.memory_allocated() / (1024 * 1024), 1),
            "reserved_mb": round(torch.cuda.memory_reserved() / (1024 * 1024), 1),
            "max_allocated_mb": round(torch.cuda.max_memory_allocated() / (1024 * 1024), 1),
        }
    return {"device": "cpu", "allocated_mb": 0.0, "reserved_mb": 0.0}


# --- Pluggable model-loaders -------------------------------------------------
_MODEL_LOADERS: Dict[str, Callable[[], Any]] = {}


def register_model_loader(key: str, loader: Callable[[], Any]) -> None:
    """Register a zero-arg loader that builds the model for ``key``."""
    _MODEL_LOADERS[key] = loader


def available_models() -> list[str]:
    return sorted(_MODEL_LOADERS)


def load_model(key: str) -> Optional[Any]:
    """Load ``key`` through the singleton, or ``None`` when unavailable."""
    from photoai.config import HAS_TORCH

    if not HAS_TORCH or key not in _MODEL_LOADERS:
        return None
    try:
        return VRAMModelManager().get_model(key, _MODEL_LOADERS[key])
    except Exception:  # pragma: no cover - weights missing / corrupt
        return None


class VRAMModelManager:
    """Process-wide singleton owner of GPU model lifetimes."""

    _instance: "Optional[VRAMModelManager]" = None

    def __new__(cls) -> "VRAMModelManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self) -> None:
        if torch is not None and torch.cuda.is_available():
            self.device = torch.device("cuda")
            self.dtype = torch.float16
        elif torch is not None and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = torch.device("mps")
            self.dtype = torch.float32
        else:
            self.device = torch.device("cpu") if torch is not None else None
            self.dtype = torch.float32 if torch is not None else None
        self.loaded_models: Dict[str, Any] = {}
        from photoai.config import MAX_VRAM_ACTIVE_MODELS

        self.max_active_models = MAX_VRAM_ACTIVE_MODELS

    def get_model(self, model_key: str, loader_fn: Callable[[], Any]) -> Any:
        """Return a cached model, loading it via ``loader_fn`` when absent."""
        if model_key in self.loaded_models:
            return self.loaded_models[model_key]

        # Evict oldest models until there is room for the newcomer.
        while len(self.loaded_models) >= self.max_active_models:
            oldest_key = next(iter(self.loaded_models))
            self.offload_model(oldest_key)

        model = loader_fn()
        if torch is not None and self.device is not None:
            if hasattr(model, "to"):
                model = model.to(device=self.device, dtype=self.dtype)
            if hasattr(model, "eval"):
                model.eval()

        self.loaded_models[model_key] = model
        return model

    def offload_model(self, model_key: str) -> None:
        """Move a model to CPU, drop the reference and free the CUDA cache."""
        if model_key not in self.loaded_models:
            return
        model = self.loaded_models.pop(model_key)
        if torch is not None and hasattr(model, "to"):
            model.to("cpu")
        del model
        gc.collect()
        if torch is not None and torch.cuda.is_available():
            torch.cuda.empty_cache()

    def clear_all(self) -> None:
        for key in list(self.loaded_models.keys()):
            self.offload_model(key)

