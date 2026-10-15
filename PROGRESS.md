# PROGRESS
## Giai đoạn hiện tại: P1
## Đã xong
- [x] P0: Đọc AGENT_SKILLS.md và PHOTO_AI_SYSTEM_DESIGN.md (gốc dự án ở `C:\O E\Blueprint\`)
- [x] P0: Repo theo cấu trúc §3, PROGRESS.md, docs/
- [x] P0: providers/{base,mock,registry}.py (S2 Provider Adapter, mock provider)
- [x] P0: pipeline/{recipe_schema,context,errors,loader,retry,runner}.py + steps/ (S1 Recipe Runner)
- [x] P0: detectors/{face,eyes_ear,person,text_logo}.py — P1: nâng cấp OpenCV-based với fallback an toàn
- [x] P0: editors/{upscale,inpaint,relight,color,retouch,restore,studio}.py
- [x] P0: qa/{identity,ssim,lpips,ocr_recheck,person_recheck,skin_color,clip_ratio,report}.py (S11)
- [x] P0: masking.py, io/, workers/main.py
- [x] P0: src/backend/ (FastAPI + in-memory store, loại bỏ SQLAlchemy/Postgres theo yêu cầu)
- [x] P0: src/frontend/ (Next.js placeholder, ko cần đăng nhập)
- [x] P0: recipes/open_eyes.yaml + prompts/open_eyes.{vi,en}.md
- [x] P0: 47 unit tests pass; docs/reports/phase-P0.md
- [x] P1: 10 recipe + prompt chi tiết theo yêu cầu người dùng (10 chức năng)
- [x] P1: detectors nâng cấp OpenCV (face, eyes_ear, person, text_logo)
- [x] P1: golden set structure (tests/golden/)
- [x] P1: 5 integration tests cho 4 chức năng (open_eyes, remove_bystanders, remove_watermark, upscale_4k)
- [x] P1: 52/52 tests pass

## Đang làm
- [ ] P1: Xác nhận pipeline end-to-end cho 4 chức năng P1 qua API (src/backend)
- [ ] P2-P4: các chức năng còn lại (skin_retouch, chin_fix, restore_old_photo, golden_hour, low_light_fix, product_studio)

## Quyết định đã chốt (theo yêu cầu người dùng)
- Độ phân giải mục tiêu phục chế ảnh cũ: **Full HD 4K** (thay "Full HD 32k")
- Provider chỉnh sửa chính: **ưu tiên chất lượng**
- Triển khai: **tự host CPU**, ưu tiên viết nhẹ, nhanh, tốt, đạt chất lượng
- Giao diện app: **ko cần đăng nhập**, chỉ cần app có giao diện
- **Không dùng Migration DB / Postgres / SQLAlchemy** — luồng đơn giản: chọn chức năng → upload ảnh → xử lý → xuất output (in-memory store)
- Stack: **Python** (FastAPI backend, pytest, OpenCV, Pillow, numpy) — không dùng Java
- Upscale tối đa cạnh dài: 8192px
- Gốc dự án: `. (gốc dự án)` (theo blueprint §3)

## Câu hỏi đã được người dùng trả lời (đã chốt)
1. Độ phân giải mục tiêu phục chế ảnh cũ: Full HD 4K ✅
2. Provider chỉnh sửa chính: ưu tiên chất lượng ✅
3. Triển khai: tự host CPU ✅
4. Giao diện: ko cần đăng nhập ✅

## Phiên bản model đang dùng
- mock-1 (P0/P1, chưa chọn provider thật)
