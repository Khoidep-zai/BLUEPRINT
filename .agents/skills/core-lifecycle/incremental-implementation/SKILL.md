---
name: incremental-implementation
description: "Thực thi từng lát mỏng (Thin Slice / /build), phát triển tăng dần có kiểm chứng, giữ hệ thống luôn ở trạng thái chạy được (Green State)."
---

# Incremental Implementation Skill (Thực Thi Lát Mỏng Tăng Dần)

Kỹ năng hiện thực hóa code từng bước nhỏ theo chiều dọc (Vertical Slice), giúp hệ thống luôn trong trạng thái ổn định và sẵn sàng chạy thử.

## 1. Phương Pháp Lát Cắt Mỏng Trong Xử Lý Ảnh
Khi xây dựng một tính năng mới (ví dụ: Chỉnh nọng cằm `chin_fix`):
1. **Lát 1 (Classical Logic):** Hiện thực thuật toán TPS và test trên ma trận tọa độ giả lập. Khẳng định thuật toán warp đúng và không làm biến dạng biên ngoài.
2. **Lát 2 (Pipeline Step):** Tích hợp vào `s4_edit.py`, kiểm tra nhận diện landmarks và cắt vùng submental mask.
3. **Lát 3 (QA Evaluation):** Định nghĩa chỉ số `identity_cosine` và `outside_roi_ssim == 1.0` trong evaluator.
4. **Lát 4 (UI Integration):** Gắn vào sidebar `ToolSelector` và hiển thị gợi ý.

## 2. Giữ Hệ Thống Luôn "Green"
- Sau mỗi lát cắt mỏng, chạy ngay `python -m pytest tests/ -q`.
- Không bao giờ chuyển sang task tiếp theo nếu task hiện tại đang gây fail test.
