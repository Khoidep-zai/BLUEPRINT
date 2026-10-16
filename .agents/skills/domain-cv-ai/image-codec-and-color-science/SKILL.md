---
name: image-codec-and-color-science
description: "Xử lý đa định dạng ảnh (đặc biệt JFIF, WebP, TIFF, PNG, JPG), xoay chuẩn EXIF, chuyển đổi không gian màu sRGB/CMYK, và quy chuẩn ngặt nghèo luôn xuất ảnh PNG hoặc JPG."
---

# Image Codec & Color Science Skill (Xử Lý Định Dạng Ảnh & Màu Sắc)

Áp dụng cho mọi thao tác đọc (Ingest), ghi (Export), xoay chiều (EXIF), chuẩn hóa màu sắc và quản lý định dạng file trong Photo AI Desktop.

## 1. Nguyên Tắc Cốt Lõi (Core Principles)

1. **Hỗ trợ tối đa định dạng đầu vào (Universal Ingest):**
   - Hỗ trợ đầy đủ: `.jfif`, `.jpeg`, `.jpg`, `.png`, `.webp`, `.bmp`, `.tif`, `.tiff`, `.gif`, `.ico`, `.ppm`.
   - **Đặc biệt với `.jfif`:** Xử lý như JPEG có header JFIF APP0 marker, không yêu cầu đổi đuôi file trước khi nạp.
2. **Luôn xuất ảnh PNG hoặc JPG (Strict PNG/JPG Export Guarantee):**
   - Ảnh sau khi chỉnh sửa chỉ được phép xuất ra `.png` (lossless, tối ưu hóa kích thước) hoặc `.jpg` / `.jpeg` (chất lượng cao, `quality=95`, `subsampling=0`).
   - Nếu người dùng nhập tên file có đuôi `.jfif`, `.webp`, hoặc không đuôi, hệ thống **bắt buộc tự động chuẩn hóa** về `.png` hoặc `.jpg`.
3. **Bảo toàn màu sắc trung thực (Color Space Fidelity):**
   - Chuẩn hóa mọi ảnh về hệ màu `RGB` 3-channel 8-bit (`uint8`).
   - Chuyển đổi kênh trong suốt `RGBA`/`LA` thành nền trắng sạch sẽ hoặc trích tách matte riêng biệt.
   - Chuyển đổi an toàn ảnh in ấn `CMYK` về `sRGB` chuẩn mà không bị đảo ngược kênh màu.
4. **Xử lý EXIF Orientation an toàn:**
   - Sử dụng `ImageOps.exif_transpose` bọc trong `try...except` để chống crash khi gặp header EXIF bị hỏng.

## 2. API Chuẩn Trong Hệ Thống (`photoai.storage.image_codec`)

```python
from photoai.storage.image_codec import (
    load_image,
    save_image,
    save_png,
    save_jpg,
    normalize_export_path,
    normalize_orientation,
    get_image_info,
    SUPPORTED_INPUT_EXTENSIONS,
    SUPPORTED_OUTPUT_EXTENSIONS,
)

# 1. Đọc ảnh đa định dạng (JFIF, PNG, WEBP...)
image = load_image("path/to/sample.jfif")  # Trả về PIL.Image mode='RGB'

# 2. Xuất ảnh đảm bảo luôn là PNG hoặc JPG
out_png = save_image(image, "results/photo.jfif")  # Tự động sửa thành photo.png!
out_jpg = save_image(image, "results/photo.jpg", quality=95)  # Lưu JPEG chất lượng cao
```

## 3. Checklist Kiểm Tra Khi Thay Đổi Codec
- [ ] Thử nghiệm với file ảnh `.jfif` thực tế.
- [ ] Thử nghiệm với file ảnh trong suốt `.png` có alpha channel.
- [ ] Thử nghiệm với file in ấn `.jpg` hệ màu CMYK.
- [ ] Kiểm tra đường dẫn xuất: không bao giờ lưu thành `.jfif` hay `.webp`, luôn kết thúc bằng `.png` hoặc `.jpg`.
- [ ] Chạy unit test: `pytest tests/unit/test_image_codec.py`.
