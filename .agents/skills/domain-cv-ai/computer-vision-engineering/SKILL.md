---
name: computer-vision-engineering
description: "Thuật toán xử lý ảnh cổ điển (Classical CV), OpenCV, NumPy, Tách tần số giữ lỗ chân lông (Frequency Separation), Biến dạng hình học TPS (Geometry Warp), Cân bằng trắng LAB/Retinex, và Dựng vật lý Studio."
---

# Computer Vision Engineering Skill (Kỹ Thuật Thị Giác Máy Tính Cổ Điển)

Kỹ năng chuyên sâu về các thuật toán thị giác máy tính cổ điển bằng OpenCV và NumPy trong Photo AI Desktop, đảm bảo tính tất định, bảo toàn texture da thật và chống hiện tượng AI hallucination.

## 1. Bốn Thuật Toán Cốt Lõi (`src/photoai/processors/cv_ops/`)

### 1.1 Tách Tần Số Da Thật (`frequency_sep.py`)
- **Mục tiêu:** Chống hiện tượng da búp bê nhựa (plastic skin) khi làm mịn hoặc AI inpainting.
- **Nguyên lý:**
  - $I_{\text{low}} = \text{GaussianBlur}(I, \sigma=3.0)$: Chứa sắc độ, màu da và chuyển sáng.
  - $I_{\text{high}} = I - I_{\text{low}}$ (float32 trong dải $[-1, 1]$): Chứa lỗ chân lông, nếp nhăn vi mô, kết cấu sợi tóc.
  - **Recombine:** Ghép lại $85\% - 100\%$ lớp $I_{\text{high}}$ gốc vào ảnh đã xử lý AI/làm mịn, chỉ tác động trong `skin_mask`.

### 1.2 Biến Dạng Lưới Thin-Plate Spline (`geometry_tps.py`)
- **Mục tiêu:** Chỉnh sửa nọng cằm và góc máy chụp từ dưới lên (Low-angle chin fix) mà không thay đổi nhận dạng khuôn mặt.
- **Nguyên lý:**
  - Khóa cứng (Anchor): 8 điểm viền khung ảnh + mắt, chân mày, sống mũi trên (Landmarks 17..47).
  - Tinh chỉnh nhẹ: Nâng nhẹ đường hàm dưới/cằm ($2\% - 4\%$) và hạ nhẹ lỗ mũi ($1.5\%$).
  - Biến dạng tọa độ tất định bằng `cv2.createThinPlateSplineShapeTransformer()`.

### 1.3 Cân Bằng Màu Sắc & Ánh Sáng (`color_lighting.py`)
- **Gray-World / Retinex Auto WB:** Khử ám màu vàng vọt hoặc xanh lạnh trong ảnh thiếu sáng.
- **LAB Histogram Matching:** Khớp phân phối màu của ảnh sau upscale với ảnh gốc để giữ nguyên 100% hướng sáng và nhiệt độ màu ban đầu.
- **Adaptive CLAHE:** Cân bằng độ tương phản vùng tối cục bộ mà không làm cháy sáng vùng highlights.
- **Film Grain Generator:** Thêm hạt phim tự nhiên vào ảnh phục hồi 4K để tăng tính chân thực.

### 1.4 Vật Lý Studio Sản Phẩm (`studio_physics.py`)
- **Bóng tiếp xúc (Contact Shadow):** Dựng hình elip mờ mềm mại ngay đáy sản phẩm theo trục $X$, giảm dần độ mờ theo hàm Gauss.
- **Phản chiếu mặt gương (Surface Reflection):** Lật ngược sản phẩm qua đáy, dịch chuyển khớp tọa độ $Y_{\text{bottom}}$, làm mờ và áp gradient suy giảm theo lũy thừa ($1.8$).

## 2. Tiêu Chuẩn Viết Mã Nguồn CV
- Mọi mảng NumPy đầu vào phải kiểm tra kiểu dữ liệu (`np.uint8` hoặc `np.float32`).
- Không làm thay đổi mảng đầu vào (In-place mutation prohibited); luôn trả về mảng mới được `clip(0, 255).astype(np.uint8)`.
- Không gọi HTTP hay dịch vụ ngoài.
