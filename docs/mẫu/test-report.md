# Test Report — Báo cáo kết quả kiểm thử (L2)

Học phần: Chuyên đề Tốt nghiệp 1 (CDTN1) — Track SE  
Sinh viên: Nguyễn Bá Anh Khôi — MSSV: 2374802010247  

**Lệnh chạy kiểm thử:** `npm test`  
**Kết quả tổng quát:** **21/21 TESTS PASS (100% SUCCESS)**  
**Thời gian thực thi:** 3,5 giây  

---

## Bảng ma trận kết quả kiểm thử chi tiết

| Mã Test | Tầng | Mục tiêu kiểm thử | Dữ liệu đầu vào | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
|---|:---:|---|---|---|---|:---:|
| **ST-01** | Smoke | Kiểm tra trạng thái máy chủ Express | `GET /health` | HTTP 200, status: ok | HTTP 200, status: ok | **PASS** |
| **ST-02** | Smoke | Kiểm tra kết nối CSDL PostgreSQL | `GET /health/db` | HTTP 200, db connected: true | HTTP 200, database: connected | **PASS** |
| **TC-01** | Unit | [Luồng đúng] Tiếp nhận thiết bị còn hạn bảo hành | soldAt: 2026-06-01, hạn 12 tháng, mốc: 2026-09-01 | Phiếu hợp lệ, mã `BH-xxxxxx/yyyy`, `is_warranty = true` | is_warranty: true, status: MOI | **PASS** |
| **TC-02** | Unit | [Biên] Ngày cuối cùng còn bảo hành và ngày kế tiếp hết hạn | Biên 365 ngày (QT-05) | Ngày cuối: `true`; Ngày kế tiếp: `false` | true / false chính xác | **PASS** |
| **TC-02b** | Unit | [Biên SLA] Hạn xử lý chuyển tiếp ca qua Chủ Nhật | Tiếp nhận Thứ 7, ưu tiên CAO (24h) | Hạn cam kết tự động bỏ qua Chủ Nhật (QT-04) | Hạn rơi vào Thứ 2 | **PASS** |
| **TC-03** | Unit | [Dữ liệu sai] Trùng Serial/IMEI đang mở | Serial `IMEI_TEST_001` đang mở phiếu | Từ chối với lỗi `PHIEU_DANG_MO` (QT-09) | Ném AppError PHIEU_DANG_MO | **PASS** |
| **TC-03b** | Unit | [Vi phạm] Chuyển lùi trạng thái vòng đời một chiều | Chuyển từ `DANG_XU_LY` về `MOI` | Từ chối với lỗi `TRANG_THAI_KHONG_HOP_LE` (QT-06) | Ném AppError TRANG_THAI_KHONG_HOP_LE | **PASS** |
| **TV-01** | Validator | Dữ liệu tạo phiếu hợp lệ | Body chuẩn có serial khoảng trắng | Trả về object đã chuẩn hóa (trim) | Dữ liệu sạch, serial chuẩn | **PASS** |
| **TV-02** | Validator | Thiếu các trường bắt buộc | Body rỗng hoặc thiếu SĐT/Serial | Ném lỗi `DU_LIEU_KHONG_HOP_LE` nêu rõ tên trường | Liệt kê đúng customer_phone, serialNo | **PASS** |
| **TV-03** | Validator | Serial chứa ký tự lạ (SQL Injection) | `SN' OR 1=1 --` | Bị từ chối với `DU_LIEU_KHONG_HOP_LE` | Bị chặn ngay tầng Validator | **PASS** |
| **TV-04** | Validator | Ngày mua sai định dạng YYYY-MM-DD | `01/06/2026` | Bị từ chối với `DU_LIEU_KHONG_HOP_LE` | Bị chặn ngay tầng Validator | **PASS** |
| **TV-05** | Validator | Trạng thái ngoài tập hợp cho phép | `status: "XONG_ROI"` | Bị từ chối với `DU_LIEU_KHONG_HOP_LE` | Bị chặn ngay tầng Validator | **PASS** |
| **IT-01** | Integration | US6: Validation đầu vào bắt buộc qua HTTP | `POST /api/tickets` với payload rỗng | HTTP 400, success: false | HTTP 400, errors liệt kê chi tiết | **PASS** |
| **IT-02** | Integration | US1: Tạo phiếu bảo hành mới thành công | `POST /api/tickets` đầy đủ thông tin | HTTP 201, trả về phiếu `BH-000001/2026` | HTTP 201, data có mã phiếu | **PASS** |
| **IT-03** | Integration | US4 & US7: Cập nhật trạng thái & timeline lịch sử | `PATCH /api/tickets/:id/status` | HTTP 200, ghi thêm 1 bản ghi status_history | HTTP 200, status_history có 2 mục | **PASS** |
| **IT-04** | Integration | US5: Lọc danh sách phiếu theo trung tâm & trạng thái | `GET /api/tickets?center_id=1&status=MOI` | HTTP 200, danh sách phiếu lọc đúng | HTTP 200, đúng 100% điều kiện | **PASS** |
| **IT-05** | Integration | FR1/US1: Tra cứu hồ sơ khách hàng theo SĐT (QT-01) | `GET /api/customers?phone=+84901234567` | HTTP 200, tìm thấy khách hàng | HTTP 200, đúng hồ sơ | **PASS** |
| **IT-06** | Integration | QT-04: Thuật toán SLA Engine trừ ngày Chủ Nhật | Tính toán trực tiếp qua `calculateDueDate` | Không có hạn rơi vào ngày Chủ Nhật | Kiểm chứng thành công | **PASS** |
| **IT-07** | Integration | Master Data: Trả về đầy đủ trung tâm & nhóm lỗi | `GET /api/categories`, `GET /api/centers` | HTTP 200, đủ 6 trung tâm, 6 nhóm lỗi | HTTP 200, dữ liệu khớp dataset | **PASS** |

---

## Kết luận
Bộ kiểm thử tự động đáp ứng đầy đủ tiêu chí đánh giá của Bài tập 2 và Buổi 8 Workshop Sprint 1, chứng minh tính toàn vẹn và ổn định của mã nguồn.
