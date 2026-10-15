# Báo cáo giai đoạn P0 — Nền móng (Photo AI Tool)

## Việc đã làm
- Khởi tạo repo theo cấu trúc `AGENT_SKILLS.md §3` / `PHOTO_AI_SYSTEM_DESIGN.md §3` (gốc dự án ở `photo-ai/`).
- `providers/base.py` + `mock.py` + `registry.py` (S2 Provider Adapter, mock provider).
- `workers/src/photoai_worker/pipeline/recipe_schema.py` — Pydantic schema cho recipe YAML.
- `workers/src/photoai_worker/pipeline/context.py`, `errors.py`, `loader.py`, `retry.py`, `runner.py` — Recipe Runner S1 (detect→filter→edit→blend→qa + retry + best-effort).
- `workers/src/photoai_worker/pipeline/steps/{detect,filter,edit,blend,qa}.py` — các bước pipeline.
- `workers/src/photoai_worker/detectors/{face,eyes_ear,person,text_logo}.py` — bộ detectors.
- `workers/src/photoai_worker/editors/{upscale,inpaint,relight,color,retouch,restore,studio}.py` — bộ editors.
- `workers/src/photoai_worker/qa/{identity,ssim,lpips,ocr_recheck,person_recheck,skin_color,clip_ratio,report}.py` — QA modules (S11).
- `workers/src/photoai_worker/masking.py`, `io/` — mask & lưu trữ.
- `apps/api/src/photoai_api/` — FastAPI app đầy đủ theo ERD §4 (models, repositories, services, schemas, security, db, deps, errors) + API contract §6.
- Sample recipe `recipes/open_eyes.yaml` + prompts `open_eyes.vi.md` / `.en.md`.
- 47 unit tests pass (pytest).

## Kết quả chạy thử (mock)
- Pipeline mock chạy đầu-cuối, trả `qa_report.passed=true`.
- Xóa watermark without `ownership_confirmed=true` → báo lỗi/từ chối (rule #8).
- Thời gian chạy job mock < 1s, chi phí $0 (mock).

## Quyết định đã chốt
- Provider mặc định P0: `mock:v1`.
- Upscale tối đa cạnh dài 8192px.
- Job service theo ERD §4 (Postgres/SQLAlchemy sẵn sàng migrate).

## Câu hỏi còn mở (chờ người dùng chốt)
1. Độ phân giải mục tiêu của phục chế ảnh cũ (thay cho "Full HD 32k")?
2. Provider chỉnh sửa chính: ưu tiên chi phí hay chất lượng?
3. Triển khai đám mây hay tự host GPU?
4. Cần đăng nhập/tài khoản ngay, hay bản đầu ẩn danh có TTL?

## Sang P1
- Detector mặt + EAR (S3) → golden set mắt nhắm/mở ≥ 95%.
- Chức năng 4 `open_eyes`, 6 `remove_bystanders`, 5 `remove_watermark`, 1 `upscale_4k`.
- Migration DB theo ERD; repository và service thực.
