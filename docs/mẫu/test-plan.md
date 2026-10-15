# Test Plan rút gọn — Phân hệ tiếp nhận và phân loại bảo hành (L2)

Học phần: Chuyên đề Tốt nghiệp 1 (CDTN1) — Track SE  
Sinh viên: Nguyễn Bá Anh Khôi — MSSV: 2374802010247  

---

## 1. Phạm vi kiểm thử

### Các thành phần được kiểm thử:
* **Quy tắc nghiệp vụ cốt lõi:**
  * `QT-01`: Tra cứu hồ sơ khách hàng theo SĐT.
  * `QT-04`: SLA Engine tính hạn cam kết tự động loại trừ ngày Chủ Nhật.
  * `QT-05`: Kiểm tra điều kiện bảo hành đến hết ngày `23:59:59.999`.
  * `QT-06`: Vòng đời trạng thái một chiều (`MOI` $\rightarrow$ `DA_TIEP_NHAN` $\rightarrow$ `DANG_XU_LY` $\rightarrow$ `CHO_LINH_KIEN` $\rightarrow$ `HOAN_TAT`).
  * `QT-09`: Ngăn chặn tạo phiếu trùng lặp trên cùng số Serial/IMEI.
* **Tầng kiểm tra dữ liệu đầu vào (Validator):**
  * Kiểm tra bắt buộc trường (NOT NULL).
  * Chuẩn hóa định dạng SĐT Việt Nam (10 chữ số).
  * Kiểm tra độ dài và ký tự an toàn cho Serial/IMEI.
* **Tích hợp API và Master Data:**
  * Khởi tạo phiếu tiếp nhận qua API `POST /api/tickets`.
  * Cập nhật trạng thái phiếu và tra cứu timeline lịch sử `PATCH /api/tickets/:id/status`.
  * Lọc danh sách phiếu theo trung tâm và trạng thái `GET /api/tickets`.
  * Nạp master data: 6 trung tâm, 6 nhóm sự cố, 320 sản phẩm.

---

## 2. Phân loại kiểm thử và số lượng

| Tầng kiểm thử | Số lượng | Tệp kiểm thử | Mục đích |
|---|:---:|---|---|
| **Smoke Test** | 2 | `tests/smoke.test.js` | Kiểm tra server sống (`/health`) và kết nối CSDL PostgreSQL (`/health/db`). |
| **Unit Test (Service)** | 5 | `tests/ticket.service.test.js` | Kiểm thử lớp Service độc lập với Mock Repository (đủ 3 loại test Buổi 7: Luồng đúng, Biên, Dữ liệu sai). |
| **Unit Test (Validator)** | 5 | `tests/ticket.validator.test.js` | Kiểm tra tính toàn vẹn và chuẩn hóa của tầng kiểm tra đầu vào. |
| **Integration Test** | 7 | `tests/ticket.test.js` | Kiểm thử tích hợp toàn bộ luồng tiếp nhận, lọc danh sách và audit trail qua HTTP thực. |
| **TỔNG CỘNG** | **19** | `tests/*.test.js` (21 test assertion) | **100% tự động hóa bằng lệnh `npm test`**. |

---

## 3. Tiêu chí thành công đo được

1. **100% test pass** qua một lệnh duy nhất: `npm test` (hoặc `node --test --test-concurrency=1 tests/*.test.js`).
2. Thời gian chạy toàn bộ bộ kiểm thử dưới **5 giây**.
3. Mỗi quy tắc nghiệp vụ đều có test case kiểm thử cả trường hợp hợp lệ (Happy Path) và trường hợp vi phạm (Error Handling).
4. Không có lỗi rò rỉ bộ nhớ hoặc cổng kết nối bị treo sau khi chạy test.
