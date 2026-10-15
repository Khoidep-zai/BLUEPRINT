# PROGRESS
## Giai đoạn hiện tại: P1
## Đã xong
- [x] P0: Đọc AGENT_SKILLS.md và PHOTO_AI_SYSTEM_DESIGN.md
- [x] P0: Tạo repo theo cấu trúc §3; PROGRESS.md, docs/
- [x] P0: providers/base.py + mock.py + registry.py (S2)
- [x] P0: pipeline/recipe_schema.py (Pydantic) + test
- [x] P0: pipeline/context.py, retry.py, runner.py (S1 Recipe Runner) + test
- [x] P0: qa/report.py (S11)
- [x] P0: FastAPI app + job service (in-memory) + smoke test
- [x] P0: 7 unit/integration tests pass; báo cáo phase-P0.md

## Đang làm
- [ ] P1: Detector mặt + EAR (S3); golden set mắt nhắm/mở ≥ 95%

## Quyết định đã chốt
- Upscale tối đa cạnh dài 8192px
- Provider mặc định P0: mock:v1
- Job service in-memory ở P0; DB (Postgres/SQLAlchemy) ở P1

## Câu hỏi cho người dùng
- Độ phân giải mục tiêu của phục chế ảnh cũ (thay cho "Full HD 32k")?
- Provider chỉnh sửa chính: ưu tiên chi phí hay chất lượng?
- Triển khai đám mây hay tự host GPU?
- Cần đăng nhập/tài khoản ngay, hay bản đầu ẩn danh có TTL?

## Phiên bản model đang dùng
- mock:v1 (P0, chưa chọn provider thật)
