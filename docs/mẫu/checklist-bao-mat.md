# Checklist bảo mật — Tự đánh giá phân hệ L2

Học phần: Chuyên đề Tốt nghiệp 1 (CDTN1) — Track SE  
Sinh viên: Nguyễn Bá Anh Khôi — MSSV: 2374802010247  

Bảng tự đánh giá 7 mục bắt buộc của Bài tập 3 theo rubric Khoa CNTT ĐH Văn Lang:

| # | Mục kiểm tra | Kết quả | Minh chứng thực tế trong mã nguồn |
|---|---|---|---|
| 1 | Không có secret / password trong repo | **ĐÃ LÀM** | File `.env` nằm trong `.gitignore`; chỉ có `.env.example` với giá trị mẫu. Lệnh `git log --all --full-history -- .env` không có kết quả rò rỉ. Không hardcode chuỗi kết nối vào code. |
| 2 | Dữ liệu đầu vào được kiểm ở tầng ứng dụng | **ĐÃ LÀM** | Kiểm soát 3 tầng: `src/backend/validators/ticketValidator.js` (kiểm kiểu dữ liệu & regex), `src/backend/services/ticketService.js` (thẩm định nghiệp vụ), `schema.sql` (ràng buộc `CHECK`, `NOT NULL`, `FOREIGN KEY`). Mọi truy vấn PostgreSQL đều dùng parameterized query `$1, $2`, chống 100% SQL Injection. |
| 3 | Kiểm soát truy cập và phân quyền dữ liệu | **ĐÃ LÀM** | Khóa thao tác theo trạng thái một chiều (QT-06). Mọi cập nhật trạng thái phiếu đều bắt buộc có `updated_by` để phục vụ audit trail (NFR3). |
| 4 | Mật khẩu và dữ liệu nhạy cảm được bảo vệ | **ĐÃ LÀM** | File `src/backend/utils/logger.js` có hàm `che()` tự động che giấu (`***`) các trường nhạy cảm (`password`, `token`, `secret`, `jwt`, `authorization`) trước khi ghi ra log hệ thống. |
| 5 | Thông báo lỗi không để lộ cấu trúc bên trong | **ĐÃ LÀM** | Middleware xử lý lỗi cuối cùng trong `src/backend/index.js` trả về mã lỗi chuẩn `{ success: false, error: 'LOI_HE_THONG', message: '...', requestId: '...' }`, tuyệt đối không trả vết ngăn xếp (stack trace) hay tên bảng CSDL ra client. |
| 6 | Nhật ký không ghi secret hay dữ liệu cá nhân thừa | **ĐÃ LÀM** | `src/backend/utils/logger.js` ghi log dạng JSON có cấu trúc, chỉ ghi nhận requestId, method, url, statusCode, responseTime; trường nhạy cảm được che giấu tự động. |
| 7 | Thư viện phụ thuộc được ghim phiên bản | **ĐÃ LÀM** | Toàn bộ package trong `package.json` đều được quản lý chặt chẽ kèm `package-lock.json` (`express ^5.2.1`, `pg ^8.23.1`, `dotenv ^18.0.5`). Sử dụng Node.js 20+ LTS runtime chính thức. |

---

## 4 Mục bảo mật bổ sung đã thực hiện:

| Mục | Minh chứng |
|---|---|
| **Giới hạn kích thước thân yêu cầu (Body Limit)** | `src/backend/index.js`: cấu hình `express.json({ limit: '256kb' })` nhằm chống tấn công DoS làm cạn kiệt bộ nhớ RAM. |
| **Gán Request ID truy vết sự cố** | `src/backend/utils/logger.js`: middleware `ganRequestId` tự động tạo UUID gán vào header `X-Request-Id` cho từng request. |
| **Sanitize chuỗi Serial / IMEI** | `src/backend/validators/ticketValidator.js`: áp dụng regex `^[A-Za-z0-9-]{6,40}$` loại trừ các ký tự escape injection. |
| **Ràng buộc toàn vẹn cơ sở dữ liệu** | `src/backend/db/schema.sql`: thiết lập `UNIQUE (ticket_code)`, `CHECK (priority IN ('CAO', 'TRUNG_BINH', 'THAP'))`. |
