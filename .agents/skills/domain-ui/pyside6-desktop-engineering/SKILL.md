---
name: pyside6-desktop-engineering
description: "Thiết kế và phát triển giao diện ứng dụng Desktop bằng PySide6 (Qt6), QThread worker non-blocking, Qt Signals/Slots, QSS dark theme, phím tắt và xử lý sự kiện kéo thả (Drag & Drop)."
---

# PySide6 Desktop Engineering Skill (Kỹ Thuật Giao Diện Desktop Qt6)

Kỹ năng xây dựng ứng dụng máy tính PySide6 (Qt6) chuẩn kiến trúc MVVM, đảm bảo giao diện đồ họa siêu mượt, không bao giờ bị đơ (Freezing/Not Responding) và thẩm mỹ tối màu chuyên nghiệp.

## 1. Kiến Trúc Không Khóa UI (Non-Blocking Workers)

- Mọi thao tác tính toán nặng (chạy `RecipeRunner`, nạp model GPU, đọc file ảnh 4K) **BẮT BUỘC** nằm trong `QThread` (`src/photoai/ui/workers_qt.py`).
- **Giao tiếp luồng an toàn:** Chỉ dùng `QtCore.Signal` để gửi thông điệp và dữ liệu từ Worker về `MainWindow`.
  - `progress(stage: str, percent: int)`: Cập nhật thanh tiến trình theo 7 bước.
  - `finished_ok(result: PipelineResult)`: Chuyển dữ liệu ảnh kết quả và báo cáo QA.
  - `failed(message: str)`: Báo lỗi có kiểm soát về UI.

```python
class PipelineWorker(QtCore.QThread):
    progress = QtCore.Signal(str, int)
    finished_ok = QtCore.Signal(object)
    failed = QtCore.Signal(str)

    def run(self) -> None:
        try:
            result = run_pipeline(...)
            self.finished_ok.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))
```

## 2. Tiêu Chuẩn Kéo Thả (Drag & Drop) Đa Định Dạng
- Cả cửa sổ chính `MainWindow` và canvas `InteractiveCanvas` đều kích hoạt `setAcceptDrops(True)`.
- Chấp nhận mọi định dạng: `.jfif`, `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tiff`, `.gif`.
- Khi người dùng kéo thả file hợp lệ, tự động kích hoạt `_load_path` và hiển thị ảnh tức thì.

## 3. Quy Chuẩn Xuất Ảnh Trên UI
- Khi bấm "Lưu kết quả" (Ctrl+S), hộp thoại lưu file cung cấp 2 bộ lọc:
  - `Ảnh PNG (*.png)`
  - `Ảnh JPEG (*.jpg *.jpeg)`
- Luôn tự động chuẩn hóa phần mở rộng về `.png` hoặc `.jpg`, ngăn ngừa người dùng vô tình lưu sai định dạng.

## 4. Giao Diện Tối & Kiểu Dáng (QSS Dark Theme)
- Sử dụng bảng màu Dark Mode chuyên dụng cho đồ họa ảnh trong `assets/dark.qss`.
- Quản lý khoảng cách và bán kính bo góc qua `photoai.ui.theme` (`SPACE_XS`, `SPACE_SM`, `RADIUS_CARD`).
- Phím tắt chuẩn hóa:
  - `Ctrl+O`: Mở ảnh.
  - `Ctrl+S`: Lưu kết quả (PNG / JPG).
  - `Ctrl+Return`: Chạy recipe đã chọn.
  - `Ctrl+Shift+M`: Xóa mask cọ vẽ.
  - `[` và `]`: Giảm / tăng cỡ cọ vẽ.
