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
- [ ] P1: Nhập yêu cầu chi tiết 10 chức năng vào recipes/prompts; Detector mặt + EAR (S3); golden set mắt nhắm/mở ≥ 95%

## Quyết định đã chốt (theo yêu cầu người dùng)
- Độ phân giải mục tiêu phục chế ảnh cũ: **Full HD 4K** (thay cho "Full HD 32k")
- Provider chỉnh sửa chính: **ưu tiên chất lượng**
- Triển khai: **tự host CPU**, ưu tiên viết nhẹ, nhanh, tốt, đạt chất lượng
- Giao diện app: **ko cần đăng nhập**, chỉ cần tạo ra app có giao diện
- Provider mặc định P0: mock:v1
- Stack: **Python** (FastAPI, pytest, OpenCV, Pillow, numpy) — không dùng Java
- Upscale tối đa cạnh dài: 8192px (P0), mở ra 4K cho P1+
- Gốc dự án: `photo-ai/` (theo blueprint §3)

## Câu hỏi đã được người dùng trả lời (đã chốt)
1. Độ phân giải mục tiêu phục chế ảnh cũ: Full HD 4K ✅
2. Provider chỉnh sửa chính: ưu tiên chất lượng ✅
3. Triển khai: tự host CPU ✅
4. Giao diện: ko cần đăng nhập ✅

## Phiên bản model đang dùng
- mock:v1 (P0, chưa chọn provider thật)
