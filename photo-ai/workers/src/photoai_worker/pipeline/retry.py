"""Retry parameter computation (AGENT_SKILLS S1 / design §2.2 step 6)."""
from __future__ import annotations

from .recipe_schema import RetryConfig


def retry_params(
    config: RetryConfig,
    base_strength: float,
    base_seed: int,
    attempt: int,
) -> tuple[float, int]:
    """Return ``(strength, seed)`` for a retry attempt (``attempt`` >= 1).

    Each retry lowers strength by ``strength_step`` (clamped to [0, 1]) and, when
    ``reseed`` is on, advances the seed so the provider explores a new result.
    """
    strength = base_strength + config.strength_step * attempt
    strength = max(0.0, min(1.0, strength))
    seed = base_seed + attempt if config.reseed else base_seed
    return strength, seed


def should_retry(config: RetryConfig, attempt: int) -> bool:
    """Return True while another retry attempt is allowed."""
    return attempt <= config.max
