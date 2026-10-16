"""Studio contact shadow + table reflection (design §3.4).

Recipe 10 (*phone -> studio*) must keep the product's own pixels bit-identical
(logo/text unchanged). So the product is composited *on top* of a generated
studio backdrop + reflection + contact shadow, never redrawn.

Pure NumPy + Pillow, so it runs with or without OpenCV.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter


def _gaussian_blur(img: np.ndarray, radius: float) -> np.ndarray:
    mode = "RGB" if img.ndim == 3 else "L"
    if img.ndim == 2:
        pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), mode="L")
    else:
        pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), mode="RGB")
    blurred = pil.filter(ImageFilter.GaussianBlur(radius))
    return np.asarray(blurred, dtype=np.float32)


def _ellipse_mask(shape: tuple[int, int], center: tuple[int, int], axes: tuple[int, int]) -> np.ndarray:
    height, width = shape
    yy, xx = np.mgrid[0:height, 0:width]
    cx, cy = center
    ax, ay = max(1, axes[0]), max(1, axes[1])
    inside = ((xx - cx) / ax) ** 2 + ((yy - cy) / ay) ** 2 <= 1.0
    return inside.astype(np.float32)


def compose_luxury_studio_product(
    orig_rgb: np.ndarray,
    product_alpha: np.ndarray,
    studio_bg_rgb: np.ndarray,
    reflection_opacity: float = 0.22,
    shadow_strength: float = 0.65,
) -> np.ndarray:
    """Composite ``orig_rgb`` (via ``product_alpha``) onto a studio backdrop.

    Adds a contact shadow at the base and a mirrored, exponentially fading
    reflection on the table surface. The product pixels themselves are placed
    last, unchanged.
    """
    h, w = orig_rgb.shape[:2]
    alpha_f = (product_alpha.astype(np.float32) / 255.0)[:, :, np.newaxis]

    ys, xs = np.where(product_alpha > 128)
    if len(ys) == 0:
        return orig_rgb
    y_bottom = int(np.max(ys))
    x_min, x_max = int(np.min(xs)), int(np.max(xs))

    canvas = studio_bg_rgb.astype(np.float32)

    # 1. Surface reflection: the product, flipped vertically about y_bottom.
    prod_only = orig_rgb.astype(np.float32) * alpha_f
    flipped_prod = prod_only[::-1, :, :]
    flipped_alpha = alpha_f[::-1, :, :]

    shift_y = 2 * y_bottom - h
    refl_rgb = np.zeros_like(prod_only)
    refl_mask = np.zeros_like(alpha_f)
    if shift_y >= 0:
        refl_rgb[shift_y:, :, :] = flipped_prod[: h - shift_y, :, :]
        refl_mask[shift_y:, :, :] = flipped_alpha[: h - shift_y, :, :]
    else:
        refl_rgb[:h, :, :] = 0.0

    refl_rgb = _gaussian_blur(refl_rgb, 4.0)
    grad = np.zeros((h, 1, 1), dtype=np.float32)
    refl_height = max(1, h - y_bottom)
    grad[y_bottom:h, 0, 0] = np.linspace(reflection_opacity, 0.0, refl_height) ** 1.8

    effective_refl_mask = refl_mask * grad
    canvas = canvas * (1.0 - effective_refl_mask) + refl_rgb * effective_refl_mask

    # 2. Contact shadow: soft ellipse at the product base.
    shadow_map = np.zeros((h, w), dtype=np.float32)
    center_x = (x_min + x_max) // 2
    axis_x = max(10, int((x_max - x_min) * 0.48))
    axis_y = max(4, int(h * 0.018))
    shadow_map = _ellipse_mask((h, w), (center_x, y_bottom), (axis_x, axis_y)) * shadow_strength
    shadow_map = _gaussian_blur(shadow_map * 255.0, 12.0)[:, :, np.newaxis] / 255.0
    canvas = canvas * (1.0 - shadow_map)

    # 3. Place the untouched original product on top.
    final_img = canvas * (1.0 - alpha_f) + orig_rgb.astype(np.float32) * alpha_f
    return np.clip(final_img, 0, 255).astype(np.uint8)
