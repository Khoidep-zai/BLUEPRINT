"""Thin-Plate Spline geometry correction (design §3.3).

Used by recipe 3 (*chin fix / low camera angle*). Instead of letting a diffusion
model redraw the face (which destroys identity), micro-move only the lower-jaw
and nostril landmarks by 2-4%, while pinning the eyes, brow and all four image
borders. Identity is preserved by construction.

Uses ``cv2.createThinPlateSplineShapeTransformer`` when OpenCV is available and
a self-contained NumPy TPS solver otherwise.
"""
from __future__ import annotations

import numpy as np

try:
    import cv2  # type: ignore
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore


def _kernel(r: np.ndarray) -> np.ndarray:
    r = np.maximum(r, 1e-12)
    return r * r * np.log(r)


def _pairwise_distance(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=-1))


def tps_fit(from_pts: np.ndarray, to_pts: np.ndarray) -> np.ndarray:
    """Solve the TPS coefficients mapping ``from_pts`` -> ``to_pts``."""
    n = len(from_pts)
    k = _kernel(_pairwise_distance(from_pts, from_pts))
    p = np.hstack([np.ones((n, 1)), from_pts])
    system = np.zeros((n + 3, n + 3))
    system[:n, :n] = k
    system[:n, n:] = p
    system[n:, :n] = p.T
    rhs = np.vstack([to_pts, np.zeros((3, 2))])
    return np.linalg.solve(system, rhs)


def tps_apply(coeffs: np.ndarray, from_pts: np.ndarray, query: np.ndarray) -> np.ndarray:
    """Evaluate the fitted TPS at ``query`` ``(M, 2)`` points."""
    n = len(from_pts)
    weights = coeffs[:n]
    affine = coeffs[n:]
    r = np.sqrt(((query[:, None, :] - from_pts[None, :, :]) ** 2).sum(axis=-1))
    return _kernel(r) @ weights + affine[0] + query @ affine[1:]


def _bilinear_sample(image: np.ndarray, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """Sample ``image`` at float coordinates ``xs``/``ys`` with border clamping."""
    height, width = image.shape[:2]
    x0 = np.floor(xs).astype(np.int64)
    y0 = np.floor(ys).astype(np.int64)
    x1 = np.clip(x0 + 1, 0, width - 1)
    y1 = np.clip(y0 + 1, 0, height - 1)
    x0 = np.clip(x0, 0, width - 1)
    y0 = np.clip(y0, 0, height - 1)
    wx = (xs - x0)[:, None]
    wy = (ys - y0)[:, None]

    top = image[y0, x0] * (1 - wx) + image[y0, x1] * wx
    bottom = image[y1, x0] * (1 - wx) + image[y1, x1] * wx
    return top * (1 - wy) + bottom * wy


def _numpy_warp(image: np.ndarray, src_pts: np.ndarray, dst_pts: np.ndarray) -> np.ndarray:
    """Warp by mapping every destination pixel back to its source via TPS."""
    height, width = image.shape[:2]
    # TPS fitted on destination control points -> source (inverse mapping).
    coeffs = tps_fit(dst_pts, src_pts)
    out = np.empty_like(image)
    work = image.astype(np.float32)
    chunk = 64
    for y_start in range(0, height, chunk):
        y_end = min(height, y_start + chunk)
        yy, xx = np.mgrid[y_start:y_end, 0:width]
        query = np.stack([xx.ravel(), yy.ravel()], axis=1).astype(np.float64)
        mapped = tps_apply(coeffs, dst_pts, query)
        sampled = _bilinear_sample(work, mapped[:, 0], mapped[:, 1])
        out[y_start:y_end] = np.clip(sampled.reshape(y_end - y_start, width, 3), 0, 255).astype(
            image.dtype
        )
    return out


def subtle_perspective_chin_warp(
    img_rgb: np.ndarray,
    landmarks_68: np.ndarray,
    jaw_lift_ratio: float = 0.03,
    nostril_drop_ratio: float = 0.015,
) -> np.ndarray:
    """Lift the jaw ~3% and drop the nostrils ~1.5%, pinning eyes + borders."""
    landmarks_68 = np.asarray(landmarks_68, dtype=np.float64)
    if landmarks_68.shape[0] < 48:
        return img_rgb

    h, w = img_rgb.shape[:2]
    face_height = float(np.linalg.norm(landmarks_68[8] - landmarks_68[27]))

    src_pts: list[list[float]] = []
    dst_pts: list[list[float]] = []

    # 1. Pin the 8 image-border corners so the background is 100% stable.
    border_pts = [
        [0, 0], [w // 2, 0], [w - 1, 0],
        [0, h // 2], [w - 1, h // 2],
        [0, h - 1], [w // 2, h - 1], [w - 1, h - 1],
    ]
    src_pts.extend(border_pts)
    dst_pts.extend(border_pts)

    # 2. Pin eyes, brows and forehead (landmarks 17..47).
    for idx in range(17, 48):
        pt = landmarks_68[idx].tolist()
        src_pts.append(pt)
        dst_pts.append(pt)

    # 3. Gently lift the lower jaw + chin (landmarks 5..11).
    center_face = landmarks_68[30]
    for idx in range(5, 12):
        pt = landmarks_68[idx].copy()
        src_pts.append(pt.tolist())
        moved = pt + (center_face - pt) * jaw_lift_ratio
        dst_pts.append(moved.tolist())

    # 4. Reduce nostril exposure from a low angle (landmarks 31..35).
    for idx in range(31, 36):
        pt = landmarks_68[idx].copy()
        src_pts.append(pt.tolist())
        dst_pts.append([pt[0], pt[1] + face_height * nostril_drop_ratio])

    src_arr = np.array([src_pts], dtype=np.float32)
    dst_arr = np.array([dst_pts], dtype=np.float32)

    if cv2 is not None:
        tps = cv2.createThinPlateSplineShapeTransformer()
        matches = [cv2.DMatch(i, i, 0) for i in range(len(src_pts))]
        tps.estimateTransformation(dst_arr, src_arr, matches)
        return tps.warpImage(img_rgb)

    return _numpy_warp(img_rgb, np.array(src_pts, dtype=np.float64), np.array(dst_pts, dtype=np.float64))
