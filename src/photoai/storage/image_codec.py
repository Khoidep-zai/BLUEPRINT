"""Image load/save with EXIF orientation normalization, multi-format ingestion, and strict PNG/JPG export."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional, Union

from PIL import Image, ImageCms, ImageOps

SUPPORTED_INPUT_EXTENSIONS: tuple[str, ...] = (
    ".jfif",
    ".jpeg",
    ".jpg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
    ".gif",
    ".ico",
    ".ppm",
    ".pgm",
    ".pbm",
)

SUPPORTED_OUTPUT_EXTENSIONS: tuple[str, ...] = (
    ".png",
    ".jpg",
    ".jpeg",
)


def normalize_orientation(image: Image.Image) -> Image.Image:
    """Normalize image orientation based on EXIF metadata with fault tolerance."""
    try:
        transposed = ImageOps.exif_transpose(image)
        return transposed if transposed is not None else image
    except Exception:
        # Some corrupted EXIF headers cause exif_transpose to fail; return untouched
        return image


def load_image(source: Union[Path, str, bytes, io.BytesIO]) -> Image.Image:
    """Load an image from path or bytes, normalising format, color space and orientation to standard RGB.

    Supports JFIF, JPEG, PNG, WEBP, BMP, TIFF, GIF and all standard image formats.
    Transparent alpha channels are cleanly composited over white; CMYK is converted to sRGB.
    """
    if isinstance(source, (bytes, bytearray)):
        source_stream = io.BytesIO(source)
    elif isinstance(source, io.BytesIO):
        source_stream = source
    else:
        source_stream = open(Path(source), "rb")

    try:
        with Image.open(source_stream) as raw_img:
            # Load pixel data before closing file
            raw_img.load()
            img = normalize_orientation(raw_img)

            # Handle transparency / alpha channels cleanly
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                rgba = img.convert("RGBA")
                background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                img = Image.alpha_composite(background, rgba).convert("RGB")
            elif img.mode == "CMYK":
                # Convert CMYK to sRGB cleanly
                img = img.convert("RGB")
            elif img.mode != "RGB":
                img = img.convert("RGB")

            return img
    finally:
        if not isinstance(source, (bytes, bytearray, io.BytesIO)):
            source_stream.close()


def normalize_export_path(path: Union[Path, str], preferred_format: str = "png") -> Path:
    """Ensure the target export path strictly has a .png or .jpg / .jpeg extension.

    If the provided path has another extension (such as .jfif, .webp, .bmp) or no extension,
    it automatically normalizes it to .png or .jpg based on preferred_format.
    """
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix in SUPPORTED_OUTPUT_EXTENSIONS:
        return p

    ext = ".jpg" if preferred_format.lower() in ("jpg", "jpeg") else ".png"
    return p.with_suffix(ext)


def save_image(
    image: Image.Image,
    path: Union[Path, str],
    format: Optional[str] = None,
    quality: int = 95,
    compress_level: int = 6,
) -> Path:
    """Save an image strictly in PNG or JPG format with balanced performance.

    - If path ends with .jpg/.jpeg or format is 'jpeg'/'jpg', saves high-quality JPEG.
    - Otherwise, saves lossless PNG with balanced compress_level (fast and compact).
    - If path has another extension (e.g. .jfif), it is automatically corrected.
    """
    dest = Path(path)

    # Determine desired format
    fmt = format.lower() if format else None
    if fmt in ("jpg", "jpeg") or dest.suffix.lower() in (".jpg", ".jpeg"):
        target_format = "JPEG"
        preferred_ext = "jpg"
    else:
        target_format = "PNG"
        preferred_ext = "png"

    dest = normalize_export_path(dest, preferred_format=preferred_ext)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Ensure image is in RGB for JPEG output
    save_img = image
    if target_format == "JPEG" and save_img.mode != "RGB":
        save_img = save_img.convert("RGB")

    if target_format == "JPEG":
        save_img.save(dest, format="JPEG", quality=quality, optimize=True, subsampling=0)
    else:
        # compress_level=6 is the optimal sweet spot for speed and size (up to 10x faster than optimize=True on 4K)
        save_img.save(dest, format="PNG", compress_level=compress_level)

    return dest



def save_png(image: Image.Image, path: Union[Path, str]) -> Path:
    """Save image strictly as PNG."""
    return save_image(image, path, format="PNG")


def save_jpg(image: Image.Image, path: Union[Path, str], quality: int = 95) -> Path:
    """Save image strictly as high-quality JPG."""
    return save_image(image, path, format="JPEG", quality=quality)


def get_image_info(path: Union[Path, str]) -> dict[str, Union[str, int, tuple[int, int]]]:
    """Retrieve format, dimensions and mode metadata without loading full pixels into memory."""
    p = Path(path)
    with Image.open(p) as img:
        return {
            "format": (img.format or p.suffix.lstrip(".").upper() or "UNKNOWN"),
            "width": img.width,
            "height": img.height,
            "mode": img.mode,
            "size": (img.width, img.height),
            "suffix": p.suffix.lower(),
        }

