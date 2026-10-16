---
name: canvas-and-interactive-tools
description: "Phát triển khung vẽ tương tác (Interactive Canvas), QGraphicsView, lăn chuột Zoom/Pan ảnh 4K mượt mà, cọ vẽ mask bán trong suốt, và thanh trượt so sánh Trước/Sau."
---

# Canvas & Interactive Tools Skill (Khung Vẽ Tương Tác & Công Cụ Thao Tác)

Kỹ năng chuyên sâu về khung làm việc đồ họa `InteractiveCanvas` (`QGraphicsView`) và thanh so sánh `BeforeAfterView` trong Photo AI Desktop.

## 1. Khung Vẽ Đồ Họa 4K (`src/photoai/ui/widgets/interactive_canvas.py`)

- **Kế thừa:** `QtWidgets.QGraphicsView` kết hợp `QGraphicsScene`.
- **Cơ chế Phóng to / Thu nhỏ (Smooth Zoom):**
  - Giới hạn hệ số thu phóng an toàn: `MIN_ZOOM = 0.05` đến `MAX_ZOOM = 8.0`.
  - Phóng to/thu nhỏ tập trung ngay tại vị trí trỏ chuột (`ViewportAnchor.AnchorUnderMouse`).
  - Hỗ trợ nút `Vừa khung` (`fit_to_view`) tự động căn chỉnh ảnh nằm trọn trong viewport.
- **Di chuyển ảnh (Pan Mode):**
  - Kéo chuột giữa hoặc giữ chuột trái ở chế độ `Di chuyển` (`MODE_PAN`).
  - Khóa giới hạn không để ảnh bị bay mất khỏi màn hình.

## 2. Hệ Thống Cọ Vẽ Mask Vectorized (`MODE_BRUSH` & `MODE_ERASE`)
- **Lưu trữ mask:** Ảnh xám 8-bit `QImage(Format_Grayscale8)` có kích thước đồng bộ 1:1 với kích thước ảnh gốc.
- **Tạo lớp phủ bán trong suốt (Translucent Overlay):**
  - Biến đổi mảng NumPy từ ảnh xám sang `ARGB32` với màu tím bán trong suốt (`theme.MASK_RGBA`).
  - Vẽ overlay trong sự kiện `drawForeground` để người dùng luôn thấy rõ nét vùng cọ vẽ mà không che khuất hoàn toàn chi tiết ảnh dưới.
- **Tẩy xóa mask:** Chế độ `MODE_ERASE` cho phép xóa bớt các nét vẽ sai với cùng cơ chế cọ vẽ đầu tròn (`RoundCap`).

## 3. Thanh Trượt So Sánh Trước / Sau (`BeforeAfterView`)
- Hiển thị song song ảnh gốc (Before) và ảnh sau xử lý (After).
- Cho phép người dùng kéo con trượt chia đôi màn hình hoặc nhấp chuột để chuyển đổi nhanh giữa 2 trạng thái nhằm đánh giá sự khác biệt chi tiết.
