---
name: code-review-and-quality
description: "Rà soát chất lượng mã nguồn theo 5 trục (/review): Tính chính xác, An toàn VRAM/bộ nhớ, Thẩm mỹ & trải nghiệm PySide6, Hiệu năng NumPy/PyTorch, và Tính toàn vẹn kiến trúc."
---

# Code Review & Quality Skill (Rà Soát Chất Lượng Mã Nguồn Theo 5 Trục)

Kỹ năng kiểm tra và phản biện mã nguồn trước khi hợp nhất hoặc bàn giao, đảm bảo sức khỏe dài hạn của codebase Photo AI Desktop.

## 1. Năm Trục Đánh Giá Toàn Diện (5-Axis Review)

### Trục 1: Tính Chính Xác & Bảo Toàn Dữ Liệu (Correctness & Invariants)
- [ ] Ảnh gốc có bị thay đổi trực tiếp không? (`context.original_rgb.flags.writeable == False`).
- [ ] Ảnh sau khi lưu có đúng là `.png` hoặc `.jpg` không? Có bị xuất ra `.jfif` hay định dạng lạ không?
- [ ] Kết quả có vượt qua ngưỡng QA đã định nghĩa trong recipe không?

### Trục 2: An Toàn VRAM & Tài Nguyên Máy (Resource & Memory Safety)
- [ ] Model có đi qua `VRAMModelManager` không?
- [ ] Số lượng model active trên GPU có vượt quá 2 không?
- [ ] Có gọi `empty_cache()` và `gc.collect()` khi offload không?

### Trục 3: Trải Nghiệm Giao Diện Desktop (Desktop UX & PySide6)
- [ ] Tác vụ nặng có bị chặn main thread không? Có bọc trong `QThread` không?
- [ ] Kéo thả ảnh (kể cả JFIF) có mượt mà không?
- [ ] Báo lỗi và thông báo tiến độ có hiển thị rõ trên thanh trạng thái / banner không?

### Trục 4: Hiệu Năng Tính Toán (Performance & Vectorization)
- [ ] Thao tác mảng có dùng vector hóa của NumPy/OpenCV thay vì vòng lặp for lồng nhau không?
- [ ] Kích thước ảnh 4K có được phân chia ô xử lý (Tiled processing) để chống tràn RAM không?

### Trục 5: Tính Toàn Vẹn Kiến Trúc (Architecture & Simplicity)
- [ ] Cấu trúc thư mục có tuân thủ sơ đồ phân chia mô-đun không?
- [ ] Code có rõ ràng, dễ đọc, không lạm dụng trừu tượng hóa thừa thãi không?
