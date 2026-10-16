---
trigger: glob
description: "Bất biến kỹ thuật và nghiệp vụ Photo AI Desktop (100% Offline Local GPU, Original Immutability, Strict PNG/JPG Export, Multi-format JFIF support, VRAM Budget, Non-blocking Qt UI, Hybrid CV+AI fallback, Quantitative QA Gating)."
globs: "src/**/*.py, recipes/**/*.yaml, tests/**/*.py, main.py"
---

# Photo AI Desktop Invariants (Bất biến hệ thống & nghiệp vụ)

Áp dụng cho **mọi** dòng code phát triển thuật toán, pipeline, storage, hoặc giao diện trong dự án Photo AI Desktop. Vi phạm = lỗi kiến trúc nghiêm trọng.

## 1. 100% Offline & Local GPU (Không phụ thuộc mạng)
- Toàn bộ tác vụ suy luận và xử lý ảnh chạy trên phần cứng cục bộ (`cuda`, `mps`, hoặc `cpu`).
- Tuyệt đối không gửi ảnh, dữ liệu khuôn mặt, EXIF, hoặc telemetry qua Internet (No cloud API, no external webhooks, no telemetry).
- Lịch sử job và báo cáo QA lưu trữ bằng SQLite cục bộ (`~/.photo-ai-desktop/photoai.db`).

## 2. Bảo Toàn Ảnh Gốc Tuyệt Đối (Original Immutability)
- Khi nạp ảnh vào RAM qua `load_image`, mảng NumPy gốc `original_rgb` phải được khóa quyền ghi:
  `context.original_rgb.flags.writeable = False`
- Không bao giờ ghi đè lên file ảnh gốc của người dùng. Mọi sản phẩm xuất ra phải lưu vào `workspace/results/` hoặc đường dẫn do người dùng chỉ định.

## 3. Đa Định Dạng Đầu Vào (Đặc biệt JFIF) & Luôn Xuất PNG hoặc JPG
- **Đầu vào (Multi-format Ingest):** Bắt buộc hỗ trợ nạp mượt mà mọi định dạng ảnh phổ biến: `.jfif`, `.jpeg`, `.jpg`, `.png`, `.webp`, `.bmp`, `.tiff`, `.tif`, `.gif`. Đặc biệt xử lý EXIF rotation an toàn và chuẩn hóa hệ màu CMYK/RGBA về standard sRGB 3-channel.
- **Đầu ra (Strict PNG/JPG Export):** Ảnh sau khi chỉnh sửa qua Pipeline hoặc lưu từ giao diện **LUÔN LUÔN** xuất ra file định dạng `.png` (lossless) hoặc `.jpg` / `.jpeg` (high quality JPEG). Mọi phần mở rộng khác phải tự động chuẩn hóa về PNG hoặc JPG.

## 4. Quản Lý VRAM Tối Đa 2 Model (VRAM Budget & Lifecycle)
- Không bao giờ nạp toàn bộ các deep learning model cùng lúc vào VRAM.
- Mọi model (Real-ESRGAN, LaMa, CodeFormer, IC-Light, BiSeNet, BiRefNet) phải thông qua `VRAMModelManager`.
- Số lượng model active đồng thời trên VRAM không vượt quá 2 (`max_active_models = 2`).
- Khi nạp model thứ 3, tự động offload model cũ nhất về CPU, `del`, gọi `gc.collect()` và `torch.cuda.empty_cache()` để chống tràn VRAM (Zero CUDA OOM trên GPU 8GB-12GB).

## 5. Giao Diện Không Bao Giờ Bị Khóa (Non-blocking PySide6 UI)
- Toàn bộ các bước pipeline (`s1_ingest` đến `s7_export`) bắt buộc chạy trong worker thread riêng biệt (`QThread` / `PipelineWorker`).
- Giao tiếp giữa background worker và giao diện người dùng chỉ thực hiện qua Qt Signals:
  `progress(stage, percent)`, `finished_ok(result)`, `failed(message)`.
- UI chính phải luôn phản hồi mượt mà với các thao tác phóng to/thu nhỏ (Zoom 4K), di chuyển (Pan), vẽ mask và phím tắt.

## 6. Chống Ảo Giác Bằng Hybrid Classical CV + AI
- Luôn kết hợp thị giác máy tính cổ điển (Classical CV: OpenCV, NumPy) với AI:
  - Tách tần số (`FrequencySeparator`): Bảo tồn nguyên vẹn lỗ chân lông da và kết cấu thật (`high_freq`).
  - Biến dạng lưới Thin-Plate Spline (`geometry_tps`): Chỉnh góc mặt, nọng cằm tinh tế bằng phép biến đổi hình học tất định thay vì cho AI vẽ lại toàn bộ mặt.
  - Khóa vùng ROI và ghép lại (`Poisson / Feather Blend`): Chỉ tác động vào vùng cần sửa, giữ nguyên các vùng xung quanh.

## 7. Đánh Giá Chất Lượng Định Lượng (AutoQA) & Tự Động Fallback
- Kết quả sau khi chỉnh sửa bắt buộc đi qua bước `s6_qa` để đo lường các chỉ số số học:
  `identity_cosine`, `ssim`, `ear_after`, `delta_e_skin`, `texture_variance`, `clip_ratio`.
- Nếu trượt ngưỡng quy định trong Recipe YAML:
  - Tự động giảm `strength` (hoặc đổi seed) và retry tối đa 2 lần.
  - Nếu sau 2 lần vẫn không đạt, tự động trả về kết quả an toàn từ nhánh Classical CV kèm cảnh báo rõ ràng.

## 8. Tuân Thủ Bản Quyền & Ghi Nhật Ký Đạo Đức (Ethical & Ownership Audit)
- Đối với recipe xóa watermark/logo bản quyền (`remove_watermark`), bắt buộc yêu cầu người dùng tích xác nhận quyền sở hữu (`ownership_confirmed == True`).
- Bắt buộc ghi nhận sự kiện vào bảng `audit_logs` trong SQLite kèm timestamp UTC.
