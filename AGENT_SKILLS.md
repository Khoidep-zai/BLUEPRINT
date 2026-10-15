# AGENT_SKILLS.md — Hướng dẫn cho AI Agent xây dựng Photo AI Tool

> **Đọc file này đầu tiên, mỗi phiên làm việc.** Sau đó đọc `BLUEPRINT.md` (bản vẽ). File này cho biết *bạn là ai, làm theo quy trình nào, cần kỹ năng gì, và thế nào là "xong"*.

---

## 0. Vai trò & mục tiêu

Bạn là kỹ sư full-stack + ML đang xây **Photo AI Tool** gồm 10 chức năng chỉnh ảnh (xem `BLUEPRINT.md` §4). Mục tiêu: sản phẩm chạy được, mỗi chức năng **giữ nguyên danh tính/bố cục** và vượt ngưỡng QA.

## 1. Quy trình mỗi phiên (bắt buộc)

1. Đọc `AGENT_SKILLS.md` và `BLUEPRINT.md`.
2. Đọc `PROGRESS.md` (nếu chưa có thì tạo) để biết đang ở giai đoạn P0–P4 nào.
3. Chọn **một** nhiệm vụ nhỏ theo thứ tự lộ trình (BLUEPRINT §8). Không nhảy giai đoạn.
4. Viết test trước/cùng lúc → code → chạy test → cập nhật `PROGRESS.md`.
5. Commit nhỏ, thông điệp rõ: `feat(open_eyes): add EAR detector`.
6. Cuối phiên: ghi lại việc đã làm, việc dở dang, quyết định đã chốt, câu hỏi cần người dùng.

## 2. Quy tắc bất biến

1. **Không bao giờ ghi đè ảnh gốc.**
2. **Không sửa/cắt ràng buộc trong prompt** của người dùng (các câu "không đổi khuôn mặt…", "chỉ sửa…"). Chỉ được thêm bản dịch tiếng Anh, không làm yếu đi.
3. **Ràng buộc phải đo được:** mọi chức năng có bước QA bằng số (BLUEPRINT §4). Không có QA = chưa xong.
4. **Recipe-driven:** thêm/sửa chức năng bằng file YAML trong `recipes/`, không hard-code trong lõi.
5. **Provider adapter:** không gọi trực tiếp SDK của nhà cung cấp ngoài `providers/`.
6. **Riêng tư:** không log nội dung ảnh/khuôn mặt, không gửi ảnh tới dịch vụ ngoài khi chưa khai báo; ảnh có TTL tự xóa.
7. **Chức năng xóa watermark:** bắt buộc cờ `ownership_confirmed=true` + ghi `audit_logs`.
8. **Không bịa số liệu/model:** trước khi chọn model/phiên bản/API, kiểm tra tài liệu hiện hành; ghi lại phiên bản đã dùng.
9. **Gặp mâu thuẫn trong yêu cầu** (ví dụ "Full HD 32k" ở chức năng 7): dừng, đề xuất phương án, hỏi người dùng; không tự đoán.
10. Mọi bí mật (API key) nằm trong biến môi trường, không commit.

## 3. Cấu trúc dự án chuẩn

```
photo-ai/
├─ apps/
│  ├─ web/                # Next.js + TS + Tailwind (PWA)
│  └─ api/                # FastAPI
├─ workers/
│  ├─ pipeline/           # recipe runner, steps
│  ├─ detectors/          # face, eyes(EAR), person, text/logo
│  ├─ editors/            # upscale, inpaint, relight, color
│  └─ qa/                 # identity, ssim, lpips, ocr_recheck
├─ providers/             # ImageEditProvider adapters
├─ recipes/               # 10 file YAML
├─ prompts/               # <id>.vi.md + <id>.en.md
├─ tests/
│  ├─ golden/             # ảnh mẫu + kỳ vọng
│  └─ unit/
├─ infra/                 # docker-compose, k8s, CI
├─ AGENT_SKILLS.md
├─ BLUEPRINT.md
└─ PROGRESS.md
```

## 4. Bộ kỹ năng (Skills)

Mỗi skill: **Khi nào dùng → Cách làm → Xong khi**.

### S1. Recipe Runner
- **Dùng khi:** xây lõi thực thi chức năng.
- **Làm:** parse YAML (Pydantic) → chạy tuần tự `detect → filter → edit → blend → qa`; hỗ trợ retry, ghi `qa_report` JSON.
- **Xong khi:** chạy được recipe mẫu với provider giả (mock) và test pass.

### S2. Provider Adapter
- **Dùng khi:** gọi model ngoài/nội bộ.
- **Làm:** interface `edit(image, mask?, prompt, strength, seed) -> image`; có timeout, retry có backoff, đo chi phí/độ trễ, đổi provider chỉ bằng cấu hình.
- **Xong khi:** ≥ 2 provider (1 mock + 1 thật) dùng cùng interface.

### S3. Face & Eye Detection
- **Dùng khi:** chức năng 2, 3, 4, 8.
- **Làm:** detect mặt + landmark; tính EAR `(|p2−p6|+|p3−p5|)/(2|p1−p4|)`; ngưỡng mặc định ~0.18–0.2, điều chỉnh bằng golden set; xử lý ảnh nhóm (nhiều mặt, mặt nhỏ, nghiêng, đeo kính).
- **Xong khi:** phân biệt đúng nhắm/mở ≥ 95% trên golden set.

### S4. Mask & Segmentation
- **Dùng khi:** chức năng 4, 5, 6, 10, 8.
- **Làm:** SAM/segmentation người; chọn "chủ thể chính" (lớn nhất + gần tâm + cho phép người dùng chạm chọn); dilate/feather mask; hợp nhất mask người dùng vẽ + mask tự động.
- **Xong khi:** mask không cắt vào chủ thể chính; có test với ảnh đông người.

### S5. Inpainting
- **Dùng khi:** xóa watermark, xóa người, sửa mắt, xóa trầy xước.
- **Làm:** chọn LaMa cho vật thể lớn/hậu cảnh; diffusion inpaint cho chi tiết mặt; crop quanh vùng + padding, xử lý, ghép lại bằng feather/Poisson; giữ độ phân giải gốc.
- **Xong khi:** SSIM ngoài mask ≥ 0.98 và đường ghép không thấy viền.

### S6. Super-Resolution & Face Restoration
- **Dùng khi:** chức năng 1, 2, 7.
- **Làm:** SR theo tile (chống tràn VRAM, tránh đường nối); khôi phục mặt chỉ trên vùng mặt với fidelity cao để giữ danh tính; giới hạn kích thước đầu ra (mặc định cạnh dài ≤ 8192).
- **Xong khi:** không "tưởng tượng chi tiết" (kiểm bằng so sánh cấu trúc), ArcFace ≥ ngưỡng.

### S7. Skin Retouch (tách tần số)
- **Dùng khi:** chức năng 2.
- **Làm:** face parsing → mask da → tách tần số thấp/cao → làm mịn tần số thấp, giữ tần số cao; xóa mụn bằng spot-inpaint; giữ tông da (ΔE nhỏ).
- **Xong khi:** không còn hiệu ứng "da nhựa" (phương sai kết cấu không giảm quá ngưỡng).

### S8. Lighting & Color Science
- **Dùng khi:** chức năng 8, 9, 10, 7.
- **Làm:** white balance (gray-world/learned), trung hòa ám màu, tone mapping cục bộ, giảm bóng gắt flash, relight mềm; làm việc trong không gian màu rõ ràng (sRGB/Lab), kiểm clip highlight.
- **Xong khi:** không cháy sáng (<1% pixel clip), ΔE tông da trong ngưỡng, bố cục không đổi.

### S9. Old Photo Restoration
- **Dùng khi:** chức năng 7.
- **Làm:** phân loại ảnh (đen trắng/sepia/phim/mờ) → mask hư hại → inpaint → khử nhiễu giữ hạt → khôi phục mặt → tô màu (tùy chọn) đúng thời kỳ → upscale.
- **Xong khi:** ảnh mất hư hại nhưng vẫn giữ "chất" thời kỳ; người dùng có công tắc bật/tắt tô màu.

### S10. Product Studio Compositing
- **Dùng khi:** chức năng 10.
- **Làm:** tách nền → dựng nền studio → bóng đổ mềm + phản chiếu bề mặt → khớp màu/ánh sáng → grade sang trọng.
- **Xong khi:** hình dáng, logo, chữ trên sản phẩm giữ nguyên; màu lệch < ngưỡng.

### S11. QA & Evaluation
- **Dùng khi:** mọi chức năng (bắt buộc).
- **Làm:** triển khai các đo lường:
  - `identity_cosine` (ArcFace/InsightFace)
  - `outside_mask_ssim`
  - `lpips` / `structure_similarity` (bố cục)
  - `ear` (mắt)
  - `ocr_recheck` (còn chữ watermark không)
  - `person_recheck` (còn người trong vùng xóa không)
  - `delta_e_skin`, `clip_ratio`
  Trả `qa_report` JSON; nếu fail → retry (giảm strength, đổi seed) tối đa 2 lần → trả bản tốt nhất kèm cảnh báo.
- **Xong khi:** CI chạy golden set và chặn merge khi chất lượng giảm.

### S12. Prompt Engineering
- **Dùng khi:** viết/sửa prompt cho provider.
- **Làm:** giữ bản gốc `.vi.md`; tạo `.en.md`; cấu trúc 3 phần **Mục tiêu / Ràng buộc / Cấm**; đặt ràng buộc ở đầu và lặp lại ở cuối; ghi seed + tham số; A/B trên golden set trước khi đổi.
- **Xong khi:** điểm QA không thấp hơn bản trước.

### S13. Backend API & Job Queue
- **Dùng khi:** xây API, worker.
- **Làm:** FastAPI + Pydantic; Celery/RQ + Redis; job idempotent; trạng thái `queued/running/qa/done/failed`; WebSocket/polling; presigned upload; rate limit; xóa dữ liệu theo TTL.
- **Xong khi:** gửi job → nhận kết quả đầu-cuối; có test tích hợp; job lỗi không làm treo worker.

### S14. Frontend (mobile-first)
- **Dùng khi:** xây UI.
- **Làm:** Next.js + Tailwind; lưới 10 chức năng; canvas tô mask (Konva/Fabric); chạm chọn chủ thể chính; slider trước/sau; hiển thị QA dễ hiểu; xử lý ảnh lớn (nén phía client trước khi upload nếu cần, nhưng giữ bản gốc).
- **Xong khi:** dùng thoải mái trên màn hình ~380px; Lighthouse PWA đạt; có test Playwright cho luồng chính.
- *Gợi ý:* đọc skill `frontend-design` (nếu có) trước khi dựng UI.

### S15. Infra, Security, Privacy
- **Dùng khi:** triển khai.
- **Làm:** Docker; GPU worker; secret manager; mã hóa lưu trữ; TTL xóa ảnh; audit log; giới hạn kích thước/định dạng upload (chống file độc); không train trên dữ liệu người dùng; chính sách riêng tư.
- **Xong khi:** checklist bảo mật được đánh dấu hết, quét phụ thuộc không còn lỗi mức cao.

## 5. Ma trận Chức năng → Skill

| # | Chức năng | Skill chính |
|---|---|---|
| 1 | Nâng cấp 4K | S6, S11 |
| 2 | Retouch da | S3, S7, S6, S11 |
| 3 | Sửa nọng cằm | S3, S2, S11, S12 |
| 4 | Cứu ảnh nhắm mắt | S3, S4, S5, S11 |
| 5 | Xóa watermark | S4, S5, S11, S15 |
| 6 | Xóa người hậu cảnh | S4, S5, S11 |
| 7 | Phục chế ảnh cũ | S9, S5, S6, S8, S11 |
| 8 | Chân dung giờ vàng | S3, S4, S8, S11 |
| 9 | Sửa ảnh thiếu sáng | S8, S3, S11 |
| 10 | Điện thoại → Studio | S4, S10, S8, S11 |

## 6. Định nghĩa "Xong" (Definition of Done) cho mỗi chức năng

- [ ] File `recipes/<id>.yaml` + `prompts/<id>.vi.md` + `prompts/<id>.en.md`
- [ ] Các bước detect/mask/edit/blend chạy được
- [ ] QA module đo đủ chỉ số của chức năng, ngưỡng nằm trong YAML
- [ ] Golden set ≥ 20 ảnh, tỉ lệ QA pass ≥ 90%
- [ ] Xử lý lỗi: không có mặt, không có mắt nhắm, ảnh quá nhỏ/lớn, định dạng lạ → thông báo rõ, không crash
- [ ] Thời gian xử lý & chi phí/job được đo và ghi lại
- [ ] UI có luồng đầy đủ + trước/sau
- [ ] Cập nhật `PROGRESS.md`

## 7. Xử lý tình huống thường gặp

| Tình huống | Hành động |
|---|---|
| Model làm đổi khuôn mặt | Giảm strength, crop vùng nhỏ hơn, đổi seed, dùng khôi phục mặt fidelity cao; nếu vẫn fail → trả bản gốc + cảnh báo |
| Hậu cảnh sau khi xóa người bị lặp họa tiết | Mở rộng mask hợp lý, dùng LaMa + tile, hoặc cho người dùng tô lại |
| Da bị mịn quá | Tăng trọng số tần số cao, giảm cường độ |
| Ảnh quá lớn gây OOM | Tiling, hạ độ chính xác (fp16), xử lý theo crop |
| Người dùng yêu cầu ngoài phạm vi 10 chức năng | Ghi vào backlog, không làm trong luồng hiện tại |
| Yêu cầu mơ hồ/mâu thuẫn | Dừng và hỏi người dùng, kèm đề xuất mặc định |

## 8. Mẫu `PROGRESS.md`

```md
# PROGRESS
## Giai đoạn hiện tại: P1
## Đã xong
- [x] P0: recipe runner, provider mock
## Đang làm
- [ ] upscale_4k: tiling SR (60%)
## Quyết định đã chốt
- Upscale tối đa cạnh dài 8192px
## Câu hỏi cho người dùng
- Chọn provider edit chính (chi phí vs chất lượng)?
## Phiên bản model đang dùng
- ...
```

## 9. Lệnh khởi động nhanh cho Agent

> "Hãy đọc `AGENT_SKILLS.md`, `BLUEPRINT.md` và `PROGRESS.md`. Xác định nhiệm vụ tiếp theo theo lộ trình, nêu kế hoạch ngắn (≤ 5 dòng), rồi thực hiện theo quy trình ở §1 và Definition of Done ở §6."
