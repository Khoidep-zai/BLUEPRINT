---
name: security-and-audit-logs
description: "Kiểm soát an toàn thông tin, bảo vệ quyền riêng tư 100% offline, hộp thoại xác nhận quyền sở hữu ảnh (Ownership Confirmation) và ghi nhật ký kiểm toán SQLite (Audit Trail)."
---

# Security & Audit Logs Skill (An Toàn Thông Tin & Nhật Ký Kiểm Toán)

Kỹ năng kiểm soát rủi ro bảo mật, quyền riêng tư dữ liệu cá nhân (PII) và tuân thủ đạo đức khi chỉnh sửa ảnh AI trên Photo AI Desktop.

## 1. Nguyên Tắc An Toàn Dữ Liệu Ngoại Tuyến
- **Không Rò Rỉ Dữ Liệu (Zero Data Exfiltration):** Ứng dụng chạy hoàn toàn cô lập trên máy người dùng. Không có socket lén lút, không có webhook ra ngoài.
- **Xóa Dấu Vết Tạm Thời (Workspace TTL):**
  - Mọi ảnh trung gian trong `workspace/cache/` được dọn dẹp theo thời gian định kỳ (`CACHE_TTL_HOURS = 24`).
  - Hàm `purge_expired_cache()` tự động xóa các file tạm hết hạn mà không ảnh hưởng tới ảnh kết quả đã xuất.

## 2. Kiểm Soát Quyền Sở Hữu Khi Xóa Watermark (`remove_watermark`)
- Việc xóa logo, chữ ký, watermark bản quyền tiềm ẩn rủi ro xâm phạm quyền tác giả.
- **Ràng Buộc Nghiệp Vụ:**
  - Thuộc tính `ownership_required: true` được khai báo trong `recipes/remove_watermark.yaml`.
  - Cửa sổ giao diện bắt buộc bật `WatermarkDialog` yêu cầu người dùng xác nhận: *"Tôi có quyền hợp pháp hoặc sự đồng ý của tác giả để chỉnh sửa bức ảnh này"*.
  - Nếu người dùng bấm Hủy hoặc không tích chọn: Pipeline từ chối thực thi và trả về lỗi `OwnershipError`.
  - Nếu xác nhận: Bắt buộc ghi nhận sự kiện vào bảng `audit_logs` trong cơ sở dữ liệu SQLite (`db.py`):
    ```sql
    INSERT INTO audit_logs (id, event, details, created_at)
    VALUES (?, 'watermark_removal_confirmed', ?, ?);
    ```
