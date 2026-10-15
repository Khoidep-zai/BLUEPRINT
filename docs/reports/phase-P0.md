# Báo cáo giai đoạn P0 — Nền móng (Photo AI Tool)

## Việc đã làm
- Khởi tạo repo theo cấu trúc `AGENT_SKILLS.md §3` / `PHOTO_AI_SYSTEM_DESIGN.md §3`.
- `providers/base.py` + `mock.py` + `registry.py` (S2 Provider Adapter, mock provider).
- `workers/src/photoai_worker/pipeline/recipe_schema.py` — Pydantic schema cho recipe YAML.
- `workers/src/photoai_worker/pipeline/context.py`, `retry.py`, `runner.py` — Recipe Runner S1 (detect→filter→edit→blend→qa + retry).
- `workers/src/photoai_worker/qa/report.py` — QA report module (S11).
- `apps/api/src/photoai_api/` — FastAPI app: `POST /v1/jobs`, `GET /v1/jobs/{id}`, `GET /v1/jobs/{id}/result`, `GET /healthz`, `GET /v1/recipes`, watermark ownership guard (403).
- In-memory job service (P0) chạy recipe inline với mock provider.
- Sample recipe `recipes/open_eyes.yaml` + prompts `open_eyes.vi.md` / `.en.md`.
- 7 unit/integration tests pass (pytest).

## Kết quả chạy thử (mock)
- `POST /v1/jobs` → job chạy pipeline mock, trả `status=done`, `qa_report.passed=true`.
- Xóa watermark without `ownership_confirmed=true` → HTTP 403.
- Thời gian chạy job mock < 1s, chi phí $0 (mock).

## Quyết định đã chốt
- Provider mặc định P0: `mock:v1`.
- Upscale tối đa cạnh dài 8192px.
- Job service in-memory ở P0; sẽ thay bằng DB (Postgres/SQLAlchemy) ở P1.

## Câu hỏi còn mở (chờ người dùng chốt)
1. Độ phân giải mục tiêu của phục chế ảnh cũ (thay cho "Full HD 32k")?
2. Provider chỉnh sửa chính: ưu tiên chi phí hay chất lượng?
3. Triển khai đám mây hay tự host GPU?
4. Cần đăng nhập/tài khoản ngay, hay bản đầu ẩn danh có TTL?

## Sang P1
- Detector mặt + EAR (S3) → golden set mắt nhắm/mở ≥ 95%.
- Chức năng 4 `open_eyes`, 6 `remove_bystanders`, 5 `remove_watermark`, 1 `upscale_4k`.
- DB + migration theo ERD §4; repository và service.
