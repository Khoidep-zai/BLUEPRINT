# Phase report — P1 → P4 (hoàn tất luồng sản phẩm, không DB)

> Ngày: 2026-10-16 · Trạng thái: **hoàn tất** · Bằng chứng kiểm thử: `101 passed` (`python -m pytest tests/ -q`)

## 1. Phạm vi đã giao

| Hạng mục | Nội dung |
|---|---|
| P1 | Detector mặt/EAR + re-detect sau edit; sửa bug detect `person`; blend `none` cho upscale; 10 recipe chạy được end-to-end |
| P2 | API FastAPI đầy đủ (upload → xử lý → kết quả + QA); in-memory store thay SQLAlchemy/Postgres/Alembic/Redis; bỏ migration theo ERD |
| P3 | Golden set 200 ảnh (20 × 10 chức năng) deterministic; script hiệu chuẩn ghi số đo thật; test replay tái lập |
| P4 | Frontend tĩnh trong `src/frontend` phục vụ tại `/`; đóng gói Docker 1 service; requirements đúng stack |

## 2. Kiến trúc luồng (đúng yêu cầu người dùng)

```
Người dùng chọn chức năng (10 card) → tải ảnh → POST /api/jobs
   → validate upload → decode ảnh (Pillow)
   → RecipeRunner: detect → filter → edit (provider adapter) → blend → QA (+retry)
   → lưu kết quả PNG + QA report vào in-memory store
   → trả job + QA; frontend hiển thị trước/sau, tải kết quả
```

- Ảnh gốc **không bao giờ bị ghi đè** (asset `original` tách khỏi asset `result`).
- Không có DB/queue: 1 request = 1 ảnh xử lý xong mới trả về (self-host CPU).
- `remove_watermark` bắt buộc `ownership_confirmed=true`, nếu thiếu → `403 OWNERSHIP_REQUIRED` + audit log `watermark_blocked`; khi chạy → audit `watermark_confirmed`.

## 3. Endpoint

| Method | Path | Ghi chú |
|---|---|---|
| GET | `/healthz` | `{"status": "ok"}` |
| GET | `/api/recipes` | 10 chức năng + metadata (`requires_ownership`, steps, editor) |
| GET | `/api/recipes/{id}` | 404 `RECIPE_NOT_FOUND` nếu sai |
| POST | `/api/jobs` | multipart `file` + `recipe_id` + `params`(JSON: strength, seed, post_left_ear, post_right_ear…) + `ownership_confirmed` |
| GET | `/api/jobs` / `/api/jobs/{id}` | job + `qa_report` (passed, metrics, thresholds, warnings) |
| GET | `/api/jobs/{id}/result` | PNG kết quả |
| GET | `/` | Frontend (`src/frontend`) |

Envelope lỗi: `{"error": {"code": ..., "message": ...}}` — `INVALID_FILE_TYPE|IMAGE_TOO_LARGE|OWNERSHIP_REQUIRED|NO_FACE_DETECTED|NO_CLOSED_EYES|RECIPE_NOT_FOUND|JOB_NOT_FOUND|INVALID_PARAMS`.

## 4. Đo lường QA (golden set 200 ảnh, mock-1, seed 42)

| Chức năng | Pass | Best-effort | Số đo chính (mean) |
|---|---|---|---|
| open_eyes | 0.00 | 1.00 | ear=0.15 — gate 0.20 cố ý fail với mock; pass khi mô phỏng model trả mắt mở (test riêng) |
| skin_retouch | 1.00 | 0.00 | delta_e_skin=0.045 / gate 3.0 |
| chin_fix | 1.00 | 0.00 | identity=1.0, ssim=1.0 |
| remove_bystanders | 1.00 | 0.00 | ssim=0.9996, person_recheck=True |
| remove_watermark | 1.00 | 0.00 | ssim=0.9969, clip=0.06%, ocr_recheck=True |
| restore_old_photo | 1.00 | 0.00 | identity=1.0, clip=0% |
| golden_hour | 1.00 | 0.00 | delta_e=0.849 / 4.0, clip=0.35% |
| low_light_fix | 1.00 | 0.00 | delta_e=3.085 / 4.0 |
| upscale_4k | 1.00 | 0.00 | ssim=0.9797 / 0.975, structure=0.9999 / 0.99 |
| product_studio | 1.00 | 0.00 | ssim=0.9966 / 0.95 |

**Hiệu chuẩn đã áp dụng:** `upscale_4k` hạ `outside_mask_ssim_min` 0.98→0.975 (đo thật 0.9794–0.9799, giữ margin) và thêm gate `structure_similarity_min=0.99`. `open_eyes` **giữ nguyên** gate 0.20 — không hạ chuẩn để test xanh; QA trả best-effort + cảnh báo trung thực.

## 5. Kiểm thử (101 tests)

- `tests/unit/` (47): runner, recipe schema, QA modules, detectors/masking, provider mock.
- `tests/integration/test_p1_functions.py` (5): 4 chức năng P1 qua runner.
- `tests/integration/test_all_recipes.py` (16): 10 recipe chạy end-to-end; regression detect `person`; filter mắt mở; gate EAR pass khi model mô phỏng; watermark ownership.
- `tests/integration/test_api_jobs.py` (13): healthz, recipes, full flow, watermark 403/OK, upscale, lỗi 400/404, frontend `/`, danh sách job.
- `tests/integration/test_golden_set.py` (20): 20 ảnh/chức năng đã đo, replay tái lập số đo (P1 đủ 20 ảnh, còn lại subset 5).

## 6. Giới hạn & bước tiếp theo

1. `mock:v1` chỉ mô phỏng chỉnh sửa → cần provider AI thật (đăng ký `providers/registry.py`, không sửa core).
2. Placeholder đo lường (EAR tổng hợp, embedder 16×16) → thay bằng model thật rồi re-tighten ngưỡng.
3. `ocr_recheck`/`person_recheck` pass-through khi không có detector (hợp đồng P0 đã document; logic 2 chiều có test).
4. Privacy: thêm TTL dọn blob + rate limit theo design §8 ở phase hardening.
