# Bug Log — Phân hệ tiếp nhận và phân loại bảo hành (L2)

Học phần: Chuyên đề Tốt nghiệp 1 (CDTN1) — Track SE  
Sinh viên: Nguyễn Bá Anh Khôi — MSSV: 2374802010247  

---

## BUG-01 · Mức độ: **CRITICAL** (Kiểm soát chuyển trạng thái một chiều)

1. **Phát hiện bởi:** TC-03b (Kiểm thử vi phạm quy tắc vòng đời trạng thái một chiều QT-06).
2. **Triệu chứng:** Phiếu đang ở trạng thái `DANG_XU_LY` hoặc `HOAN_TAT` bị người dùng gửi request cập nhật lùi về trạng thái `MOI`. API chấp nhận và ghi đè trạng thái.
3. **Cách tái lập:** Gọi `PATCH /api/tickets/:id/status` với thân `{"status": "MOI", "updated_by": "NV_TEST"}` khi phiếu đã ở `DANG_XU_LY`.
4. **Nguyên nhân:** Tầng Service trước đó chỉ kiểm tra sự tồn tại của phiếu mà chưa thẩm định ma trận chuyển trạng thái hợp lệ (`VALID_TRANSITIONS`).
5. **Cách sửa:** Khai báo hằng số `VALID_TRANSITIONS` trong `src/backend/services/ticketService.js`. Trong hàm `updateStatus`, nếu `!VALID_TRANSITIONS[oldStatus].includes(targetStatus)` thì lập tức ném lỗi nghiệp vụ `AppError('TRANG_THAI_KHONG_HOP_LE')`.
6. **Xác nhận:** Chạy lại `TC-03b` trong `tests/ticket.service.test.js` $\rightarrow$ ném lỗi chính xác và trạng thái cũ được bảo toàn $\rightarrow$ **PASS**.

---

## BUG-02 · Mức độ: **MAJOR** (Lệch 1 ngày bảo hành tại điểm biên)

1. **Phát hiện bởi:** TC-02 (Kiểm thử giá trị biên của điều kiện bảo hành QT-05).
2. **Triệu chứng:** Thiết bị mua ngày `2025-06-01` với hạn bảo hành 12 tháng bị hệ thống tính là **hết hạn** vào lúc 10:00 sáng ngày `2026-06-01`.
3. **Cách tái lập:** Gọi hàm thẩm định bảo hành với mốc thời gian tiếp nhận nằm trong ngày cuối cùng của hạn bảo hành.
4. **Nguyên nhân:** Khi cộng số tháng bảo hành, đối tượng `Date` giữ nguyên phần giờ `00:00:00`. Bất kỳ thời điểm nào sau 0 giờ của ngày cuối cùng đều bị toán tử `>` coi là quá hạn. Theo quy tắc nghiệp vụ QT-05: thiết bị vẫn còn hạn bảo hành đến hết ngày cuối cùng (`23:59:59.999`).
5. **Cách sửa:** Trong `TicketService.isUnderWarranty`, thiết lập mốc hết hạn đến cuối ngày: `expiryDate.setHours(23, 59, 59, 999)` trước khi so sánh với thời điểm tiếp nhận.
6. **Xác nhận:** `TC-02` kiểm thử đúng ngày hết hạn và ngày kế tiếp $\rightarrow$ **PASS 100%**.

---

## BUG-03 · Mức độ: **MAJOR** (Tối ưu hóa thời gian lọc danh sách phiếu)

1. **Phát hiện bởi:** Đo hiệu năng truy vấn khi nạp 7.800 phiếu bảo hành mẫu từ dataset.
2. **Triệu chứng:** Lọc danh sách phiếu theo `center_id` và `status` qua `GET /api/tickets` mất hơn 1,8 giây, vi phạm ngưỡng yêu cầu phi chức năng NFR1 (< 1 giây).
3. **Cách tái lập:** Nạp toàn bộ dataset vào PostgreSQL; chạy truy vấn `EXPLAIN ANALYZE SELECT * FROM tickets WHERE center_id = 1 AND status = 'MOI' ORDER BY received_at DESC`.
4. **Nguyên nhân:** Bảng `tickets` thiếu chỉ mục kết hợp, PostgreSQL phải thực hiện `Seq Scan` toàn bộ 7.800 dòng và sắp xếp bộ nhớ.
5. **Cách sửa:** Bổ sung chỉ mục `CREATE INDEX idx_tickets_center_status ON tickets(center_id, status)` và `CREATE INDEX idx_tickets_serial ON tickets(serial_imei)` vào `src/backend/db/schema.sql`.
6. **Xác nhận:** Thời gian truy vấn giảm từ **1,85 giây** xuống còn **0,04 giây** (40ms) $\rightarrow$ Đạt yêu cầu NFR1 (ghi nhận tại `docs/toi-uu.md`).

---

## BUG-04 · Mức độ: **NORMAL** (Lỗ hổng dữ liệu nhập ký tự lạ SQL Injection)

1. **Phát hiện bởi:** TV-03 (Unit test kiểm tra tầng Validator).
2. **Triệu chứng:** Chuỗi serial chứa ký tự đặc biệt (`SN' OR 1=1 --`) đi lọt qua tầng kiểm tra đầu vào trước khi tới cơ sở dữ liệu.
3. **Cách tái lập:** Gửi request tạo phiếu với `serial_imei: "SN' OR 1=1 --"`.
4. **Nguyên nhân:** Regex kiểm tra chuỗi serial chưa được siết chặt định dạng.
5. **Cách sửa:** Chuẩn hóa regex `RE_SERIAL = /^[A-Za-z0-9-]{6,40}$/` trong `src/backend/validators/ticketValidator.js`, từ chối ngay lập tức các ký tự không an toàn với mã lỗi `DU_LIEU_KHONG_HOP_LE`.
6. **Xác nhận:** `TV-03` chạy thành công $\rightarrow$ **PASS**.
