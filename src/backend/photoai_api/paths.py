"""Monorepo path bootstrap.

The API must be importable both from tests (``pyproject.toml`` sets
``pythonpath``) and when run standalone via ``uvicorn photoai_api.main:app``.
Importing this module first guarantees ``photoai_worker`` and the provider
adapters are on ``sys.path`` in every entry point.
"""
from __future__ import annotations

import sys
from pathlib import Path

# .../src/backend/photoai_api/paths.py -> project root is three levels up.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
RECIPES_DIR = PROJECT_ROOT / "recipes"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

for _path in (PROJECT_ROOT, PROJECT_ROOT / "workers" / "src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))
