"""Retry strength/seed computation (design §1.2 rule 6).

On a QA miss the runner lowers ``strength`` by ``strength_step`` and (optionally)
re-seeds before re-running stage 4, up to ``max`` retries. Exhausting the retries
drops to the Classical CV fallback branch.
"""
from __future__ import annotations

from photoai.engine.recipe_schema import RetryConfig


def retry_params(
    config: RetryConfig,
    base_strength: float,
    base_seed: int,
    attempt: int,
) -> tuple[float, int]:
    """Return ``(strength, seed)`` for zero-based ``attempt``."""
    strength = base_strength + config.strength_step * attempt
    strength = max(0.0, min(1.0, strength))
    seed = base_seed + attempt if config.reseed else base_seed
    return strength, seed


def should_retry(config: RetryConfig, attempt: int) -> bool:
    """True while there are attempts left (``attempt`` is 1-based)."""
    return attempt <= config.max
