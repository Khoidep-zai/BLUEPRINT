# PROGRESS
## Giai đoạn hiện tại: P1
## Đã xong
- [x] P0: Đọc AGENT_SKILLS.md và PHOTO_AI_SYSTEM_DESIGN.md (gốc dự án ở `photo-ai/`)
- [x] P0: Repo theo cấu trúc §3 (gốc `photo-ai/`), PROGRESS.md, docs/
- [x] P0: providers/{base,mock,registry}.py (S2 Provider Adapter, mock provider)
- [x] P0: pipeline/{recipe_schema,context,errors,loader,retry,runner}.py + steps/ (S1 Recipe Runner)
- [x] P0: detectors/{face,eyes_ear,person,text_logo}.py
- [x] P0: editors/{upscale,inpaint,relight,color,retouch,restore,studio}.py
- [x] P0: qa/{identity,ssim,lpips,ocr_recheck,person_recheck,skin_color,clip_ratio,report}.py (S11)
- [x] P0: masking.py, io/, workers/main.py
- [x] P0: apps/api/ (FastAPI + ERD models/repositories/services/schemas/security + API contract §6)
- [x] P0: recipes/open_eyes.yaml + prompts/open_eyes.{vi,en}.md
- [x] P0: 47 unit tests pass; docs/reports/phase-P0.md

## Đang làm
- [ ] P1: Detector mặt + EAR (S3); golden set mắt nhắm/mở ≥ 95%

## Quyết định đã chốt
- Provider mặc định P0: mock:v1
- Upscale tối đa cạnh dài 8192px
- Gốc dự án: `photo-ai/` (theo blueprint §3)

## Câu hỏi cho người dùng (chưa chốt — cần trả lời trước P3 chức năng 7)
1. Độ phân giải mục tiêu của phục chế ảnh cũ (thay cho "Full HD 32k")?
2. Provider chỉnh sửa chính: ưu tiên chi phí hay chất lượng?
3. Triển khai đám mây hay tự host GPU?
4. Cần đăng nhập/tài khoản ngay, hay bản đầu ẩn danh có TTL?

## Phiên bản model đang dùng
- mock:v1 (P0, chưa chọn provider thật)
