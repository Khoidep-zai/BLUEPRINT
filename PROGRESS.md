# PROGRESS

## Giai đoạn hiện tại: HOÀN THÀNH P0 → P4 (chờ model AI thật để thay provider mock)

## Đã xong

### P0 — Nền tảng (trước đây)
- [x] Repo theo cấu trúc §3, PROGRESS.md, docs/
- [x] providers/{base,mock,registry}.py (S2 Provider Adapter)
- [x] pipeline/{recipe_schema,context,errors,loader,retry,runner}.py + steps/ (S1 Recipe Runner)
- [x] detectors/ + editors/ + qa/ + masking.py + io/
- [x] 10 recipe YAML + 20 prompt (.vi/.en) theo yêu cầu chi tiết của người dùng

### P1 — Chân dung cơ bản + hạ tầng đo lường
- [x] Detectors nâng cấp (OpenCV có feature-detect, fallback an toàn): face Haar Cascade, person skin-blob, text MSER
- [x] EAR thật theo công thức `(|p2−p6|+|p3−p5|)/(2|p1−p4|)`; **re-detect EAR sau edit** khi recipe gate `ear_min` (đo kết quả, không đo đầu vào)
- [x] Re-check sau edit: `delta_e_skin` tự đo bằng skin mask YCbCr heuristic; `ocr_recheck`/`person_recheck` luôn được đưa vào report
- [x] Sửa bug: recipe `person: true` (số ít) giờ được detect step hiểu đúng
- [x] `blend: { method: none }` cho upscale (giữ ảnh to, không ghép về size gốc)
- [x] `upscale_4k` chạy thật: editor `upscale` 4x, cap cạnh dài 8192px

### P2 — API end-to-end (chọn chức năng → upload → xử lý → output)
- [x] Tái cấu trúc: `src/backend/` (FastAPI + in-memory store), `src/frontend/` (app tĩnh), `workers/` (core pipeline)
- [x] Loại bỏ **Migration DB / Postgres / SQLAlchemy / Alembic / Redis / RQ** — không cần DB
- [x] `POST /api/jobs` (multipart): validate upload → decode → chạy recipe → QA report → lưu kết quả in-memory
- [x] `GET /api/recipes`, `GET /api/recipes/{id}`, `GET /api/jobs`, `GET /api/jobs/{id}`, `GET /api/jobs/{id}/result`
- [x] Envelope lỗi chuẩn `{"error": {"code", "message"}}`; watermark thiếu xác nhận → **403 OWNERSHIP_REQUIRED** + audit log
- [x] Ảnh gốc không bao giờ bị ghi đè (lưu riêng, kết quả là asset mới)

### P3 — Golden set + hiệu chuẩn QA (đo, không giả định)
- [x] Generator ảnh tổng hợp deterministic: **20 ảnh × 10 chức năng = 200 ảnh** (`tests/golden/generate.py`)
- [x] Script hiệu chuẩn chạy toàn bộ qua runner thật + mock provider (`tests/golden/calibrate.py`) → `expected.json` từng chức năng
- [x] Test replay kiểm tra số đo tái lập chính xác (deterministic)

### P4 — Frontend + đóng gói
- [x] `src/frontend/`: app tĩnh (HTML/CSS/JS thuần, không build step) — chọn chức năng, kéo-thả ảnh, xem trước/sau, bảng QA, tải kết quả, lịch sử
- [x] FastAPI phục vụ frontend tại `/`; không cần đăng nhập
- [x] `docker-compose.yml` 1 service duy nhất (bỏ postgres/redis/worker); Dockerfile.api PYTHONPATH đúng
- [x] requirements.txt gọn đúng stack Python thực tế

## Kết quả hiệu chuẩn golden set (mock-1, seed=42, ảnh tổng hợp)

| Chức năng | Pass | Best-effort | Số đo chính (mean) | Ghi chú |
|---|---|---|---|---|
| open_eyes | 0.00 | 1.00 | ear=0.15, identity=1.0000 | Gate `ear_min ≥ 0.20` **cố ý fail** với mock (cần model landmark thật); gate pass khi mô phỏng model trả EAR mở (có test) |
| skin_retouch | 1.00 | 0.00 | delta_e_skin=0.045 (≤3.0) | |
| chin_fix | 1.00 | 0.00 | identity=1.0000, ssim=1.0000 | |
| remove_bystanders | 1.00 | 0.00 | ssim=0.9996 | detect `person` chạy đúng (regression test) |
| remove_watermark | 1.00 | 0.00 | ssim=0.9969, clip=0.06% | Cần `ownership_confirmed=true`; audit log ghi nhận |
| restore_old_photo | 1.00 | 0.00 | identity=1.0000, clip=0% | |
| golden_hour | 1.00 | 0.00 | delta_e_skin=0.849 (≤4.0), clip=0.35% | |
| low_light_fix | 1.00 | 0.00 | delta_e_skin=3.085 (≤4.0) | |
| upscale_4k | 1.00 | 0.00 | ssim=0.9797, structure=0.9999 | Ngưỡng đã hiệu chuẩn (xem dưới) |
| product_studio | 1.00 | 0.00 | ssim=0.9966 | |

### Quyết định hiệu chuẩn (đã ghi nhận)
- `upscale_4k`: `outside_mask_ssim_min` 0.98 → **0.975** (đo thực tế 0.9794–0.9799 với LANCZOS roundtrip; luôn giữ margin) và **thêm gate** `structure_similarity_min: 0.99` (đo 0.99989). Re-tighten khi có model SR thật.
- `open_eyes`: **giữ nguyên** gate 0.20 (yêu cầu chất lượng sản phẩm) — không hạ ngưỡng để test xanh.

## Endpoint API

| Method | Path | Mô tả |
|---|---|---|
| GET | `/healthz` | Health check |
| GET | `/api/recipes` | Danh sách 10 chức năng (tên VI/EN, có cần xác nhận sở hữu?) |
| GET | `/api/recipes/{id}` | Chi tiết 1 chức năng |
| POST | `/api/jobs` | multipart: `file`, `recipe_id`, `params` (JSON), `ownership_confirmed` → xử lý & trả job + QA |
| GET | `/api/jobs` | Danh sách job gần đây |
| GET | `/api/jobs/{id}` | Job + báo cáo QA |
| GET | `/api/jobs/{id}/result` | Tải ảnh kết quả (PNG) |
| GET | `/` | Frontend |

## Quyết định đã chốt (theo yêu cầu người dùng)
- Độ phân giải mục tiêu phục chế ảnh cũ: **Full HD 4K**; cap cạnh dài upscale: **8192px**
- Provider chỉnh sửa: **ưu tiên chất lượng** (hiện tại `mock:v1` — provider thật sẽ thay qua adapter, không sửa core)
- Triển khai: **tự host CPU**, nhẹ/nhanh/tốt
- Giao diện: **không cần đăng nhập**
- **Không dùng DB**: in-memory store, luồng 1 request = 1 ảnh
- Stack: **Python** (FastAPI, pytest, Pillow, numpy; OpenCV optional)

## Giới hạn hiện tại (trung thực — không che giấu)
1. Provider `mock:v1` chỉ tint màu deterministic: pipeline/QA/threshold chạy thật, nhưng chất lượng thị giác thật cần provider AI (lộ trình: adapter mới trong `providers/`).
2. `ear`/`identity_cosine` với mock là **placeholder đo được** (không phải model mặt thật): `ear` từ landmark tổng hợp, identity từ embedder 16×16 — sẽ thay bằng MediaPipe/ArcFace.
3. `ocr_recheck`/`person_recheck` khi không inject detector trả về True theo hợp đồng P0 đã document; logic gate 2 chiều đã có test với detector stub.
4. Detector OpenCV là heuristic và chỉ bật khi `cv2` cài (hiện fallback placeholder) — không tải model.

## Chạy & kiểm thử
```powershell
# Chạy app (từ gốc dự án)
$env:PYTHONPATH = "src/backend;workers/src;."
python -m uvicorn photoai_api.main:app --port 8000   # http://127.0.0.1:8000

# Test toàn bộ
python -m pytest tests/ -q                            # 101 passed

# Tạo lại golden set + hiệu chuẩn
python tests/golden/generate.py
python tests/golden/calibrate.py
```

## Phiên bản model đang dùng
- `mock-1` (P0–P4). Khi chọn provider thật: đăng ký trong `providers/registry.py`, đổi `provider` trong recipe YAML, chạy lại golden calibration.

## Bước tiếp theo (đề xuất)
1. Chọn provider AI thật (ưu tiên chất lượng) → thay `mock` trong YAML + chạy lại calibrate.
2. Thay placeholder detectors/embedder bằng model (MediaPipe FaceMesh, ArcFace, OCR) — giữ nguyên interface.
3. Re-tighten ngưỡng QA theo model thật (open_eyes ear_min, identity, delta_e_skin).
4. TTL/privacy: dọn blob theo `expires_at`, thêm rate limit theo design §8.
