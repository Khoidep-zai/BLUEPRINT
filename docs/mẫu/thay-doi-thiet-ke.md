# Nhật ký thay đổi thiết kế

Học phần: Chuyên đề Tốt nghiệp 1 (CDTN1) — Học kỳ 1, Năm học 2026–2027  
Sinh viên: Nguyễn Bá Anh Khôi — MSSV: 2374802010247 — Track SE  
Hệ thống: Mekong Mobile CRM — Luồng L2: Tiếp nhận và phân loại yêu cầu bảo hành  

> **Mục đích:** Mọi sai lệch so với thiết kế ban đầu (Bài tập 1) đều được ghi lại tại đây, mỗi thay đổi gồm đủ **bốn dòng bắt buộc**: **Phản hồi của GV · Quyết định · Lý do · Ảnh hưởng**. Đây là minh chứng trực tiếp cho tiêu chí 3 (Nhất quán & Tích lũy) trong Rubric đánh giá của ĐH Văn Lang.

---

## Sau phản hồi Bài tập 1 (Buổi 8, ngày 15/10/2026)

### TD-01 Bổ sung bảng lịch sử trạng thái `ticket_status_logs`
- **Phản hồi của GV:** Sơ đồ ERD chỉ có thuộc tính `status` trên bảng `tickets` bị ghi đè khi cập nhật, không trả lời được câu hỏi "phiếu này nằm ở trạng thái Đang xử lý bao lâu" và thiếu cơ chế audit trail cho nghiệp vụ bảo hành.
- **Quyết định:** SỬA
- **Lý do:** Yêu cầu FR6/US7 cần truy vết dòng thời gian (timeline) và tính thời gian xử lý trung bình theo cam kết SLA, không có bảng lịch sử trạng thái thì không thể thống kê được.
- **Ảnh hưởng:** Bổ sung bảng `ticket_status_logs` vào `src/backend/db/schema.sql`, thêm phương thức `addStatusLog` / `getStatusLogs` vào `ITicketRepository` và `TicketRepository`, tự động ghi vết trong `TicketService.createTicket` và `TicketService.updateStatus`, cập nhật sơ đồ `erd.drawio`.

---

### TD-02 Chuẩn hóa mã lỗi nghiệp vụ độc lập giao thức HTTP qua lớp `AppError`
- **Phản hồi của GV:** Lớp nghiệp vụ (Service) không được phụ thuộc trực tiếp vào mã trạng thái HTTP (như ném lỗi 400, 404, 409), vì Service cần độc lập để tái sử dụng cho CLI, Background Job và Test tự động.
- **Quyết định:** SỬA
- **Lý do:** Tuân thủ nguyên tắc thiết kế 4 tầng phân lớp sạch của Buổi 7 (Separation of Concerns). Tầng Service chỉ ném mã nghiệp vụ thuần túy (`PHIEU_DANG_MO`, `TRANG_THAI_KHONG_HOP_LE`, `DU_LIEU_KHONG_HOP_LE`), việc ánh xạ sang HTTP status code (400, 404, 409, 422) do tầng Controller / Routes đảm nhiệm.
- **Ảnh hưởng:** Tạo `src/backend/errors/AppError.js`, cập nhật `TicketService.js` ném `AppError`, bổ sung bảng ánh xạ `HTTP_BY_CODE` trong `src/backend/controllers/ticketController.js`.

---

### TD-03 Hiện thực quy tắc QT-09 ngăn chặn tạo phiếu trùng trên cùng Serial/IMEI
- **Phản hồi của GV:** Cần có cơ chế kiểm tra ràng buộc nghiệp vụ ngăn chặn lễ tân tại quầy tạo 2 phiếu tiếp nhận cùng lúc cho 1 thiết bị đang trong quá trình bảo hành/sửa chữa.
- **Quyết định:** SỬA
- **Lý do:** Tránh tình trạng trùng lặp hồ sơ tiếp nhận, sai lệch chỉ số KPI và lãng phí linh kiện thay thế khi thiết bị chưa đóng phiếu cũ.
- **Ảnh hưởng:** Bổ sung hàm `findBySerial(serialNo)` vào `ITicketRepository` và `TicketRepository`, thêm logic thẩm định `QT-09` trong `TicketService.createTicket` (ném `PHIEU_DANG_MO` nếu phiếu cũ chưa thuộc `HOAN_TAT` / `DA_HUY` / `DA_DONG`), bổ sung test case `TC-03`.

---

### TD-04 Giữ nguyên việc tính hạn SLA loại trừ ngày Chủ Nhật (QT-04)
- **Phản hồi của GV:** Có cần tính thêm ngày nghỉ lễ quốc gia vào thuật toán tính hạn SLA của phiếu tiếp nhận không?
- **Quyết định:** GIỮ NGUYÊN
- **Lý do:** Trong phạm vi học phần CDTN1 (Sprint 1 & Prototype BT2), Mekong Mobile quy định trung tâm bảo hành làm việc từ Thứ Hai đến Thứ Bảy, nghỉ cố định Chủ Nhật. Việc tích hợp lịch nghỉ lễ động đòi hỏi thêm bảng cấu hình Calendar, sẽ mở rộng ở Chuyên đề tốt nghiệp 2.
- **Ảnh hưởng:** Không làm thay đổi thiết kế hiện tại. Đã ghi chú phạm vi vào `docs/srs.md` mục QT-04 và xây dựng bộ test biên `TC-02b` kiểm chứng thuật toán nhảy ca qua Chủ Nhật.

---

### TD-05 Tách riêng Mock Repository độc lập phục vụ Unit Test tầng Service
- **Phản hồi của GV:** Bộ kiểm thử tầng Service trong Bài tập 1 bị phụ thuộc vào CSDL thật, khi CSDL chưa kết nối thì toàn bộ test bị fail.
- **Quyết định:** SỬA
- **Lý do:** Đúng chuẩn kiểm thử phần mềm Buổi 7: Unit Test phải chạy nhanh trong vài phần nghìn giây, xác định (deterministic) và độc lập hoàn toàn với hạ tầng mạng hay CSDL ngoài.
- **Ảnh hưởng:** Viết lại `tests/ticket.service.test.js` sử dụng In-Memory Mock Repository mô phỏng `ITicketRepository`, đưa thời gian chạy 5 unit test xuống còn dưới 25ms, cho phép chạy test ngay cả khi PostgreSQL chưa bật.

---

### TD-06 Bổ sung chỉ mục tối ưu hóa truy vấn danh sách phiếu bảo hành
- **Phản hồi của GV:** Khi số lượng phiếu lên đến hàng ngàn bản ghi, truy vấn lọc theo trung tâm và thời gian tiếp nhận có thể bị chậm.
- **Quyết định:** SỬA
- **Lý do:** Đáp ứng yêu cầu phi chức năng NFR1 (thời gian phản hồi API dưới 1 giây với tập dữ liệu lớn).
- **Ảnh hưởng:** Thêm chỉ mục `idx_tickets_center_status` trên `(center_id, status)` và `idx_tickets_serial` trên `serial_imei` trong `src/backend/db/schema.sql`, ghi nhận số liệu trước/sau trong `docs/toi-uu.md`.
