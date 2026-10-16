# PHOTO AI DESKTOP APP — BẢN VẼ HỆ THỐNG & HƯỚNG DẪN CHO AI AGENT (LOCAL GPU EDITION)

> **Mục tiêu cho AI Agent:** Tài liệu này là đặc tả kỹ thuật chuẩn (Single Source of Truth) để xây dựng ứng dụng **Photo AI Desktop App** bằng Python, sử dụng **100% Local GPU (CUDA/MPS)**, giao diện **PySide6 (Qt6)**, không phụ thuộc vào Web Server, Redis hay Cloud API bên ngoài.

---

## 1. Kiến Trúc Tổng Thể & Nguyên Tắc Cốt Lõi

### 1.1 Sơ đồ kiến trúc (Local Desktop MVVM + GPU Pipeline)

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                     DESKTOP UI LAYER (PySide6 / Qt6)                     │
│  ┌────────────┐  ┌──────────────────────┐  ┌──────────┐  ┌────────────┐  │
│  │ ToolGrid   │  │ InteractiveCanvas    │  │ QaPanel  │  │ BeforeAfter│  │
│  │ (10 Tools) │  │ (Mask/Point/Zoom 4K) │  │ (Metrics)│  │ Slider     │  │
│  └─────┬──────┘  └──────────┬───────────┘  └────▲─────┘  └─────▲──────┘  │
└────────┼────────────────────┼───────────────────┼──────────────┼─────────┘
         │ Qt Signal (JobReq) │                   │ Qt Signal    │
         ▼                    ▼                   │ (Progress/QA)│
┌─────────────────────────────────────────────────┴──────────────┴─────────┐
│                APPLICATION CONTROLLER & QTHREAD WORKER                   │
│  ┌───────────────────────┐   ┌────────────────────────────────────────┐  │
│  │ LocalWorkspaceManager │   │ RecipeRunner (7-Stage Hybrid Pipeline) │  │
│  │ - SQLite (Jobs/Audit) │   │ 1.Ingest ─▶ 2.Detect ─▶ 3.ROI/Mask     │  │
│  │ - File Cache (TTL)    │   │ 7.Export ◀─ 6.AutoQA ◀─ 5.Blend ◀─ 4.AI│  │
│  └───────────────────────┘   └────────────────────┬───────────────────┘  │
└───────────────────────────────────────────────────┼──────────────────────┘
                                                    │
         ┌──────────────────────────────────────────┴───────────┐
         ▼                                                      ▼
┌─────────────────────────────────────┐  ┌─────────────────────────────────┐
│     VRAM MODEL MANAGER (GPU)        │  │   CLASSICAL CV ENGINE (CPU/GPU) │
│ - PyTorch FP16 /BF16, CUDA Streams  │  │ - Frequency Separation (Da thật)│
│ - Auto Load / Offload + EmptyCache  │  │ - TPS Geometry Warp (Góc mặt)   │
│ - Models: RealESRGAN, BiSeNet, LaMa,│  │ - Histogram/LAB Color Transfer  │
│   CodeFormer, IC-Light, SDXL-Inpaint│  │ - Studio Shadow & Reflection    │
└─────────────────────────────────────┘  └─────────────────────────────────┘
```

### 1.2 Nguyên tắc bất biến khi Agent viết code
1. **100% Offline & Local GPU:** Mọi tác vụ suy luận chạy trên GPU cục bộ qua PyTorch (`cuda` hoặc `mps`). Không gọi HTTP API ra ngoài.
2. **Bảo toàn ảnh gốc (Original Immutability):** Ảnh gốc khi nạp vào RAM phải khóa quyền ghi (`img.flags.writeable = False`). Mọi kết quả lưu ra thư mục `workspace/results/`.
3. **Quản lý VRAM nghiêm ngặt:** Không bao giờ nạp toàn bộ model cùng lúc. Phải thông qua `VRAMModelManager` để nạp theo nhu cầu (On-demand Loading) và giải phóng VRAM ngay khi qua bước tiếp theo.
4. **Không khóa giao diện (Non-blocking UI):** Toàn bộ `RecipeRunner` bắt buộc chạy trong `QThread` hoặc `QRunnable`. Giao tiếp với UI chỉ dùng `QtCore.Signal`.
5. **Chống ảo giác bằng Hybrid CV + AI:** Luôn dùng thuật toán thị giác máy tính (OpenCV/NumPy) để khóa vùng Mask, tách tần số giữ lỗ chân lông và ghép vùng sửa (ROI Paste-back).
6. **QA Định lượng & Tự động Fallback:** Mọi chức năng đều phải qua bước chấm điểm QA bằng số. Nếu sau 2 lần retry trên GPU vẫn trượt QA (ví dụ làm lệch nhận dạng mặt), tự động trả về kết quả từ nhánh thuật toán Classical CV an toàn.

---

## 2. Cấu Trúc Thư Mục `src` Chuẩn Hóa (Clean & Modular)

```text
photo-ai-desktop/
├─ pyproject.toml                    # Quản lý dependencies (PySide6, torch, opencv, pydantic...)
├─ main.py                           # Điểm khởi chạy ứng dụng Desktop
├─ assets/                           # Icons, QSS stylesheet (Dark theme chuyên nghiệp)
├─ models_weights/                   # Thư mục chứa weights (.pth, .safetensors, .onnx)
├─ recipes/                          # 10 file YAML cấu hình thông số & ngưỡng QA cho 10 chức năng
├─ prompts/                          # 10 file prompt gốc (.vi.md / .en.md)
├─ src/
│  └─ photoai/
│     ├─ config.py                   # Cấu hình đường dẫn, giới hạn VRAM, thiết bị (cuda/cpu)
│     ├─ errors.py                   # Các ngoại lệ chuẩn (NoFaceDetectedError, OwnershipError...)
│     │
│     ├─ ui/                         # TẦNG GIAO DIỆN DESKTOP (PySide6)
│     │  ├─ main_window.py           # Cửa sổ chính (Sidebar 10 công cụ + Canvas + QA Dock)
│     │  ├─ workers_qt.py            # QThread bọc RecipeRunner, phát Signal tiến độ về UI
│     │  ├─ widgets/
│     │  │  ├─ tool_selector.py      # Danh sách 10 chức năng
│     │  │  ├─ interactive_canvas.py # Vẽ Mask, chấm chọn chủ thể, Zoom/Pan 4K
│     │  │  ├─ before_after_view.py  # Thanh trượt so sánh Trước / Sau trực quan
│     │  │  ├─ qa_panel.py           # Hiển thị các chỉ số QA (Identity, SSIM, EAR...)
│     │  │  └─ watermark_dialog.py   # Hộp thoại bắt buộc tick xác nhận quyền sở hữu
│     │
│     ├─ storage/                    # TẦNG DỮ LIỆU CỤC BỘ
│     │  ├─ db.py                    # SQLite (SQLAlchemy): bảng jobs, qa_reports, audit_logs
│     │  ├─ workspace.py             # Quản lý đọc/ghi ảnh tạm, xóa EXIF, dọn rác TTL
│     │  └─ image_codec.py           # Đọc/ghi ảnh 8-bit/16-bit, chuẩn hóa EXIF orientation
│     │
│     ├─ engine/                     # TẦNG ĐIỀU PHỐI PIPELINE & QUẢN LÝ GPU
│     │  ├─ vram_manager.py          # Nạp/giải phóng model trên VRAM (Singleton + LRU)
│     │  ├─ context.py               # PipelineContext chứa ảnh gốc, masks, HF layer, ROIs
│     │  ├─ recipe_schema.py         # Pydantic schema đọc và kiểm tra file recipes/*.yaml
│     │  ├─ runner.py                # Điều phối luồng 7 bước + cơ chế Retry/Fallback
│     │  └─ steps/
│     │     ├─ s1_ingest.py          # Chuẩn hóa hệ màu RGB, lưu kích thước gốc
│     │     ├─ s2_detect.py          # Gọi các detectors theo cấu hình YAML
│     │     ├─ s3_roi_mask.py        # Cắt vùng ROI, tạo mask feather, tách tần số cao
│     │     ├─ s4_edit.py            # Thực thi chuỗi xử lý Hybrid (CV + GPU Models)
│     │     ├─ s5_blend.py           # Ghép ROI, trộn Frequency, Poisson/Feather blend
│     │     ├─ s6_qa.py              # Đo lường chất lượng đầu ra & quyết định Retry
│     │     └─ s7_export.py          # Xuất file thành phẩm & lưu SQLite
│     │
│     ├─ detectors/                  # CÁC MODULE NHẬN DIỆN (Chạy trên GPU)
│     │  ├─ face_analyzer.py         # InsightFace/RetinaFace (BBox, 5/68/468 Landmarks, ArcFace)
│     │  ├─ face_parsing.py          # BiSeNet (Tách 19 vùng mặt: da, mắt, mũi, môi, tóc, râu)
│     │  ├─ eyes_gaze.py             # Tính chỉ số mở mắt EAR & vector hướng nhìn
│     │  ├─ person_depth.py          # YOLOv8-seg + Depth-Anything-V2 (Tách người & chiều sâu)
│     │  ├─ product_matting.py       # BiRefNet / MODNet (Tách nền sản phẩm & sợi tóc siêu nét)
│     │  └─ ocr_damage.py            # PaddleOCR (Watermark/Logo) + Detector vết xước ảnh cũ
│     │
│     ├─ processors/                 # CÁC THUẬT TOÁN XỬ LÝ CHÍNH (CV + AI)
│     │  ├─ cv_ops/                  # Thuật toán Toán học / OpenCV thuần (Không ảo giác)
│     │  │  ├─ frequency_sep.py      # Tách/ghép tần số cao-thấp (Bảo vệ lỗ chân lông)
│     │  │  ├─ geometry_tps.py       # Thin-Plate Spline (Chỉnh góc mặt/nọng cằm tinh tế)
│     │  │  ├─ color_lighting.py     # Gray-World WB, LAB Histogram Match, CLAHE, Film Grain
│     │  │  └─ studio_physics.py     # Dựng bóng đổ tiếp xúc & phản chiếu gương cho sản phẩm
│     │  └─ ai_wrappers/             # Các trình bọc Model PyTorch chạy GPU
│     │     ├─ upscaler_gpu.py       # Real-ESRGAN / SwinIR (Chia Tiled chống tràn VRAM)
│     │     ├─ inpainter_gpu.py      # LaMa (Xóa vật thể/mụn) & SDXL/Flux ControlNet Inpaint
│     │     ├─ face_restorer_gpu.py  # CodeFormer (Khôi phục mặt ảnh cũ với fidelity cao)
│     │     └─ relighter_gpu.py      # IC-Light (Đổi nắng Giờ vàng, Studio, Xóa bóng Flash)
│     │
│     └─ qa/                         # ĐO LƯỜNG CHẤT LƯỢNG TỰ ĐỘNG
│        ├─ metrics.py               # Tính Identity Cosine, SSIM, EAR, Delta-E, Clip Ratio, Texture Variance
│        └─ evaluator.py             # So khớp với ngưỡng trong YAML và tạo QA Report
└─ tests/
   ├─ unit/                          # Test từng thuật toán CV, QA metrics, VRAM manager
   └─ golden/                        # Bộ ảnh test chuẩn cho 10 chức năng
```

---

## 3. Thiết Kế Mã Nguồn Lõi & Các Thuật Toán Trọng Tâm

AI Agent cần hiện thực hóa chính xác các đoạn mã và thuật toán cốt lõi dưới đây trong `src/photoai/`:

### 3.1 Bộ quản lý bộ nhớ GPU (`src/photoai/engine/vram_manager.py`)
Giúp ứng dụng chạy mượt trên cả các GPU tầm trung (8GB - 12GB VRAM) mà không bao giờ bị lỗi `CUDA Out of Memory`:

```python
import gc
import torch
from typing import Callable, Dict, Any

class VRAMModelManager:
    """Quản lý vòng đời Model trên GPU: Tự động nạp FP16 và giải phóng VRAM."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            cls._instance.dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            cls._instance.loaded_models: Dict[str, Any] = {}
            cls._instance.max_active_models = 2
        return cls._instance

    def get_model(self, model_key: str, loader_fn: Callable[[], Any]) -> Any:
        if model_key in self.loaded_models:
            return self.loaded_models[model_key]

        # Nếu vượt số lượng model cho phép trên VRAM, giải phóng model cũ nhất
        if len(self.loaded_models) >= self.max_active_models:
            oldest_key = next(iter(self.loaded_models))
            self.offload_model(oldest_key)

        model = loader_fn()
        if hasattr(model, "to"):
            model = model.to(device=self.device, dtype=self.dtype)
        if hasattr(model, "eval"):
            model.eval()

        self.loaded_models[model_key] = model
        return model

    def offload_model(self, model_key: str) -> None:
        if model_key in self.loaded_models:
            model = self.loaded_models.pop(model_key)
            if hasattr(model, "to"):
                model.to("cpu")
            del model
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def clear_all(self) -> None:
        for key in list(self.loaded_models.keys()):
            self.offload_model(key)
```

### 3.2 Thuật toán 1: Tách & Tái tạo Tần Số Da (`src/photoai/processors/cv_ops/frequency_sep.py`)
Giải quyết triệt để bài toán **"Không da nhựa, giữ nguyên lỗ chân lông và kết cấu gốc"** ở chức năng 1, 2, 8, 9:

```python
import cv2
import numpy as np

class FrequencySeparator:
    @staticmethod
    def decompose(img_rgb: np.ndarray, sigma: float = 3.0) -> tuple[np.ndarray, np.ndarray]:
        """
        Tách ảnh RGB [0..255] thành:
        - low_freq (float32 [0..1]): Chứa sắc độ, màu da và vùng chuyển sáng.
        - high_freq (float32 [-1..1]): Chứa lỗ chân lông, sợi tóc, kết cấu vải.
        """
        img_f = img_rgb.astype(np.float32) / 255.0
        ksize = int(2 * round(3 * sigma) + 1)
        low_freq = cv2.GaussianBlur(img_f, (ksize, ksize), sigma)
        high_freq = img_f - low_freq
        return low_freq, high_freq

    @staticmethod
    def smooth_low_frequency(low_freq: np.ndarray, diameter: int = 9, sigma_color: float = 0.08, sigma_space: float = 9.0) -> np.ndarray:
        """Làm mịn thông minh lớp màu sắc/ánh sáng bằng Bilateral Filter (giữ cạnh khuôn mặt)."""
        return cv2.bilateralFilter(low_freq, diameter, sigma_color, sigma_space)

    @staticmethod
    def recombine(
        edited_img_rgb: np.ndarray,
        original_high_freq: np.ndarray,
        skin_mask: np.ndarray,
        hf_restore_strength: float = 0.85,
        sigma: float = 3.0
    ) -> np.ndarray:
        """
        Lấy phần màu/ánh sáng đã qua xử lý AI/CV cộng với lớp lỗ chân lông gốc (original_high_freq).
        Chỉ áp dụng bên trong vùng skin_mask (float32 [0..1]).
        """
        edited_low, _ = FrequencySeparator.decompose(edited_img_rgb, sigma=sigma)
        restored = np.clip(edited_low + original_high_freq * hf_restore_strength, 0.0, 1.0)
        
        orig_f = edited_img_rgb.astype(np.float32) / 255.0
        mask_3c = np.repeat(skin_mask[:, :, np.newaxis], 3, axis=2)
        blended = orig_f * (1.0 - mask_3c) + restored * mask_3c
        return (blended * 255.0).astype(np.uint8)
```

### 3.3 Thuật toán 2: Biến dạng Lưới TPS Chỉnh Góc Mặt Thấp (`src/photoai/processors/cv_ops/geometry_tps.py`)
Dùng cho chức năng số 3 (**Sửa nọng cằm & góc máy thấp**). Thay vì để AI vẽ lại mặt gây mất nhận dạng, thuật toán dịch chuyển vi mô các điểm Landmark vùng dưới cằm/lỗ mũi khoảng $2\% - 4\%$ theo phương thẳng đứng trong khi khóa cứng mắt, hộp sọ và toàn bộ viền ảnh:

```python
import cv2
import numpy as np

def subtle_perspective_chin_warp(
    img_rgb: np.ndarray,
    landmarks_68: np.ndarray,
    jaw_lift_ratio: float = 0.03,
    nostril_Drop_ratio: float = 0.015
) -> np.ndarray:
    """
    Mô phỏng góc máy ngang tầm mắt bằng Thin-Plate Spline (TPS):
    - Khoá cố định (Anchor): Mắt, chân mày, sống mũi trên, và 8 điểm viền khung ảnh.
    - Tinh chỉnh nhẹ: Nâng nhẹ đỉnh cằm/hàm dưới và hạ nhẹ cánh mũi lộ do góc chụp từ dưới lên.
    """
    h, w = img_rgb.shape[:2]
    face_height = np.linalg.norm(landmarks_68[8] - landmarks_68[27])

    src_pts = []
    dst_pts = []

    # 1. Khóa cứng 8 điểm biên ảnh để hậu cảnh bất biến 100%
    border_pts = [[0,0], [w//2,0], [w-1,0], [0,h//2], [w-1,h//2], [0,h-1], [w//2,h-1], [w-1,h-1]]
    src_pts.extend(border_pts)
    dst_pts.extend(border_pts)

    # 2. Khóa cứng vùng mắt, mày, trán (Landmarks 17..47)
    for idx in range(17, 48):
        pt = landmarks_68[idx].tolist()
        src_pts.append(pt)
        dst_pts.append(pt)

    # 3. Thu gọn nhẹ đường hàm dưới & cằm (Landmarks 5..11)
    center_face = landmarks_68[30]
    for idx in range(5, 12):
        pt = landmarks_68[idx].copy()
        src_pts.append(pt.tolist())
        # Đẩy nhẹ điểm cằm lên trên (giả lập nâng góc máy)
        vec_to_center = center_face - pt
        moved_pt = pt + vec_to_center * jaw_lift_ratio
        dst_pts.append(moved_pt.tolist())

    # 4. Giảm độ lộ lỗ mũi do góc thấp (Landmarks 31..35)
    for idx in range(31, 36):
        pt = landmarks_68[idx].copy()
        src_pts.append(pt.tolist())
        moved_pt = [pt[0], pt[1] + face_height * nostril_Drop_ratio]
        dst_pts.append(moved_pt)

    src_arr = np.array([src_pts], dtype=np.float32)
    dst_arr = np.array([dst_pts], dtype=np.float32)

    tps = cv2.createThinPlateSplineShapeTransformer()
    matches = [cv2.DMatch(i, i, 0) for i in range(len(src_pts))]
    tps.estimateTransformation(dst_arr, src_arr, matches)
    warped = tps.warpImage(img_rgb)
    return warped
```

### 3.4 Thuật toán 3: Tạo Phản Chiếu & Bóng Đổ Studio Vật Lý (`src/photoai/processors/cv_ops/studio_physics.py`)
Dùng cho chức năng số 10 (**Điện thoại thành Studio**). Bảo toàn 100% từng pixel của sản phẩm gốc, tự động dựng mặt bàn phản chiếu và bóng tiếp xúc mềm mại:

```python
import cv2
import numpy as np

def compose_luxury_studio_product(
    orig_rgb: np.ndarray,
    product_alpha: np.ndarray,
    studio_bg_rgb: np.ndarray,
    reflection_opacity: float = 0.22,
    shadow_strength: float = 0.65
) -> np.ndarray:
    """
    Ghép sản phẩm gốc (bất biến 100%) lên nền Studio kèm:
    1. Contact Shadow (Bóng đổ tiếp xúc dưới đáy sản phẩm).
    2. Mirror Surface Reflection (Phản chiếu lật ngược mờ dần theo hàm mũ).
    """
    h, w = orig_rgb.shape[:2]
    alpha_f = (product_alpha.astype(np.float32) / 255.0)[:, :, np.newaxis]

    # Tìm tọa độ đáy thấp nhất của sản phẩm (y_bottom)
    ys, xs = np.where(product_alpha > 128)
    if len(ys) == 0:
        return orig_rgb
    y_bottom = np.max(ys)
    x_min, x_max = np.min(xs), np.max(xs)

    canvas = studio_bg_rgb.astype(np.float32)

    # 1. Tạo phản chiếu bề mặt (Surface Reflection) bên dưới y_bottom
    prod_only = orig_rgb.astype(np.float32) * alpha_f
    flipped_prod = cv2.flip(prod_only, 0)
    flipped_alpha = cv2.flip(alpha_f, 0)

    # Dịch ảnh lật ngược xuống khớp với đáy y_bottom
    shift_y = 2 * y_bottom - h
    M = np.float32([[1, 0, 0], [0, 1, shift_y]])
    refl_rgb = cv2.warpAffine(flipped_prod, M, (w, h))
    refl_mask = cv2.warpAffine(flipped_alpha, M, (w, h))[:, :, np.newaxis]

    # Làm mờ phản chiếu và tạo Gradient giảm dần từ y_bottom xuống đáy ảnh
    refl_rgb = cv2.GaussianBlur(refl_rgb, (15, 15), 4.0)
    grad = np.zeros((h, 1, 1), dtype=np.float32)
    refl_height = max(1, h - y_bottom)
    grad[y_bottom:h, 0, 0] = np.linspace(reflection_opacity, 0.0, refl_height) ** 1.8

    effective_refl_mask = refl_mask * grad
    canvas = canvas * (1.0 - effective_refl_mask) + refl_rgb * effective_refl_mask

    # 2. Tạo bóng đổ tiếp xúc (Contact Shadow) dạng elip mờ ngay tại y_bottom
    shadow_map = np.zeros((h, w), dtype=np.float32)
    center_x = (x_min + x_max) // 2
    axis_x = max(10, int((x_max - x_min) * 0.48))
    axis_y = max(4, int(h * 0.018))
    cv2.ellipse(shadow_map, (center_x, y_bottom), (axis_x, axis_y), 0, 0, 360, shadow_strength, -1)
    shadow_map = cv2.GaussianBlur(shadow_map, (41, 15), 12.0)[:, :, np.newaxis]
    canvas = canvas * (1.0 - shadow_map)

    # 3. Đặt sản phẩm gốc nguyên vẹn 100% lên trên cùng
    final_img = canvas * (1.0 - alpha_f) + orig_rgb.astype(np.float32) * alpha_f
    return np.clip(final_img, 0, 255).astype(np.uint8)
```

---

## 4. Bảng Ánh Xạ Chi Tiết 10 Chức Năng Nghiệp Vụ (Cho AI Agent Lập Trình)

| # | Recipe ID | Detectors (Bước 2) | Mask & ROI (Bước 3) | Luồng Xử Lý Hybrid CV + GPU (Bước 4 & 5) | Chỉ Số QA Bắt Buộc (Bước 6) |
|---|---|---|---|---|---|
| **1** | `upscale_4k` | `RetinaFace` (Lấy embedding mặt gốc) | Toàn ảnh (Chia Tiled $512 \times 512$, overlap $64\text{px}$) | 1. Khử nhiễu nén JPEG nhẹ.<br>2. Chạy **Real-ESRGAN 4x + ControlNet Tile** (`strength=0.15`).<br>3. Khớp Histogram màu `LAB` với ảnh gốc để giữ nguyên 100% cân bằng trắng và hướng sáng. | `identity_cosine >= 0.95`<br>`ssim_downscaled >= 0.92`<br>`clip_ratio_diff < 0.01` |
| **2** | `skin_retouch` | `BiSeNet` (Tách vùng da mặt/cổ; loại trừ mắt, mày, môi, tóc, râu) | Mask da + Phát hiện đốm mụn bằng Black-hat | 1. **LaMa GPU** xóa mụn trên mask đốm mụn.<br>2. **Frequency Separation**: Làm mịn lớp `Low-Freq`, giữ nguyên và ghép lại $85\%$ lớp lỗ chân lông `High-Freq`.<br>3. Upscale 3x bằng Real-ESRGAN. | `identity_cosine >= 0.95`<br>`delta_e_skin <= 1.8`<br>`texture_variance >= 0.7 * orig` (Chống da nhựa) |
| **3** | `chin_fix` | `MediaPipe 468` / `68 Landmarks` + Ước lượng góc `pitch` | Mask vùng dưới cằm (`submental_mask`) + Lưới TPS | 1. Chạy **TPS Geometry Warp** nâng nhẹ đường hàm ($3\%$) và giảm độ lộ lỗ mũi ($1.5\%$), khóa cứng mắt & hậu cảnh.<br>2. Dùng **IC-Light / Inpaint nhẹ** (`strength=0.28`) làm dịu bóng đen dưới cằm.<br>3. Ghép lại lớp lỗ chân lông da cổ. | `identity_cosine >= 0.92`<br>`outside_roi_ssim == 1.0` |
| **4** | `open_eyes` | `RetinaFace` + Đo độ mở mắt `EAR` từng người trong nhóm | Chỉ lọc người có `EAR < 0.20`. Cắt ROI từng cặp mắt + `pad=0.3` | 1. Tính hướng nhìn và màu da trung bình của từng người.<br>2. Chạy **Face Inpaint GPU** mở mắt tự nhiên trên từng ROI độc lập.<br>3. Ghép lại bằng **Poisson Seamless Clone** vào mặt gốc. | `ear_after >= 0.22`<br>`identity_cosine >= 0.88`<br>`outside_mask_ssim >= 0.995` |
| **5** | `remove_watermark` | `PaddleOCR` + `YOLOv8-Logo` + Mask người dùng vẽ thêm | Dilate mask $5\text{px}$, khóa trừ vùng mặt nếu chồng lấn | 1. Bắt buộc kiểm tra `ownership_confirmed == True` & ghi SQLite `audit_logs`.<br>2. Chạy **LaMa Inpainting GPU** tái tạo nền.<br>3. Chỉ ghi đè đúng các pixel nằm trong mask. | `ocr_recheck_chars == 0`<br>`outside_mask_ssim == 1.0` |
| **6** | `remove_bystanders` | `YOLOv8-seg` + `Depth Anything V2` | Giữ chủ thể chính (gần camera nhất / người dùng chạm chọn). Mask người phụ + bóng đổ dưới chân | 1. Mở rộng mask bao phủ bóng đổ của người phụ.<br>2. Chạy **LaMa / SDXL Depth-ControlNet Inpaint** tái tạo kiến trúc/cảnh vật hậu cảnh.<br>3. Khóa cứng 100% pixel chủ thể chính. | `bystander_count_after == 0`<br>`subject_mask_ssim == 1.0` |
| **7** | `restore_old_photo` | Phân tích ảnh đen trắng/màu + Detector vết rách/xước | Mask vết rách (`scratch_mask`) + ROI khuôn mặt | 1. **LaMa** vá vết rách/nếp gấp.<br>2. **CodeFormer** (`w=0.85`) khôi phục nét mặt tự nhiên.<br>3. Nếu ảnh B&W: chạy **DDColor** tô màu lịch sử.<br>4. Upscale lên **4K (cạnh dài 4096px)** + phủ hạt phim mịn (`Film Grain`). | `identity_cosine >= 0.88`<br>`clip_ratio < 0.01`<br>`max_edge == 4096` |
| **8** | `golden_hour` | `BiSeNet` + `MODNet` (Tách sợi tóc) + `Depth Map` | Mask hậu cảnh, chủ thể và viền tóc ngược sáng (`rim_hair_mask`) | 1. Chạy **IC-Light GPU** chiếu nắng ấm chéo từ phía trước.<br>2. Tăng sáng ấm (Subsurface Rim-light) dọc theo các sợi tóc lòa xòa.<br>3. **Frequency Re-injection**: Ghép lại 100% lớp chi tiết `High-Freq` của ảnh gốc để giữ nguyên cấu trúc mặt và hậu cảnh. | `identity_cosine >= 0.95`<br>`structure_ssim >= 0.94`<br>`clip_ratio < 0.01` |
| **9** | `low_light_fix` | `RetinaFace` + Phân tích vùng bóng gắt Flash & vùng ám màu | Mask vùng tối, vùng bóng gắt dưới mũi/cằm, vùng lóa trán | 1. Cân bằng trắng tự động **Gray-World / Retinex** khử ám cam/xanh.<br>2. Nâng sáng vùng tối bằng đường cong cục bộ / **Zero-DCE++**.<br>3. Làm dịu bóng gắt đèn flash quanh mũi/cằm và ghép lại kết cấu da thật. | `delta_e_skin` chuẩn tự nhiên<br>`clip_ratio < 0.01`<br>`identity_cosine >= 0.96` |
| **10** | `product_studio` | `BiRefNet` (Tách sản phẩm siêu nét) + `PaddleOCR` (Khóa chữ/logo) | `product_alpha_matte` (Khóa bất biến toàn bộ bên trong sản phẩm) | 1. Sinh nền Studio sang trọng bằng **IC-Light Background**.<br>2. Chạy thuật toán `compose_luxury_studio_product` tạo bóng tiếp xúc & phản chiếu mặt bàn.<br>3. Đặt nguyên vẹn 100% pixel sản phẩm gốc lên trên (Logo/chữ không đổi 1 pixel). | `product_iou == 1.0`<br>`logo_ocr_similarity == 1.0`<br>`product_pixel_diff == 0.0` |

---

## 5. Lộ Trình Thực Thi Từng Bước Dành Cho AI Agent

Khi AI Agent nhận file này, hãy thực hiện tuần tự 4 Phase sau:

### Phase 1: Khởi tạo Core Engine, SQLite & Quản lý GPU
1. Tạo cấu trúc thư mục theo đúng **Mục 2** và file `pyproject.toml`.
2. Viết `src/photoai/storage/db.py` (SQLite với 3 bảng: `jobs`, `qa_reports`, `audit_logs`) và `workspace.py`.
3. Viết `VRAMModelManager` (`vram_manager.py`), `PipelineContext` (`context.py`), `RecipeSchema` (`recipe_schema.py`) và `RecipeRunner` 7 bước (`runner.py`).
4. Viết bộ `tests/unit/test_engine.py` kiểm tra luồng nạp/xả VRAM và khóa bất biến ảnh gốc.

### Phase 2: Xây dựng Thư viện Thuật toán Classical CV & Bộ đo QA
1. Viết đầy đủ 4 module trong `src/photoai/processors/cv_ops/`:
   - `frequency_sep.py` (Tách/ghép tần số da).
   - `geometry_tps.py` (Biến dạng lưới TPS chỉnh góc mặt).
   - `color_lighting.py` (Cân bằng trắng, Histogram Matching, CLAHE, Film Grain).
   - `studio_physics.py` (Bóng đổ và phản chiếu Studio).
2. Viết `src/photoai/qa/metrics.py` và `evaluator.py` tính toán chính xác: `SSIM`, `ArcFace Cosine`, `EAR`, `CIELAB Delta-E`, `Texture Variance` (Laplacian), `Clip Ratio`.
3. Viết Unit Test kiểm chứng từng thuật toán toán học và hàm chấm điểm QA.

### Phase 3: Tích hợp Detectors, AI Wrappers (PyTorch GPU) & 10 Recipes
1. Hiện thực các Detectors trong `src/photoai/detectors/` và các AI Wrappers trong `src/photoai/processors/ai_wrappers/` (tất cả đều gọi qua `VRAMModelManager`).
2. Tạo đủ 10 file cấu hình `recipes/<id>.yaml` và 10 file prompt trong `prompts/<id>.vi.md` giữ nguyên 100% nội dung đặc tả gốc của người dùng.
3. Kết nối cơ chế **Auto-Retry & Fallback**: nếu `s6_qa.py` báo trượt ngưỡng, `runner.py` tự động giảm `strength` đi `0.1` và chạy lại bước 4; nếu quá 2 lần vẫn trượt thì trả về bản xử lý từ `cv_ops` kèm cảnh báo.

### Phase 4: Xây dựng Giao diện Desktop PySide6 (Qt6)
1. Thiết kế `main_window.py` với giao diện Dark Mode chuyên nghiệp cho chỉnh sửa ảnh.
2. Xây dựng `interactive_canvas.py` hỗ trợ lăn chuột Zoom/Pan ảnh 4K, cọ vẽ Mask (cho xóa watermark/xóa người) và click chọn chủ thể.
3. Xây dựng `before_after_view.py` (thanh gạt so sánh ảnh gốc và ảnh sau xử lý trực tiếp trên vùng nhìn) và `qa_panel.py` hiển thị huy hiệu Xanh/Vàng cho từng chỉ số QA.
4. Tích hợp `QThread` trong `workers_qt.py` để cập nhật thanh tiến trình theo từng bước (`Ingest -> Detect -> Mask -> GPU Edit -> Blend -> QA -> Done`).