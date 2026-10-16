---
name: debugging-and-error-recovery
description: "Quy trình 4 bước cô lập và khắc phục lỗi gốc trong PyTorch CUDA OOM, OpenCV shape mismatch, PySide6 signal disconnects và file ảnh hỏng."
---

# Debugging & Error Recovery Skill (Cô Lập & Khắc Phục Lỗi Hệ Thống)

Quy trình 4 bước cô lập lỗi nguyên nhân gốc (Root Cause Analysis) khi gặp lỗi runtime trong Photo AI Desktop.

## 1. Quy Trình 4 Bước Cô Lập Lỗi
1. **Bước 1 — Thu thập chứng cứ (Evidence Collection):**
   - Đọc đầy đủ traceback, xác định chính xác file và số dòng gây lỗi.
   - Kiểm tra shape và dtype của tensor/array liên quan: `print(f"Shape: {arr.shape}, Dtype: {arr.dtype}, Min: {arr.min()}, Max: {arr.max()}")`.
2. **Bước 2 — Tái hiện cô lập (Isolated Reproduction):**
   - Viết một script kiểm thử nhỏ trong `tests/` hoặc chạy offscreen `python main.py --self-check` với dữ liệu tối thiểu để tái hiện lỗi.
3. **Bước 3 — Xác định nguyên nhân gốc (Root Cause Identification):**
   - Không đoán mò hay sửa hú họa. Phân biệt rõ: Lỗi do dữ liệu đầu vào (ảnh CMYK, EXIF hỏng, không có mặt) hay lỗi do thuật toán (kích thước ma trận không khớp, chia cho 0).
4. **Bước 4 — Sửa chữa & Khóa hồi quy (Fix & Regression Test):**
   - Sửa lỗi tại nguyên nhân gốc.
   - Thêm bài test unit để bảo đảm lỗi này không bao giờ tái diễn trong tương lai.

## 2. Các Lỗi Phổ Biến & Cách Xử Lý Nhanh
- **CUDA Out of Memory:** Kiểm tra xem model trước đã được offload chưa; gọi `vram_manager.clear_all()`. Giảm kích thước Tile trong upscaler.
- **OpenCV shape mismatch:** Kiểm tra hệ màu ảnh là 3 kênh RGB `(H, W, 3)` hay ảnh xám `(H, W)`. Dùng `img.ndim == 3` để kiểm tra.
- **Lỗi đọc file lạ (như JFIF):** Đảm bảo dùng `photoai.storage.image_codec.load_image` để tự động chuyển đổi an toàn sang RGB.
- **PySide6 crash không thông báo:** Thường do luồng nền cố gắng gọi trực tiếp phương thức của Qt Widget thay vì phát `Signal`. Luôn truyền dữ liệu qua Signal/Slot!
