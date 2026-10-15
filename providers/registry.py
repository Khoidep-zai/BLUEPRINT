"""Provider registry - selects provider by configuration."""

from __future__ import annotations

from typing import Optional

from providers.base import ImageEditProvider
from providers.mock import MockProvider

_REGISTRY: dict[str, type[ImageEditProvider]] = {
    "mock": MockProvider,
}


def register(name: str, provider_cls: type[ImageEditProvider]) -> None:
    _REGISTRY[name] = provider_cls


def get(name: str = "mock", **kwargs) -> ImageEditProvider:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown provider: {name}. Available: {list(_REGISTRY)}")
    return _REGISTRY[name](**kwargs)
