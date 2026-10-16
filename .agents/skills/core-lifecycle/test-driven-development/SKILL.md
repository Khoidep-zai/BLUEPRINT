---
name: test-driven-development
description: "Quy trình kiểm thử hướng phát triển (TDD / /test), chu trình Red-Green-Refactor với Pytest, kiểm thử thuật toán toán học, storage, và kiểm thử offscreen của PySide6."
---

# Test-Driven Development Skill (Phát Triển Hướng Kiểm Thử Với Pytest)

Kỹ năng viết kiểm thử làm bằng chứng xác nhận tính đúng đắn trước khi bàn giao mã nguồn trong Photo AI Desktop.

## 1. Chu Trình Red -> Green -> Refactor
1. **Red:** Viết một bài kiểm tra ngắn trong `tests/unit/` miêu tả hành vi mong muốn (ví dụ: file `.jfif` nạp vào phải có `mode == 'RGB'`, file lưu ra phải kết thúc bằng `.png` hoặc `.jpg`). Chạy test để thấy thất bại.
2. **Green:** Viết lượng code tối thiểu trong `src/photoai/` để bài test vượt qua.
3. **Refactor:** Tối ưu hóa thuật toán, dọn dẹp biến thừa, làm code trong sáng mà test vẫn tiếp tục pass.

## 2. Các Tầng Kiểm Thử Trong Dự Án
- **Unit Tests (`tests/unit/`):**
  - `test_cv_ops.py`: Kiểm thử các phép toán ma trận, lọc tần số, TPS warp.
  - `test_image_codec.py`: Kiểm thử đa định dạng (JFIF, PNG, WEBP...), chuẩn hóa kênh màu, và quy chuẩn ngặt nghèo luôn xuất PNG/JPG.
  - `test_engine.py`: Kiểm thử khóa bất biến ảnh gốc (`flags.writeable == False`) và cơ chế xả VRAM.
  - `test_detectors.py`: Kiểm thử các module nhận diện với fallback heuristic.
  - `test_recipe_schema.py`: Kiểm thử tính hợp lệ của file cấu hình YAML.
- **Integration Tests (`tests/integration/`):**
  - `test_all_recipes.py`: Chạy thật 10 recipes qua đường ống 7 bước và khẳng định đạt ngưỡng QA.
- **UI Offscreen Test:**
  - `python main.py --self-check`: Khởi chạy ứng dụng PySide6 ở chế độ offscreen (`QT_QPA_PLATFORM=offscreen`), kích hoạt event loop và thoát sạch sẽ với mã 0.
