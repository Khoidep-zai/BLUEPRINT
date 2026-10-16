---
name: spec-driven-development
description: "Đặc tả kỹ thuật trước khi viết code (/spec), lập tài liệu yêu cầu, xác định các trường hợp biên, bất biến hệ thống và bộ chỉ số nghiệm thu."
---

# Spec-Driven Development Skill (Đặc Tả Trước Khi Viết Code)

Nguyên tắc vàng: **Không bao giờ viết code khi chưa có bản đặc tả kỹ thuật rõ ràng.** Áp dụng cho mọi tính năng mới, tái cấu trúc thuật toán CV, nâng cấp pipeline hoặc chỉnh sửa giao diện trong Photo AI Desktop.

## 1. Mẫu Đặc Tả Tính Năng (Technical Spec Template)

Mọi đề xuất kỹ thuật cần được định hình ngắn gọn qua 5 mục:

1. **Mục tiêu & Nghiệp vụ (Objective & Domain Value):**
   - Người dùng giải quyết được vấn đề gì? (Ví dụ: nạp ảnh JFIF, xuất PNG/JPG, chỉnh góc mặt).
2. **Bất biến hệ thống (System Invariants to Preserve):**
   - 100% offline? Giữ nguyên ảnh gốc? VRAM $\le 2$ models? Luôn xuất PNG/JPG?
3. **Thiết kế API / Dữ liệu (Interface & Data Contracts):**
   - Tên hàm, tham số, kiểu dữ liệu (`Image.Image`, `np.ndarray`, `Path`).
   - Đầu vào nhận dạng những định dạng nào, đầu ra trả về gì.
4. **Trường hợp biên & Xử lý lỗi (Edge Cases & Fallbacks):**
   - Ảnh không có mặt người? Ảnh quá nhỏ hoặc quá lớn 8K? File hỏng EXIF? Không có GPU?
5. **Tiêu chuẩn kiểm thử (Acceptance Criteria & Test Plan):**
   - Chỉ số QA đo lường (`SSIM`, `Identity`, `Delta-E`).
   - Các bài test unit và integration cần chạy.

## 2. Quy Tắc Giữ Gìn Single Source of Truth
- Mọi sửa đổi kiến trúc lớn phải được đồng bộ cập nhật vào `PHOTO_AI_SYSTEM_DESIGN.md` và `PROGRESS.md`.
