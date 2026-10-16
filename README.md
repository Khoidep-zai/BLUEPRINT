# Photo AI Desktop (Local GPU Edition)

Ứng dụng chỉnh sửa và phục hồi ảnh chân dung & sản phẩm chuyên nghiệp bằng trí tuệ nhân tạo, hoạt động **100% Cục bộ & Ngoại tuyến (Local GPU)**, giao diện **PySide6 (Qt6)** hiện đại, không phụ thuộc Web Server, Redis hay bất kỳ Cloud API nào.

---

## 🌟 Điểm Nổi Bật & Nghiệp Vụ Cốt Lõi

- 🔒 **100% Offline & Bảo mật tuyệt đối:** Mọi model AI chạy trực tiếp trên GPU máy bạn (CUDA / Apple Silicon MPS). Dữ liệu ảnh và khuôn mặt không bao giờ rời khỏi thiết bị.
- 🖼️ **Hỗ trợ đa định dạng đầu vào (Đặc biệt `.jfif`):** Mở và kéo thả mượt mà mọi định dạng ảnh: `.jfif`, `.jpeg`, `.jpg`, `.png`, `.webp`, `.bmp`, `.tif`, `.tiff`, `.gif`. Xử lý an toàn EXIF orientation và chuyển đổi chuẩn màu sRGB cho ảnh in ấn `CMYK` hay ảnh trong suốt `RGBA`.
- 💾 **Luôn xuất ảnh PNG hoặc JPG:** Toàn bộ thành phẩm xuất từ Pipeline hoặc lưu qua giao diện đều được đảm bảo **chỉ xuất định dạng `.png` (lossless) hoặc `.jpg` (high quality JPEG)**. Hệ thống tự động chuẩn hóa mọi phần mở rộng khác.
- ⚡ **Quản lý VRAM thông minh (Zero CUDA OOM):** Cơ chế `VRAMModelManager` giới hạn tối đa 2 model active đồng thời trên GPU, tự động offload giải phóng VRAM, hỗ trợ mượt mà cả GPU 8GB–12GB VRAM.
- 🎨 **Chống ảo giác bằng Hybrid CV + AI:** Tách tần số (`Frequency Separation`) giữ nguyên 85%–100% lỗ chân lông da thật, biến dạng lưới Thin-Plate Spline (`TPS`) chỉnh góc mặt tất định, không làm biến đổi nhân dạng.
- 📊 **Kiểm định chất lượng định lượng (AutoQA):** Đo lường số học SSIM, ArcFace Identity Cosine, EAR mở mắt, CIELAB Delta-E màu da trước khi xuất file; tự động thử lại hoặc fallback về nhánh Classical CV an toàn nếu trượt ngưỡng.

---

## 📋 Bản Đồ 10 Chức Năng Chuyên Sâu (10 Core Recipes)

| # | Recipe ID | Chức Năng Nghiệp Vụ | Công Nghệ Hybrid CV + AI | Chỉ Số QA Bắt Buộc |
|:---:|---|---|---|---|
| **1** | `upscale_4k` | **Siêu phân giải 4K chi tiết** | Real-ESRGAN Tiled $512\text{px}$ + Khớp Histogram LAB giữ nguyên màu gốc | `identity_cosine >= 0.95`<br>`ssim >= 0.92`<br>`clip_ratio < 0.01` |
| **2** | `skin_retouch` | **Làm mịn da giữ lỗ chân lông** | BiSeNet tách da mặt/cổ + LaMa xóa mụn + Frequency Separation tiêm lại kết cấu da thật | `identity_cosine >= 0.95`<br>`delta_e_skin <= 1.8`<br>`texture_variance >= 0.70` |
| **3** | `chin_fix` | **Chỉnh nọng cằm & góc chụp thấp** | TPS Geometry Warp nâng nhẹ hàm $3\%$, giảm lộ lỗ mũi $1.5\%$, IC-Light dịu bóng | `identity_cosine >= 0.92`<br>`outside_roi_ssim == 1.0` |
| **4** | `open_eyes` | **Mở mắt tự nhiên ảnh nhóm** | RetinaFace đo độ mở mắt $EAR < 0.20$ + Inpaint mắt tự nhiên + Poisson Seamless Blend | `ear_after >= 0.22`<br>`identity_cosine >= 0.88` |
| **5** | `remove_watermark` | **Xóa watermark & logo bản quyền** | PaddleOCR + Cọ vẽ Mask + Xác nhận quyền sở hữu (Audit Logs) + LaMa Inpaint | `ocr_chars == 0`<br>`outside_mask_ssim == 1.0` |
| **6** | `remove_bystanders` | **Xóa người lạ qua đường** | YOLOv8-seg + Depth-Anything V2 tách người phụ & bóng đổ, bảo vệ 100% chủ thể | `bystander_count == 0`<br>`subject_mask_ssim == 1.0` |
| **7** | `restore_old_photo` | **Phục hồi ảnh cũ & rách nát** | LaMa vá vết rách + CodeFormer nét mặt + DDColor tô màu + Hạt phim mịn 4K | `identity_cosine >= 0.88`<br>`long_edge == 4096` |
| **8** | `golden_hour` | **Đổi ánh sáng Giờ Vàng** | BiSeNet + MODNet tách sợi tóc + IC-Light chiếu nắng ấm + Tăng sáng viền Rim-light | `identity_cosine >= 0.95`<br>`structure_ssim >= 0.94` |
| **9** | `low_light_fix` | **Cứu ảnh tối & khử bóng Flash** | Gray-World / Retinex cân bằng trắng khử ám vàng + Nâng sáng chi tiết bóng cằm/mũi | `identity_cosine >= 0.96`<br>`delta_e_skin` tự nhiên |
| **10** | `product_studio` | **Sản phẩm điện thoại thành Studio** | BiRefNet tách nền siêu nét + Dựng bóng đổ tiếp xúc và phản chiếu mặt bàn sang trọng | `product_iou == 1.0`<br>`product_pixel_diff == 0.0` |

---

## 🏗️ Kiến Trúc Hệ Thống & Đường Ống 7 Bước (7-Stage Pipeline)

```
┌────────────────────────────────────────────────────────────────────────┐
│                    TẦNG GIAO DIỆN (PySide6 / Qt6)                      │
│   ToolSelector   │  InteractiveCanvas  │  BeforeAfterView  │  QaPanel  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Qt Signals (Non-blocking QThread)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     ĐIỀU PHỐI PIPELINE 7 BƯỚC                          │
│                                                                        │
│ 1. Ingest  ──▶ 2. Detect ──▶ 3. ROI/Mask ──▶ 4. GPU Edit              │
│ (Khóa gốc)    (Retina/YOLO)   (Feather/Sep)   (Hybrid CV+AI)          │
│                                                     │                  │
│ 7. Export ◀─── 6. AutoQA ◀─── 5. Blend ◀────────────┘                  │
│ (PNG / JPG)    (Đo SSIM/ID)   (Poisson/Recomb)                         │
└───────────────────┬───────────────────────────────┬────────────────────┘
                    ▼                               ▼
     ┌─────────────────────────────┐ ┌─────────────────────────────────┐
     │   VRAM MODEL MANAGER (GPU)  │ │   CLASSICAL CV ENGINE (OpenCV)  │
     │ - PyTorch FP16 / MPS / CUDA │ │ - Frequency Separation          │
     │ - Max 2 Active Models (LRU) │ │ - Thin-Plate Spline Warp (TPS)  │
     │ - Tiled 512px Inference     │ │ - LAB Histogram Matching        │
     │ - RealESRGAN, LaMa, BiSeNet │ │ - Studio Contact Shadow/Mirror  │
     └─────────────────────────────┘ └─────────────────────────────────┘
```

---

## 📁 Cấu Trúc Thư Mục Codespace

Codespace được chuẩn hóa mô-đun, dễ đọc, dễ bảo trì:

```
Blueprint/
├── main.py                     # Khởi chạy Desktop App (hoặc --self-check)
├── pyproject.toml              # Cấu hình dự án và dependencies
├── requirements.txt            # Thư viện runtime (PySide6, Pillow, NumPy...)
├── requirements-dev.txt        # Thư viện kiểm thử (pytest, pytest-asyncio...)
├── PHOTO_AI_SYSTEM_DESIGN.md   # Đặc tả kỹ thuật chi tiết toàn diện
├── PROGRESS.md                 # Nhật ký tiến độ và kết quả hiệu chuẩn
├── AGENT.md                    # Bản đồ điều hướng kỹ năng cho AI Coding Agents
│
├── assets/                     # Tài nguyên đồ họa, icon SVG, Dark theme (dark.qss)
├── recipes/                    # 10 file YAML cấu hình tham số & ngưỡng QA
├── prompts/                    # 10 file prompt đặc tả nghiệp vụ (.vi.md / .en.md)
├── models_weights/             # Thư mục lưu trọng số model ngoại tuyến (.pth, .onnx)
│
├── src/photoai/                # Mã nguồn chính của ứng dụng
│   ├── config.py               # Thiết bị (cuda/mps/cpu), VRAM budget, đường dẫn
│   ├── errors.py               # Định nghĩa ngoại lệ (PipelineError, OwnershipError...)
│   │
│   ├── storage/                # Tầng lưu trữ và I/O ảnh
│   │   ├── image_codec.py      # Nạp đa định dạng (JFIF, WEBP...), xuất nghiêm ngặt PNG/JPG
│   │   ├── workspace.py        # Quản lý file tạm, dọn dẹp theo thời gian sống (TTL)
│   │   └── db.py               # SQLite quản lý lịch sử jobs, qa_reports, audit_logs
│   │
│   ├── engine/                 # Tầng điều phối luồng xử lý
│   │   ├── vram_manager.py     # Quản lý bộ nhớ VRAM, tự động nạp/offload model
│   │   ├── context.py          # PipelineContext lưu trữ ảnh gốc, mask, metadata
│   │   ├── runner.py           # Bộ thực thi 7 bước, cơ chế Retry & Classical Fallback
│   │   ├── loader.py           # Bộ nạp danh sách 10 recipes từ YAML
│   │   ├── recipe_schema.py    # Schema Pydantic kiểm tra tính hợp lệ của recipe
│   │   └── steps/              # Triển khai 7 bước: s1_ingest đến s7_export
│   │
│   ├── processors/             # Các thuật toán xử lý hình ảnh
│   │   ├── cv_ops/             # OpenCV/NumPy thuần: frequency_sep, geometry_tps, color...
│   │   └── ai_wrappers/        # Trình bọc deep learning: upscaler, inpainter, restorer...
│   │
│   ├── detectors/              # Bộ nhận diện: face_analyzer, bisenet, ocr, matting...
│   ├── qa/                     # Đo lường chất lượng: metrics (SSIM, Identity) & evaluator
│   │
│   └── ui/                     # Tầng giao diện PySide6 (Qt6)
│       ├── main_window.py      # Cửa sổ chính, toolbar, menu, thanh trạng thái
│       ├── workers_qt.py       # QThread chạy ngầm không giật lag giao diện
│       ├── theme.py            # Bảng màu, typography, khoảng cách thiết kế
│       └── widgets/            # 5 widget: interactive_canvas, before_after, qa_panel...
│
├── tests/                      # Bộ kiểm thử tự động
│   ├── unit/                   # Test cv_ops, image_codec, engine, detectors, storage
│   └── integration/            # Test toàn bộ 10 recipes qua pipeline thật
│
└── .agents/                    # Hệ thống kỹ năng & quy chuẩn Agent (Chuẩn Addy Osmani & VoltAgent)
    ├── rules/                  # Bất biến hệ thống (photoai-invariants, photoai-sdlc-workflow)
    └── skills/                 # Kỹ năng nghiệp vụ: domain-cv-ai, domain-ui, domain-qa...
```

---

## 🚀 Hướng Dẫn Cài Đặt & Sử Dụng

### 1. Yêu Cầu Môi Trường
- **Hệ điều hành:** Windows 10/11, macOS (Apple Silicon M1/M2/M3), hoặc Linux Ubuntu 22.04+.
- **Python:** Phiên bản 3.10 trở lên (khuyến nghị 3.11 hoặc 3.12/3.14).
- **GPU (Tùy chọn tăng tốc):** NVIDIA GPU với CUDA 11.8/12.1+ hoặc Apple Silicon MPS (nếu không có GPU, app tự động chạy mượt mà trên CPU bằng Classical CV).

### 2. Cài Đặt Thư Viện

```bash
# Clone hoặc mở thư mục dự án
cd "C:\O E\Blueprint"

# Cài đặt thư viện ứng dụng
pip install -r requirements.txt

# Cài đặt thư viện phục vụ kiểm thử (tuỳ chọn)
pip install -r requirements-dev.txt

# (Tuỳ chọn) Cài PyTorch có CUDA để kích hoạt tăng tốc GPU thật
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### 3. Khởi Chạy Ứng Dụng

```bash
# Khởi chạy giao diện chính Desktop
python main.py

# Kiểm tra khởi động ngầm không cần màn hình (Self-check)
python main.py --self-check
```

### 4. Chạy Bộ Kiểm Thử (72 Tests Passed)

```bash
python -m pytest tests/ -q
```

---

## ⌨️ Phím Tắt Tiện Dụng Trong Ứng Dụng

| Phím tắt | Thao tác tương ứng |
|---|---|
| `Ctrl + O` | Mở ảnh từ máy tính (Hỗ trợ JFIF, JPG, PNG, WEBP, BMP, TIFF) |
| `Ctrl + S` | Lưu kết quả chỉnh sửa (Luôn xuất PNG hoặc JPG) |
| `Ctrl + Enter` | Chạy xử lý công thức đang chọn |
| `Ctrl + Shift + M` | Xóa sạch toàn bộ nét vẽ mask trên canvas |
| `[` / `]` | Giảm / Tăng kích thước cọ vẽ mask |
| `Lăn chuột` | Phóng to / Thu nhỏ ảnh 4K mượt mà tại vị trí con trỏ |
| `Kéo thả (Drag & Drop)` | Thả ảnh trực tiếp vào canvas hoặc bất kỳ vị trí nào trên cửa sổ |

---

## 🤖 Hệ Thống Kỹ Năng Agent (Agent Skills)

Dự án tích hợp hệ thống Agent Skills chuyên nghiệp được tinh gọn dựa trên [Addy Osmani Agent Skills](https://github.com/addyosmani/agent-skills) và [VoltAgent Awesome Agent Skills](https://github.com/VoltAgent/awesome-agent-skills):

- **Kỹ năng nghiệp vụ hình ảnh (`.agents/skills/domain-cv-ai/`):** Tách tần số da, TPS geometry warp, VRAM budgeting, Ingest đa định dạng JFIF & xuất PNG/JPG.
- **Kỹ năng giao diện máy tính (`.agents/skills/domain-ui/`):** PySide6 non-blocking worker thread, QGraphicsView 4K canvas zoom/pan.
- **Kỹ năng kiểm định chất lượng (`.agents/skills/domain-qa/`):** Đo đạc SSIM, ArcFace Cosine, EAR, kiểm toán bản quyền watermark SQLite.
- **Vòng đời kỹ thuật (`.agents/skills/core-lifecycle/`):** `spec-driven-development` (/spec), `planning-and-task-breakdown` (/plan), `incremental-implementation` (/build), `test-driven-development` (/test), `code-review-and-quality` (/review), `code-simplification` (/code-simplify), `debugging-and-error-recovery`.
- **Bất biến hệ thống:** Xem chi tiết tại [photoai-invariants.md](file:///C:/O%20E/Blueprint/.agents/rules/photoai-invariants.md).

---

## 📄 Giấy Phép & Đạo Đức Sử Dụng

Dự án được xây dựng với tinh thần bảo vệ quyền riêng tư cá nhân và tôn trọng bản quyền sở hữu trí tuệ. Chức năng xóa watermark yêu cầu cam kết quyền sở hữu và được ghi nhận lịch sử minh bạch trong hệ thống kiểm toán cục bộ.
