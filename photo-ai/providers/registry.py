"""Provider registry."""
from typing import Dict, Type
from .base import ImageEditProvider
from .mock import MockProvider


class ProviderRegistry:
    """Registry for providers."""

    def __init__(self):
        self._providers: Dict[str, Type[ImageEditProvider]] = {
            "mock": MockProvider,
        }

    def register(self, name: str, provider_cls: Type[ImageEditProvider]) -> None:
        """Register a provider."""
        self._providers[name] = provider_cls

    def get(self, name: str = "mock") -> ImageEditProvider:
        """Get provider instance."""
        if name not in self._providers:
            name = "mock"
        return self._providers[name]()


registry = ProviderRegistry()
get_provider = registry.get
