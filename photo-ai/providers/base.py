"""Base provider interface (AGENT_SKILLS S2).

Every external model SDK must live behind a provider adapter. The core pipeline
only ever talks to :class:`ImageEditProvider`, so the provider can be swapped by
configuration without touching the recipe runner.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Optional

from PIL import Image


@dataclass
class ProviderCall:
    """Metadata captured for one provider invocation."""

    provider: str
    model_version: str
    seed: int
    strength: float
    latency_ms: float
    cost_usd: float


class ProviderError(RuntimeError):
    """Raised when a provider fails after exhausting its retries."""


class ImageEditProvider(ABC):
    """Common interface: ``edit(image, mask?, prompt, strength, seed) -> image``.

    The public :meth:`edit` owns the cross-cutting concerns (timeout budget,
    retry with backoff, latency and cost accounting). Subclasses implement only
    the model call in :meth:`_edit`.
    """

    name: str = "base"
    model_version: str = "0"
    timeout_s: float = 30.0
    max_retries: int = 2
    cost_per_call_usd: float = 0.0

    def __init__(self) -> None:
        self.last_call: Optional[ProviderCall] = None

    def edit(
        self,
        image: Image.Image,
        mask: Optional[Image.Image] = None,
        prompt: str = "",
        strength: float = 0.5,
        seed: int = 42,
    ) -> Image.Image:
        """Run the provider with retry/backoff and record call metadata."""
        started = time.perf_counter()
        attempts = self.max_retries + 1
        last_error: Optional[Exception] = None

        for attempt in range(attempts):
            try:
                result = self._edit(image, mask, prompt, strength, seed)
                latency_ms = (time.perf_counter() - started) * 1000.0
                self.last_call = ProviderCall(
                    provider=self.name,
                    model_version=self.model_version,
                    seed=seed,
                    strength=strength,
                    latency_ms=round(latency_ms, 3),
                    cost_usd=self.cost_per_call_usd,
                )
                return result
            except Exception as error:  # noqa: BLE001 - surfaced as ProviderError
                last_error = error
                if attempt < attempts - 1:
                    # Exponential backoff: 0.05s, 0.1s, ...
                    time.sleep(0.05 * (2 ** attempt))

        raise ProviderError(
            f"provider {self.name!r} failed after {attempts} attempt(s): {last_error}"
        )

    @abstractmethod
    def _edit(
        self,
        image: Image.Image,
        mask: Optional[Image.Image],
        prompt: str,
        strength: float,
        seed: int,
    ) -> Image.Image:
        """Perform the actual model call. Implemented by adapters."""
        raise NotImplementedError

    def call_metadata(self) -> dict:
        """Return the last call metadata as a plain dict (empty if never called)."""
        if self.last_call is None:
            return {}
        return asdict(self.last_call)
