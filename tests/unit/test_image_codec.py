"""Comprehensive tests for image_codec: multi-format support (JFIF, WEBP, BMP, PNG, JPG),
color space normalization, corrupted EXIF tolerance, and strict PNG/JPG export enforcement.
"""
from __future__ import annotations

import io
from pathlib import Path
from PIL import Image

from photoai.storage import image_codec
from photoai.engine.steps import s7_export
from photoai.engine.context import PipelineContext


def test_jfif_format_roundtrip(tmp_path: Path):
    """Test saving and loading JFIF formatted image."""
    img = Image.new("RGB", (64, 64), color=(120, 180, 240))
    jfif_path = tmp_path / "sample.jfif"

    # Save specifically with JFIF format/header
    img.save(jfif_path, format="JPEG")

    # Ingest using load_image
    loaded = image_codec.load_image(jfif_path)
    assert loaded.mode == "RGB"
    assert loaded.size == (64, 64)
    info = image_codec.get_image_info(jfif_path)
    assert info["size"] == (64, 64)


def test_webp_and_bmp_ingestion(tmp_path: Path):
    """Test loading WebP and BMP files."""
    img = Image.new("RGB", (32, 48), color=(200, 50, 80))
    webp_path = tmp_path / "sample.webp"
    bmp_path = tmp_path / "sample.bmp"

    img.save(webp_path, format="WEBP")
    img.save(bmp_path, format="BMP")

    loaded_webp = image_codec.load_image(webp_path)
    loaded_bmp = image_codec.load_image(bmp_path)

    assert loaded_webp.size == (32, 48)
    assert loaded_bmp.size == (32, 48)
    assert loaded_webp.mode == "RGB"
    assert loaded_bmp.mode == "RGB"


def test_rgba_and_cmyk_normalization(tmp_path: Path):
    """Test transparent RGBA and CMYK images are cleanly converted to standard RGB."""
    # RGBA with transparency
    rgba_img = Image.new("RGBA", (16, 16), color=(255, 0, 0, 128))
    rgba_path = tmp_path / "transparent.png"
    rgba_img.save(rgba_path, format="PNG")

    loaded_rgba = image_codec.load_image(rgba_path)
    assert loaded_rgba.mode == "RGB"
    assert loaded_rgba.size == (16, 16)

    # CMYK image
    cmyk_img = Image.new("CMYK", (20, 20), color=(100, 50, 0, 0))
    cmyk_path = tmp_path / "print.jpg"
    cmyk_img.save(cmyk_path, format="JPEG")

    loaded_cmyk = image_codec.load_image(cmyk_path)
    assert loaded_cmyk.mode == "RGB"
    assert loaded_cmyk.size == (20, 20)


def test_strict_export_guarantee_png(tmp_path: Path):
    """Exporting with .png or default must output a valid PNG file."""
    img = Image.new("RGB", (40, 40), color=(50, 150, 250))
    out_path = tmp_path / "exported_photo.png"

    saved = image_codec.save_image(img, out_path, format="PNG")
    assert saved.suffix.lower() == ".png"
    assert saved.is_file()

    with Image.open(saved) as verified:
        assert verified.format == "PNG"


def test_strict_export_guarantee_jpg(tmp_path: Path):
    """Exporting with .jpg or format='JPEG' must output a valid JPEG file."""
    img = Image.new("RGB", (40, 40), color=(50, 150, 250))
    out_path = tmp_path / "exported_photo.jpg"

    saved = image_codec.save_image(img, out_path, format="JPEG")
    assert saved.suffix.lower() in (".jpg", ".jpeg")
    assert saved.is_file()

    with Image.open(saved) as verified:
        assert verified.format == "JPEG"


def test_strict_export_normalizes_invalid_extension(tmp_path: Path):
    """If given an input extension like .jfif or .webp or no extension, save_image enforces PNG or JPG."""
    img = Image.new("RGB", (30, 30), color=(10, 20, 30))

    # Path had .jfif, but output must be PNG or JPG!
    jfif_request = tmp_path / "output.jfif"
    saved_png = image_codec.save_image(img, jfif_request, format="png")
    assert saved_png.suffix.lower() == ".png"
    assert saved_png.is_file()

    # Path had .webp, but user selected jpg
    webp_request = tmp_path / "output.webp"
    saved_jpg = image_codec.save_image(img, webp_request, format="jpg")
    assert saved_jpg.suffix.lower() == ".jpg"
    assert saved_jpg.is_file()


def test_s7_export_step_with_formats(tmp_path: Path):
    """Test s7_export step correctly uses PNG or JPG as configured in context params."""
    ctx = PipelineContext(recipe_id="upscale_4k", image=Image.new("RGB", (20, 20), (100, 100, 100)))
    ctx.params["persist_result"] = True

    # Test default export (PNG)
    s7_export.run(ctx, job_id="job_test_png")
    assert ctx.export_path is not None
    assert ctx.export_path.endswith(".png")
    assert Path(ctx.export_path).is_file()

    # Test JPG export
    ctx_jpg = PipelineContext(recipe_id="upscale_4k", image=Image.new("RGB", (20, 20), (100, 100, 100)))
    ctx_jpg.params["persist_result"] = True
    ctx_jpg.params["export_format"] = "jpg"

    s7_export.run(ctx_jpg, job_id="job_test_jpg")
    assert ctx_jpg.export_path is not None
    assert ctx_jpg.export_path.endswith(".jpg")
    assert Path(ctx_jpg.export_path).is_file()
