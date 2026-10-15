"""Tests for the provider interface and deterministic mock (P0 task 4)."""
import numpy as np
import pytest
from PIL import Image

from providers.base import ImageEditProvider, ProviderError, ProviderCall
from providers.mock import MockProvider
from providers.registry import get_provider


def _gradient_image(size=(32, 32)) -> Image.Image:
    width, height = size
    xs = np.linspace(0, 255, width, dtype=np.uint8)
    ys = np.linspace(0, 255, height, dtype=np.uint8)
    grid = (xs[None, :] // 2 + ys[:, None] // 2).astype(np.uint8)
    rgb = np.stack([grid, np.flipud(grid), grid], axis=-1)
    return Image.fromarray(rgb, mode="RGB")


def _mask(size=(32, 32), box=(8, 8, 16, 16)) -> Image.Image:
    arr = np.zeros((size[1], size[0]), dtype=np.uint8)
    arr[box[1]:box[3], box[0]:box[2]] = 255
    return Image.fromarray(arr, mode="L")


def test_base_is_abstract():
    with pytest.raises(TypeError):
        ImageEditProvider()  # type: ignore[abstract]


def test_mock_returns_same_size_and_mode():
    provider = MockProvider()
    image = _gradient_image()
    result = provider.edit(image, strength=0.5, seed=1)
    assert isinstance(result, Image.Image)
    assert result.size == image.size
    assert result.mode == "RGB"


def test_mock_is_deterministic():
    provider = MockProvider()
    image = _gradient_image()
    first = provider.edit(image, strength=0.5, seed=7)
    second = provider.edit(image, strength=0.5, seed=7)
    assert np.array_equal(np.asarray(first), np.asarray(second))


def test_mock_differs_with_seed():
    provider = MockProvider()
    image = _gradient_image()
    first = provider.edit(image, strength=0.9, seed=1)
    second = provider.edit(image, strength=0.9, seed=2)
    assert not np.array_equal(np.asarray(first), np.asarray(second))


def test_mock_preserves_pixels_outside_mask():
    provider = MockProvider()
    image = _gradient_image()
    mask = _mask()
    result = provider.edit(image, mask=mask, strength=1.0, seed=1)
    original = np.asarray(image)
    modified = np.asarray(result)
    mask_array = np.asarray(mask)
    outside = mask_array == 0
    assert np.array_equal(original[outside], modified[outside])


def test_mock_changes_pixels_inside_mask():
    provider = MockProvider()
    image = _gradient_image()
    mask = _mask()
    result = provider.edit(image, mask=mask, strength=1.0, seed=1)
    inside = np.asarray(mask) > 0
    assert not np.array_equal(np.asarray(image)[inside], np.asarray(result)[inside])


def test_mock_records_call_metadata():
    provider = MockProvider()
    assert provider.call_metadata() == {}
    provider.edit(_gradient_image(), strength=0.4, seed=11)
    meta = provider.call_metadata()
    assert isinstance(meta, dict)
    assert meta["provider"] == "mock"
    assert meta["seed"] == 11
    assert meta["strength"] == 0.4
    assert meta["latency_ms"] >= 0.0
    assert provider.last_call.__class__ is ProviderCall


def test_base_wraps_failures_in_provider_error():
    class BoomProvider(ImageEditProvider):
        name = "boom"
        max_retries = 1

        def _edit(self, image, mask, prompt, strength, seed):
            raise ValueError("kaboom")

    provider = BoomProvider()
    with pytest.raises(ProviderError):
        provider.edit(_gradient_image())


def test_registry_falls_back_to_mock():
    assert isinstance(get_provider("mock"), MockProvider)
    assert isinstance(get_provider("does-not-exist"), MockProvider)
