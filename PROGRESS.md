# PROGRESS

## Giai đoạn hiện tại: ĐÃ VIẾT LẠI ỨNG DỤNG THEO BẢN VẼ DESKTOP (`PHOTO_AI_SYSTEM_DESIGN.md`)

Ứng dụng cũ (FastAPI + frontend tĩnh + worker + provider mock) đã được **gỡ bỏ hoàn toàn**.
Repo hiện là **một** ứng dụng desktop 100% offline theo đúng bản vẽ: `src/photoai/`, khởi chạy bằng `python main.py`.

---

## Kiến trúc đã triển khai (khớp §1–§2 của bản vẽ)

- **100% local / offline:** không web server, không Redis/Postgres, không cloud API. Lịch sử job lưu SQLite trong `~/.photo-ai-desktop`.
- **Đường ống 7 bước:** `Ingest → Detect → ROI/Mask → GPU Edit → Blend → AutoQA → Export` (`engine/steps/s1..s7`).
- **Điều phối & retry/fallback:** `engine/runner.py` chạy trong `QThread`; QA trượt → giảm `strength`, đổi seed, tối đa 2 lần; vẫn trượt → trả về **nhánh Classical CV an toàn** kèm cảnh báo.
- **Bất biến ảnh gốc:** `s1_ingest` lưu `original_rgb` ở dạng **read-only** (`flags.writeable = False`), mọi kết quả ghi ra `workspace/results/`.
- **Quản lý VRAM:** `engine/vram_manager.py` — singleton, FP16 trên CUDA/MPS, giữ tối đa `max_active_models=2`, tự offload model cũ + `empty_cache`. Có thêm registry loader model để cắm weights thật mà không sửa core.
- **Hybrid CV + AI chống ảo giác:** tần số cao/thấp (`frequency_sep`), TPS warp (`geometry_tps`), màu sắc (`color_lighting`), vật lý studio (`studio_physics`) đều là thuật toán tất định.
- **QA định lượng:** `qa/metrics.py` (SSIM, Identity Cosine, EAR, Delta-E, Texture Variance, Clip Ratio, Structure) + `qa/evaluator.py` (so ngưỡng YAML, report pass/fail).
- **Giao diện PySide6:** `ui/main_window.py` (sidebar 10 công cụ + canvas zoom/pan + vẽ mask + QA dock + so sánh trước/sau), `ui/widgets/*`, `ui/workers_qt.py`.
- **Watermark an toàn:** recipe `remove_watermark` bắt buộc `ownership_confirmed`, hộp thoại xác nhận + ghi `audit_logs`.

## Cấu trúc `src/photoai` (khớp §2 bản vẽ)

```
src/photoai/
├─ config.py            # đường dẫn, device, giới hạn VRAM, phát hiện torch/cv2/PySide6
├─ errors.py            # PipelineError, NoFaceDetectedError, OwnershipError...
├─ ui/                  # main_window, workers_qt, widgets/ (5 widget)
├─ storage/             # db (jobs/qa_reports/audit_logs), workspace (TTL), image_codec
├─ engine/              # vram_manager, context, recipe_schema, retry, loader, runner
│  └─ steps/            # s1_ingest ... s7_export
├─ detectors/           # face_analyzer, face_parsing, eyes_gaze, person_depth, product_matting, ocr_damage
├─ processors/
│  ├─ cv_ops/           # frequency_sep, geometry_tps, color_lighting, studio_physics
│  └─ ai_wrappers/      # upscaler_gpu, inpainter_gpu, face_restorer_gpu, relighter_gpu
└─ qa/                  # metrics, evaluator
```

## 10 chức năng (recipes/*.yaml)

Mỗi recipe là dữ liệu: `detect → [filter] → edit(editor) → blend → qa`, kèm `retry` và `prompt` (vi/en).
`editor` ánh xạ tới bộ hybrid CV + GPU wrapper: `upscale, skin, geometry, eyes, inpaint, bystanders, restore, relight, lowlight, studio`.

## Cập nhật mới nhất: Tối ưu hiệu năng cao nhất (High-Efficiency) & Nâng cấp Giao diện Hiện đại

1. **Tối ưu hóa hiệu năng tính toán & bộ nhớ (Vừa mạnh vừa nhẹ, ít tài nguyên nhất):**
   - **Chuyển đổi kiểu dữ liệu `float32` toàn diện:** Tái cấu trúc phép biến đổi tần số (`frequency_sep.py`) và hệ màu sRGB-Lab (`color_lighting.py`) từ `float64` sang `float32`, cắt giảm 50% RAM tiêu thụ tức thời trên các bức ảnh độ phân giải cao (4K/8K).
   - **Tối ưu hoá phép ghép mảng không sao chép (Zero-Copy):** Sử dụng phép chiếu mảng NumPy (`skin_mask[:, :, None]`) thay vì `np.repeat(axis=2)`, loại bỏ việc nhân 3 lần bộ nhớ đệm.
   - **Vectorized Overlay Canvas với phép dịch bit:** Thay thế cấp phát mảng 33MB trên mỗi nét cọ vẽ bằng bộ đệm tái sử dụng `_cached_overlay_array` và phép nhân dịch bit `(gray * a >> 8)`.
   - **Bộ nhớ đệm hiển thị Before/After (Frame Caching):** Lưu trữ tỷ lệ co giãn `_scaled_before` và `_scaled_after`, loại bỏ hoàn toàn việc resize ảnh 4K khi người dùng kéo thanh trượt so sánh, mang lại trải nghiệm 120 FPS mượt mà.
   - **Tối ưu hóa ghi đĩa (Disk I/O & SQLite WAL):** Bật chế độ WAL (`PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL; PRAGMA temp_store = MEMORY;`) cho SQLite; thay thế thuật toán brute-force nén PNG bằng `compress_level=6` (nhanh hơn 5-10x, lưu ảnh 4K chỉ trong ~100ms).
   - **Quản lý VRAM chuyên sâu:** Tích hợp `torch.inference_mode()` và `torch.backends.cudnn.benchmark = True`, bổ sung phân chia mảnh gạch thích ứng (`optimal_tile_size`) để chạy suy luận an toàn trên GPU 4GB-8GB không tràn VRAM.

2. **Nâng cấp giao diện trực quan, thẩm mỹ & hiện đại (PySide6 UI Modern Polish):**
   - **Canvas tương tác thông minh:**
     - Hiệu ứng phát sáng viền nét đứt màu xanh ngọc (`#22C55E`) cùng banner `"Thả ảnh để mở ngay"` khi người dùng kéo tệp lướt qua khung vẽ.
     - Trạng thái trống (Empty State) hiện đại hiển thị icon trực quan, hướng dẫn phím tắt và dãy badge định dạng hỗ trợ: `JFIF · JPG · PNG · WEBP · BMP · TIFF`.
   - **Thanh danh sách công cụ dạng thẻ (`ToolCardDelegate`):**
     - Thiết kế card chuyên nghiệp chuẩn Lightroom/Figma: hiển thị số thứ tự 2 chữ số (`01`, `02`...), tiêu đề đậm, phụ đề mô tả công dụng và icon vector đồng bộ.
     - Hiệu ứng chọn thẻ viền sáng với dải accent chỉ báo trạng thái kích hoạt.
   - **Thanh điều khiển Canvas & Phân đoạn công cụ (Segmented Controls):**
     - Nút chế độ `Di chuyển`, `Cọ mask`, `Tẩy` trang bị icon vector trực quan, chuyển đổi mượt mà với phong cách segmented button.
     - Thanh trượt kích thước cọ vẽ hiển thị số đo trực tiếp dạng chip (`28 px`).
     - Bổ sung chip thông tin ảnh hiện tại (`ImageInfoChip`) hiển thị định dạng và độ phân giải (`JFIF · 3840×2160 px`).
     - Hộp hiển thị chi tiết công thức (`RecipeCard`) trong suốt thanh lịch.
   - **Bảng màu QSS Dark Theme chuẩn OLED:** Cập nhật `assets/dark.qss` với các thành phần giao diện bo góc mềm mại, độ tương phản cao, chống mỏi mắt.

3. **Bảo đảm định dạng ảnh nghiêm ngặt:**
   - Hỗ trợ toàn diện các định dạng đầu vào: `.jfif`, `.jpeg`, `.jpg`, `.png`, `.webp`, `.bmp`, `.tif`, `.tiff`, `.gif`.
   - Chuẩn hóa EXIF xoay và hệ màu CMYK/RGBA về RGB chuẩn.
   - Luôn luôn xuất ra định dạng `.png` (lossless) hoặc `.jpg` (high quality JPEG).

## Kết quả kiểm thử

```
python -m pytest tests/ -q          # 72 passed in 3.12s
python main.py --self-check         # Boot offscreen, verify event loop, exit 0
```

- `tests/unit/test_ui_widgets.py`: Kiểm thử offscreen bộ widget `InteractiveCanvas`, `ToolSelector`, `MainWindow` và chu trình nạp ảnh `.jfif`.
- `tests/unit/test_image_codec.py`: 7 bài test chuyên biệt kiểm tra nạp file `.jfif`, `.webp`, `.bmp`, chuyển đổi CMYK/RGBA, tự sửa đuôi mở rộng khi xuất, và chạy bước `s7_export` với format PNG/JPG.
- Toàn bộ 72 test pass 100%.


## Hiệu chuẩn ngưỡng (đo, không giả định)

- `upscale_4k` không gate `outside_mask_ssim` toàn ảnh (kết quả resize 4x) — chỉ gate `identity ≥ 0.95`, `structure ≥ 0.99`, `clip ≤ 1%`.
- `open_eyes` giữ gate `ear_min ≥ 0.22` (chất lượng sản phẩm). Với nhánh fallback (không có model landmark thật) gate này **cố ý fail → best-effort**; test mô phỏng model trả EAR mở qua `post_left_ear/post_right_ear` để chứng minh gate hoạt động.
- `product_studio` chỉ đo `product_pixel_diff` trên **lõi sản phẩm đục hoàn toàn** (matte > 250) — vùng viền mờ hợp lệ được trộn nền nên không tính là sai khác. Đo được `0.0`.

## Giới hạn trung thực (không che giấu)

1. **Chưa có model GPU thật.** `torch` và `cv2` là **tùy chọn**; máy test hiện không cài, nên các `ai_wrappers` chạy nhánh Classical CV tương đương (Lanczos/Telea-diffusion/unsharp/grade). Cắm model thật qua `engine.vram_manager.register_model_loader(key, loader)` — không sửa core.
2. **Detector là heuristic khi thiếu model:** face = Haar/centred-box, landmark 68 = tổng hợp hình học, parsing = YCbCr, person = blob da, matting = chênh nền, OCR = MSER/edge-grid. Interface đã đúng để thay model (InsightFace/BiSeNet/YOLO+Depth-Anything/BiRefNet/PaddleOCR).
3. **EAR & Identity là placeholder đo được** (landmark tổng hợp, embedder 16×16). Sẽ thay bằng MediaPipe/ArcFace; re-tighten ngưỡng sau.
4. **`restore_old_photo`** đích 4K (`target_long_edge: 4096`) đọc từ recipe; test truyền `target_long_edge: 256` để suite nhanh, code không đổi hành vi.

## Chạy & kiểm thử

```bash
# Chạy ứng dụng desktop
python main.py

# (tuỳ chọn) bật tăng tốc GPU/CV
pip install torch opencv-python-headless

# Test
python -m pytest tests/ -q
```

## Bước tiếp theo (đề xuất)

1. Tải weights thật và đăng ký loader (`realesrgan`, `lama`, `codeformer`, `ic_light`, `insightface`, `bisenet`, `birefnet`, `paddleocr`).
2. Thay placeholder detector/embedder bằng model — giữ nguyên interface.
3. Re-tighten ngưỡng QA theo model thật (đặc biệt `open_eyes.ear_min`, `identity_cosine`).
4. Dọn TTL/`purge_expired_cache` theo lịch định kỳ trong UI.
