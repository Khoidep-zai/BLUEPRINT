# Photo AI Tool — Bản vẽ hệ thống chi tiết

*Tài liệu bổ sung cho `AGENT_SKILLS.md`. Gồm: kiến trúc, cấu trúc `src`, ERD, use case, API contract, test plan, checklist bảo mật, mẫu báo cáo và lộ trình từng bước.*

> **Lưu ý:** file `BLUEPRINT.md` gốc chưa được gửi kèm nên 10 chức năng được suy ra từ ma trận §5 của `AGENT_SKILLS.md`. Nếu BLUEPRINT có ngưỡng QA khác, hãy ưu tiên BLUEPRINT và sửa lại các ngưỡng bên dưới.

## 1. Phạm vi & nguyên tắc

| # | ID recipe | Chức năng | QA chính |
|---|---|---|---|
| 1 | `upscale_4k` | Nâng cấp 4K | identity, structure_similarity |
| 2 | `skin_retouch` | Retouch da | identity, delta_e_skin, texture_variance |
| 3 | `chin_fix` | Sửa nọng cằm | identity, outside_mask_ssim |
| 4 | `open_eyes` | Cứu ảnh nhắm mắt | ear, identity, outside_mask_ssim |
| 5 | `remove_watermark` | Xóa watermark | ocr_recheck, outside_mask_ssim |
| 6 | `remove_bystanders` | Xóa người hậu cảnh | person_recheck, outside_mask_ssim |
| 7 | `restore_old_photo` | Phục chế ảnh cũ | identity, structure_similarity, clip_ratio |
| 8 | `golden_hour` | Chân dung giờ vàng | delta_e_skin, clip_ratio, identity |
| 9 | `low_light_fix` | Sửa ảnh thiếu sáng | clip_ratio, delta_e_skin |
| 10 | `product_studio` | Điện thoại → Studio | shape/logo similarity, color_shift |

**Nguyên tắc cốt lõi (rút từ AGENT_SKILLS §2):** không ghi đè ảnh gốc; ràng buộc prompt không bị làm yếu; mọi chức năng có QA bằng số; recipe-driven; provider adapter; riêng tư và TTL; watermark cần `ownership_confirmed` + audit log.

## 2. Kiến trúc hệ thống

### 2.1 Sơ đồ tổng thể

```
┌──────────────┐  HTTPS   ┌───────────────┐   enqueue   ┌────────────┐
│ Web (PWA)    │ ───────▶ │ API (FastAPI) │ ──────────▶ │ Redis/Queue│
│ Next.js      │ ◀─WS──── │ auth, jobs    │             └─────┬──────┘
└──────┬───────┘          └───┬───────┬───┘                   │ pull
       │ presigned PUT        │       │ SQL                   ▼
       ▼                      │       ▼              ┌────────────────────┐
┌──────────────┐ read/write   │  ┌──────────┐        │ Worker (GPU/CPU)   │
│ Object Store │◀─────────────┘  │ Postgres │◀───────│ Recipe Runner      │
│ (S3/MinIO)   │◀────────────────┴──────────┘ status │ detect→filter→edit │
│ originals/   │                                      │ →blend→qa          │
│ results/     │                                      └───┬─────────┬──────┘
└──────────────┘                                          │         │
                                              ┌───────────▼──┐  ┌───▼──────────┐
                                              │ Providers/   │  │ QA modules   │
                                              │ mock | real  │  │ identity,ssim│
                                              └──────────────┘  └──────────────┘
```

### 2.2 Luồng một job

1. Client xin presigned URL → upload ảnh gốc lên `originals/` (chỉ đọc).
2. Client gọi `POST /v1/jobs` với `recipe_id`, `asset_id`, tham số.
3. API validate, ghi `jobs(status=queued)`, đẩy vào queue.
4. Worker lấy job → `running`: detect → filter → edit → blend.
5. Chuyển `qa`: chạy các đo lường, ghi `qa_reports`.
6. Fail QA → retry tối đa 2 lần (giảm strength, đổi seed); vẫn fail → trả bản tốt nhất kèm `warnings`.
7. `done` → kết quả lưu `results/`; client nhận qua WebSocket/polling; TTL tự xóa.

### 2.3 Quyết định kiến trúc (ADR rút gọn)

| ADR | Quyết định | Lý do |
|---|---|---|
| 001 | Modular monolith + worker tách riêng | Đơn giản giai đoạn đầu, GPU scale độc lập |
| 002 | Recipe YAML + Pydantic schema | Thêm chức năng không sửa lõi |
| 003 | Provider adapter duy nhất cho SDK ngoài | Đổi nhà cung cấp bằng cấu hình |
| 004 | Postgres + S3 + Redis | Chuẩn, dễ vận hành |
| 005 | Job idempotent (khóa `idempotency_key`) | Retry an toàn |

## 3. Cấu trúc `src` chi tiết

```
photo-ai/
├─ apps/
│  ├─ api/
│  │  ├─ src/photoai_api/
│  │  │  ├─ main.py                 # tạo app FastAPI
│  │  │  ├─ config.py               # đọc env, không hard-code secret
│  │  │  ├─ deps.py                 # db session, auth, rate limit
│  │  │  ├─ routers/
│  │  │  │  ├─ uploads.py  jobs.py  assets.py  recipes.py  feedback.py  health.py
│  │  │  ├─ schemas/                # Pydantic request/response
│  │  │  ├─ services/               # job_service, asset_service, audit_service
│  │  │  ├─ models/                 # SQLAlchemy (khớp ERD)
│  │  │  ├─ repositories/
│  │  │  ├─ security/               # auth, validators, upload_guard
│  │  │  └─ errors.py               # mã lỗi chuẩn
│  │  ├─ migrations/                # Alembic
│  │  └─ tests/
│  └─ web/
│     └─ src/
│        ├─ app/                    # routes: /, /tool/[id], /job/[id]
│        ├─ components/
│        │  ├─ ToolGrid  Uploader  MaskCanvas  SubjectPicker
│        │  ├─ BeforeAfterSlider  QaPanel  JobProgress
│        ├─ lib/                    # api-client, ws-client, image-utils
│        ├─ hooks/                  # useJob, useUpload
│        └─ e2e/                    # Playwright
├─ workers/
│  ├─ src/photoai_worker/
│  │  ├─ main.py                    # consumer queue
│  │  ├─ pipeline/
│  │  │  ├─ recipe_schema.py  runner.py  context.py  retry.py
│  │  │  └─ steps/ detect.py filter.py edit.py blend.py qa.py
│  │  ├─ detectors/   face.py  eyes_ear.py  person.py  text_logo.py
│  │  ├─ editors/     upscale.py  inpaint.py  relight.py  color.py  retouch.py  restore.py  studio.py
│  │  ├─ qa/          identity.py  ssim.py  lpips.py  ocr_recheck.py  person_recheck.py  skin_color.py  clip_ratio.py  report.py
│  │  └─ io/          storage.py  image_codec.py
│  └─ tests/
├─ providers/
│  ├─ base.py                       # ImageEditProvider.edit(image, mask?, prompt, strength, seed)
│  ├─ mock.py
│  ├─ <provider_thật>.py
│  └─ registry.py                   # chọn provider theo cấu hình
├─ recipes/        # 10 file YAML, mỗi file có ngưỡng QA
├─ prompts/        # <id>.vi.md  <id>.en.md
├─ tests/
│  ├─ golden/<recipe_id>/ images/ expected.json
│  ├─ unit/  integration/  e2e/  perf/  security/
├─ docs/
│  ├─ architecture.md  erd.md  api-contract.md  usecases.md
│  ├─ test-plan.md  security-checklist.md  adr/  reports/
├─ infra/  docker-compose.yml  Dockerfile.*  k8s/  ci/
├─ AGENT_SKILLS.md  BLUEPRINT.md  PROGRESS.md
```

**Quy tắc phụ thuộc:** `routers → services → repositories`; `worker steps → detectors/editors/qa → providers`. Không import ngược. Chỉ `providers/` được import SDK ngoài.

## 4. ERD (cơ sở dữ liệu)

```
users 1───* assets 1───* jobs 1───* job_steps
  │                       │ 1───* qa_reports
  │                       │ 1───* provider_calls
  │ 1───* audit_logs ─────┘ (job_id, nullable)
  └──* feedback *──1 jobs
recipes_registry 1───* jobs
```

| Bảng | Cột chính | Ghi chú |
|---|---|---|
| `users` | id PK, email UK, role, created_at, deleted_at | Có thể ẩn danh ở bản đầu |
| `assets` | id PK, user_id FK, kind (original/result/mask), storage_key, mime, width, height, sha256, expires_at | `original` bất biến |
| `recipes_registry` | id PK (recipe_id), version, yaml_hash, active | Đồng bộ từ `recipes/` |
| `jobs` | id PK, user_id FK, recipe_id FK, input_asset_id FK, mask_asset_id FK null, params JSONB, status, idempotency_key UK, ownership_confirmed bool, result_asset_id FK null, warnings JSONB, created_at, finished_at | status: queued/running/qa/done/failed |
| `job_steps` | id PK, job_id FK, name, status, attempt, started_at, ended_at, error_code | detect/filter/edit/blend/qa |
| `qa_reports` | id PK, job_id FK, attempt, metrics JSONB, thresholds JSONB, passed bool | Mỗi lần retry một dòng |
| `provider_calls` | id PK, job_id FK, provider, model_version, seed, strength, latency_ms, cost_usd | Phục vụ đo chi phí/độ trễ |
| `audit_logs` | id PK, user_id, job_id null, action, detail JSONB, ip_hash, created_at | Bắt buộc với `remove_watermark` |
| `feedback` | id PK, job_id FK, rating, comment | Không chứa ảnh |

**Chỉ mục:** `jobs(user_id, created_at)`, `jobs(status)`, `assets(expires_at)`, `qa_reports(job_id)`.
**Ràng buộc:** `jobs.ownership_confirmed = true` khi `recipe_id = remove_watermark` (CHECK ở tầng service + test).

## 5. Use case

| UC | Tác nhân | Luồng chính | Ngoại lệ |
|---|---|---|---|
| UC1 Chọn chức năng & upload | Người dùng | Mở lưới 10 chức năng → chọn → upload | File sai định dạng/quá lớn → báo lỗi rõ |
| UC2 Chạy chỉnh ảnh | Người dùng | Gửi job → xem tiến độ → xem trước/sau | Không thấy mặt/mắt nhắm → thông báo, không crash |
| UC3 Chạm chọn chủ thể / tô mask | Người dùng | Chạm chủ thể chính hoặc tô vùng cần sửa | Mask quá nhỏ → gợi ý |
| UC4 Xóa watermark | Người dùng | Tick xác nhận quyền sở hữu → chạy → audit log | Không tick → từ chối |
| UC5 Xem QA | Người dùng | Panel QA dễ hiểu (đạt/cảnh báo) | QA fail → nhận bản tốt nhất + cảnh báo |
| UC6 Tải/xóa ảnh | Người dùng | Tải kết quả; xóa sớm trước TTL | — |
| UC7 Thêm chức năng/recipe | Dev/Agent | Thêm YAML + prompt + golden + QA | CI chặn nếu QA giảm |
| UC8 Giám sát | Vận hành | Xem queue, lỗi, chi phí/job | — |

## 6. API contract (v1)

Quy ước: JSON, `Authorization: Bearer <token>`, thời gian ISO-8601 UTC, lỗi theo mẫu chung.

| Method | Đường dẫn | Mô tả |
|---|---|---|
| POST | `/v1/uploads/presign` | Body `{filename, mime, size}` → `{asset_id, upload_url, expires_in}` |
| POST | `/v1/assets/{id}/complete` | Xác nhận upload xong, server kiểm tra magic bytes, kích thước |
| GET | `/v1/recipes` | Danh sách chức năng + tham số cho phép |
| POST | `/v1/jobs` | Tạo job (header `Idempotency-Key`) |
| GET | `/v1/jobs/{id}` | Trạng thái, `qa_report`, `warnings` |
| GET | `/v1/jobs/{id}/result` | URL tải kết quả (presigned, ngắn hạn) |
| POST | `/v1/jobs/{id}/retry` | Chạy lại với tham số mới |
| WS | `/v1/jobs/{id}/events` | Đẩy trạng thái `queued/running/qa/done/failed` |
| DELETE | `/v1/assets/{id}` | Xóa sớm |
| POST | `/v1/feedback` | `{job_id, rating, comment}` |
| GET | `/healthz` | Kiểm tra sống |

**Tạo job — request**

```json
{
  "recipe_id": "open_eyes",
  "input_asset_id": "ast_123",
  "mask_asset_id": null,
  "params": { "subject_point": [0.52, 0.41], "strength": 0.5, "seed": 42 },
  "ownership_confirmed": false
}
```

**Response 202**

```json
{ "job_id": "job_456", "status": "queued", "created_at": "2026-10-16T08:00:00Z" }
```

**Job done — response**

```json
{
  "job_id": "job_456", "status": "done",
  "result_asset_id": "ast_789",
  "warnings": [],
  "qa_report": {
    "passed": true, "attempt": 1,
    "metrics": { "ear": 0.27, "identity_cosine": 0.93, "outside_mask_ssim": 0.991 },
    "thresholds": { "ear_min": 0.2, "identity_cosine_min": 0.85, "outside_mask_ssim_min": 0.98 }
  }
}
```

**Lỗi chuẩn**

```json
{ "error": { "code": "NO_FACE_DETECTED", "message": "Không tìm thấy khuôn mặt.", "request_id": "req_abc" } }
```

| Mã lỗi | HTTP | Ý nghĩa |
|---|---|---|
| `INVALID_FILE_TYPE` | 400 | Định dạng không hỗ trợ |
| `IMAGE_TOO_SMALL` / `IMAGE_TOO_LARGE` | 422 | Ngoài giới hạn kích thước |
| `NO_FACE_DETECTED` | 422 | Chức năng cần mặt |
| `NO_CLOSED_EYES` | 422 | Không có mắt nhắm để sửa |
| `OWNERSHIP_REQUIRED` | 403 | Thiếu `ownership_confirmed` |
| `RATE_LIMITED` | 429 | Quá giới hạn |
| `QA_FAILED_BEST_EFFORT` | 200 | Trả bản tốt nhất kèm cảnh báo |
| `PROVIDER_TIMEOUT` | 504 | Nhà cung cấp quá hạn |

**Schema recipe YAML (rút gọn)**

```yaml
id: open_eyes
version: 1
steps:
  - detect: { faces: true, eyes_ear: true }
  - filter: { only_closed_eyes: true, ear_below: 0.2 }
  - edit:   { provider: inpaint_face, strength: 0.5, padding: 0.3 }
  - blend:  { method: feather, radius_px: 8 }
  - qa:
      ear_min: 0.2
      identity_cosine_min: 0.85
      outside_mask_ssim_min: 0.98
retry: { max: 2, strength_step: -0.1, reseed: true }
prompt: { vi: prompts/open_eyes.vi.md, en: prompts/open_eyes.en.md }
```

*(Các ngưỡng là giá trị khởi đầu; hiệu chỉnh bằng golden set, ghi lại trong `PROGRESS.md`.)*

## 7. Test plan

| Tầng | Công cụ | Nội dung | Tiêu chí |
|---|---|---|---|
| Unit | pytest, vitest | EAR, SSIM, mask dilate/feather, recipe parser, validators | Coverage lõi ≥ 80% |
| Integration | pytest + docker-compose | API → queue → worker (provider mock) → kết quả | Job đầu-cuối pass; job lỗi không treo worker |
| Golden/Regression | Script QA | ≥ 20 ảnh/chức năng, `expected.json` | QA pass ≥ 90%; CI chặn merge khi giảm |
| E2E | Playwright | Upload → chọn chức năng → chạy → trước/sau → tải | Luồng chính pass ở viewport 380px |
| Hiệu năng | Locust/k6 | 50 job đồng thời, ảnh 12MP | p95 thời gian/job và chi phí/job được ghi lại |
| Bảo mật | Bandit, pip-audit, npm audit, ZAP | Upload độc, IDOR, injection | Không còn lỗi mức cao |
| Lỗi/biên | pytest | Không có mặt, ảnh nhóm, mặt nhỏ, đeo kính, EXIF xoay, PNG alpha, ảnh quá lớn/nhỏ | Báo lỗi rõ, không crash |

**Golden set — cấu trúc:** `tests/golden/<recipe_id>/images/*.jpg` và `expected.json` (nhãn, vùng mong đợi, ngưỡng). Phủ đủ: ánh sáng khác nhau, tông da khác nhau, ảnh nhóm, ảnh góc nghiêng.

**Ma trận QA:**

| Chỉ số | Ngưỡng khởi đầu |
|---|---|
| `identity_cosine` | ≥ 0.85 (hiệu chỉnh) |
| `outside_mask_ssim` | ≥ 0.98 |
| `ear` (mắt mở) | ≥ 0.20 |
| `clip_ratio` | < 1% pixel |
| `delta_e_skin` | ≤ ngưỡng đặt trong YAML |
| `ocr_recheck` | Không còn chữ watermark |
| `person_recheck` | Không còn người trong vùng xóa |

## 8. Checklist bảo mật & riêng tư

**Upload & dữ liệu**
- [ ] Kiểm tra magic bytes, không tin `Content-Type`; whitelist JPEG/PNG/WebP
- [ ] Giới hạn kích thước/độ phân giải; chống decompression bomb
- [ ] Xóa metadata (EXIF GPS) ở bản kết quả
- [ ] Quét/sandbox xử lý ảnh; worker chạy quyền thấp, không có mạng ngoài trừ provider đã khai báo
- [ ] Ảnh gốc bất biến; TTL tự xóa (ảnh + mask + kết quả)

**Truy cập**
- [ ] Xác thực mọi endpoint (trừ `/healthz`); kiểm tra quyền sở hữu asset/job (chống IDOR)
- [ ] Presigned URL ngắn hạn, một mục đích
- [ ] Rate limit theo user/IP; giới hạn job đồng thời
- [ ] CORS whitelist; CSRF nếu dùng cookie

**Bí mật & hạ tầng**
- [ ] API key trong secret manager/biến môi trường, không commit; bật secret scanning
- [ ] Mã hóa lưu trữ và truyền tải (TLS)
- [ ] Quét phụ thuộc định kỳ; ghim phiên bản; image Docker tối thiểu
- [ ] Backup DB, kiểm thử khôi phục

**Riêng tư**
- [ ] Không log nội dung ảnh/khuôn mặt/embedding; chỉ log metadata
- [ ] Không gửi ảnh ra dịch vụ ngoài chưa khai báo; liệt kê provider trong chính sách riêng tư
- [ ] Không train trên dữ liệu người dùng
- [ ] Cho phép xóa dữ liệu theo yêu cầu

**Lạm dụng**
- [ ] `remove_watermark`: bắt buộc `ownership_confirmed=true` + ghi `audit_logs` (user, job, thời gian, IP băm)
- [ ] Cảnh báo rõ khi người dùng xác nhận; từ chối nếu thiếu
- [ ] Giám sát mẫu lạm dụng bất thường

## 9. Mẫu báo cáo

**9.1 Báo cáo QA mỗi job** (`qa_report` JSON, xem §6) — lưu trong `qa_reports`.

**9.2 Báo cáo chạy golden set** (`docs/reports/golden-<recipe>-<ngày>.md`)

```md
# Golden report: open_eyes — 2026-10-16
- Phiên bản recipe/prompt/model: ...
- Số ảnh: 20 | Pass: 19 (95%) | Fail: 1
- Trung bình: identity 0.91, ear 0.26, outside_ssim 0.990
- Thời gian p50/p95: 6s / 11s | Chi phí/job: $0.0x
- Ảnh fail: img_07 (mặt nghiêng) — nguyên nhân, đề xuất
- So với lần trước: +/- ...
```

**9.3 Báo cáo cuối giai đoạn** (`docs/reports/phase-Px.md`): việc xong, chỉ số đạt, rủi ro, quyết định, việc chuyển tiếp.

**9.4 `PROGRESS.md`:** dùng mẫu ở §8 của AGENT_SKILLS.

## 10. Lộ trình từng bước (làm gì, làm theo thứ tự)

### P0 — Nền móng (không có AI thật)
1. Tạo repo theo cấu trúc §3; khởi tạo `PROGRESS.md`, `docs/` và các file trống.
2. Thiết lập CI: lint, type-check, pytest, vitest, secret scan.
3. Viết `recipe_schema.py` (Pydantic) + test parser với YAML mẫu.
4. Viết `providers/base.py` + `mock.py` (trả ảnh giả có thể kiểm chứng).
5. Viết Recipe Runner (S1): detect → filter → edit → blend → qa, có retry; test bằng mock.
6. Dựng DB + migration theo ERD §4; repository và service cơ bản.
7. Dựng API tối thiểu: presign, tạo job, xem job (§6); queue + worker chạy job mock.
8. Viết module QA khung (`report.py`) và test; docker-compose chạy toàn bộ.
9. **Xong khi:** gửi job mock đầu-cuối, CI xanh, báo cáo P0.

### P1 — Chức năng dễ đo trước (S3, S5, S6, S11)
1. Detector mặt + EAR (S3); golden set mắt nhắm/mở; đạt ≥ 95%.
2. Đo QA: `outside_mask_ssim`, `identity_cosine`, `lpips`.
3. Chức năng 4 `open_eyes` (detect → mask mắt → inpaint → blend → QA).
4. Chức năng 6 `remove_bystanders` (S4 chọn chủ thể chính + LaMa + `person_recheck`).
5. Chức năng 5 `remove_watermark` (OCR/logo detect + inpaint + `ocr_recheck` + cờ sở hữu + audit log).
6. Chức năng 1 `upscale_4k` (SR tile + giới hạn cạnh dài 8192).
7. Với mỗi chức năng: YAML + prompt vi/en + golden ≥ 20 ảnh + báo cáo golden.

### P2 — Chân dung & màu (S7, S8)
1. Face parsing + tách tần số → chức năng 2 `skin_retouch`; đo `delta_e_skin`, phương sai kết cấu.
2. Chức năng 3 `chin_fix` (crop nhỏ, strength thấp, kiểm danh tính nghiêm).
3. Màu: white balance, tone mapping cục bộ → chức năng 9 `low_light_fix`.
4. Chức năng 8 `golden_hour` (relight mềm, kiểm `clip_ratio`).

### P3 — Chức năng phức tạp (S9, S10)
1. Chức năng 7: phân loại ảnh → mask hư hại → inpaint → khử nhiễu → khôi phục mặt → tô màu (tùy chọn, có công tắc) → upscale.
2. Chức năng 10: tách nền → nền studio → bóng/phản chiếu → khớp màu → grade; kiểm hình dáng/logo/màu.
3. **Mâu thuẫn chưa giải quyết:** yêu cầu "Full HD 32k" ở chức năng 7 — phải hỏi người dùng chốt độ phân giải mục tiêu trước khi làm (AGENT_SKILLS §2.9).

### P4 — Sản phẩm hóa
1. Frontend (S14): lưới 10 chức năng, upload, canvas mask, chạm chọn chủ thể, slider trước/sau, panel QA; đọc skill `frontend-design` trước khi dựng.
2. Playwright cho luồng chính ở 380px; Lighthouse PWA.
3. Hạ tầng (S15): GPU worker, secret manager, mã hóa, TTL, audit.
4. Chạy test hiệu năng và bảo mật (§7, §8); xử lý hết lỗi mức cao.
5. Ghi nhận chi phí/độ trễ từng chức năng; chốt provider chính theo chi phí/chất lượng.
6. Báo cáo phát hành + chính sách riêng tư.

## 11. Checklist "Xong" tổng

- [ ] 10 recipe YAML + prompt `.vi.md` / `.en.md`, ràng buộc gốc không bị làm yếu
- [ ] Mỗi chức năng: QA đủ chỉ số, golden ≥ 20 ảnh, pass ≥ 90%
- [ ] Xử lý lỗi biên không crash
- [ ] API khớp §6, có test tích hợp
- [ ] ERD đã migrate, có chỉ mục và ràng buộc
- [ ] Checklist bảo mật §8 đánh dấu hết
- [ ] UI đầy đủ luồng + trước/sau, dùng tốt ở ~380px
- [ ] Đã ghi phiên bản model/provider, chi phí và thời gian mỗi job
- [ ] `PROGRESS.md` và báo cáo từng giai đoạn cập nhật

## 12. Câu hỏi cần bạn chốt

1. Độ phân giải mục tiêu của phục chế ảnh cũ (thay cho "Full HD 32k")?
2. Provider chỉnh sửa chính: ưu tiên chi phí hay chất lượng?
3. Triển khai đám mây hay tự host GPU?
4. Cần đăng nhập/tài khoản ngay, hay bản đầu ẩn danh có TTL?
