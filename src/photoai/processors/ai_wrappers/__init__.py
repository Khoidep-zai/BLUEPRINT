"""PyTorch GPU model wrappers (design §2 processors/ai_wrappers).

Each wrapper loads its model **on demand** through
:class:`photoai.engine.vram_manager.VRAMModelManager` and falls back to a
deterministic classical-CV implementation when PyTorch / the weights are absent,
so the desktop app always runs offline.
"""
from . import face_restorer_gpu, inpainter_gpu, relighter_gpu, upscaler_gpu  # noqa: F401

__all__ = ["upscaler_gpu", "inpainter_gpu", "face_restorer_gpu", "relighter_gpu"]
