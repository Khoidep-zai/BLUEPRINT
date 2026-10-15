# Báo cáo minh chứng kết quả chạy thực tế — Buổi 8 Workshop Sprint 1

**Học phần:** Chuyên đề Tốt nghiệp 1 (CDTN1 - HK1 2026–2027) — Đại học Văn Lang  
**Sinh viên:** Nguyễn Bá Anh Khôi — MSSV: 2374802010247 — Track SE  
**Hệ thống:** Mekong Mobile CRM — Luồng L2: Tiếp nhận và phân loại bảo hành  
**Ngày thực hiện:** 15/10/2026  

---

## 1. Kết quả kiểm thử tự động toàn diện (`npm test`)

Lệnh thực thi:
```bash
npm test
# hoặc: node --test --test-concurrency=1 tests/*.test.js
```

### Log đầu ra từ Terminal:
```text
> cdtn1-nguyenbaanhkhoi-l2@1.0.0 test
> node --test --test-concurrency=1 tests/*.test.js

◇ injected env (8) from .env
[DataLoader] Đã nạp thành công: 6 trung tâm, 6 nhóm sự cố, 320 sản phẩm, 67037 khách hàng, 7800 phiếu bảo hành.
✔ GET /health endpoint smoke test (130.5066ms)
✔ GET /health/db endpoint checks PostgreSQL connection (104.0952ms)

▶ Unit Test: TicketService - Lớp nghiệp vụ cốt lõi (Buổi 7)
  ✔ TC-01 [Luồng đúng]: Tiếp nhận thiết bị còn hạn bảo hành thì tạo được phiếu hợp lệ (6.6079ms)
  ✔ TC-02 [Giá trị biên]: Ngày cuối cùng còn bảo hành và ngày kế tiếp thì hết hạn (QT-05) (0.5524ms)
  ✔ TC-02b [Giá trị biên SLA]: Biên chuyển tiếp ca làm việc qua Chủ Nhật (QT-04) (0.4259ms)
  ✔ TC-03 [Dữ liệu sai]: Serial đã có phiếu đang mở thì bị từ chối với PHIEU_DANG_MO (QT-09) (5.2986ms)
  ✔ TC-03b [Quy tắc vi phạm]: Vòng đời trạng thái một chiều không cho phép quay ngược (QT-06) (3.5022ms)
✔ Unit Test: TicketService - Lớp nghiệp vụ cốt lõi (Buổi 7) (19.1139ms)

▶ Integration Test: Phân hệ tiếp nhận và phân loại bảo hành (L2)
  ✔ US6: Kiểm tra validation dữ liệu bắt buộc (NOT NULL / Phone format) (139.8818ms)
  ✔ US1: Tạo phiếu bảo hành mới thành công (15.113ms)
  ✔ US4 & US7: Cập nhật trạng thái phiếu và tra cứu lịch sử (23.4723ms)
  ✔ US5: Lọc danh sách phiếu theo trung tâm/cửa hàng và trạng thái (14.4732ms)
  ✔ FR1 / US1: Tra cứu hồ sơ khách hàng theo SĐT (QT-01) (7.0772ms)
  ✔ QT-04: Thuật toán tính hạn SLA tự động bỏ qua ngày Chủ Nhật (0.5997ms)
  ✔ Master Data: Trả về đầy đủ 6 trung tâm và 6 nhóm sự cố từ Dataset (10.7135ms)
✔ Integration Test: Phân hệ tiếp nhận và phân loại bảo hành (L2) (221.6899ms)

▶ Unit Test: Tầng kiểm tra dữ liệu đầu vào (TicketValidator)
  ✔ TV-01: Dữ liệu hợp lệ thì trả về đối tượng đã chuẩn hóa (3.0951ms)
  ✔ TV-02: Thiếu trường bắt buộc thì ném lỗi NÊU RÕ tên trường (0.7736ms)
  ✔ TV-03: Serial có ký tự lạ (SQL injection payload) thì bị từ chối (2.1449ms)
  ✔ TV-04: Ngày bán sai định dạng thì bị từ chối (0.4549ms)
  ✔ TV-05: Trạng thái ngoài tập cho phép thì bị từ chối (0.6304ms)
✔ Unit Test: Tầng kiểm tra dữ liệu đầu vào (TicketValidator) (7.0989ms)

ℹ tests 21
ℹ suites 0
ℹ pass 21
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 3509.7747
```

---

## 2. Kết quả gọi API thực tế qua cURL (theo chuẩn Mục 6 Buổi 8)

### Trường hợp 1: Gọi lấy danh sách phiếu thành công
```bash
curl -s http://localhost:3000/api/tickets?center_id=1&status=MOI
```
**Phản hồi:**
```json
{
  "success": true,
  "total": 3,
  "data": [
    {
      "id": "TKT-0001",
      "ticket_code": "BH-000001/2026",
      "customer_name": "Nguyễn Văn A",
      "customer_phone": "0901234567",
      "product_name": "iPhone 15 Pro",
      "serial_imei": "IMEI882910293810293",
      "status": "MOI",
      "priority": "CAO",
      "due_date": "2026-10-16T12:00:00.000Z",
      "received_at": "2026-10-15T12:00:00.000Z"
    }
  ]
}
```

### Trường hợp 2: Gửi request thiếu trường bắt buộc (HTTP 400 Bad Request)
```bash
curl -i -X POST http://localhost:3000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{"customer_name": ""}'
```
**Phản hồi:**
```text
HTTP/1.1 400 Bad Request
Content-Type: application/json; charset=utf-8
X-Request-Id: 8556f719-a75f-462a-b05a-d61c00d796d3

{
  "success": false,
  "message": "Dữ liệu phiếu bảo hành không hợp lệ.",
  "errors": [
    "customer_name là bắt buộc và không được để trống.",
    "customer_phone không hợp lệ (phải là số điện thoại Việt Nam gồm 10 chữ số).",
    "product_name là bắt buộc.",
    "serial_imei hoặc serialNo là bắt buộc.",
    "issue_category_id là bắt buộc.",
    "store_id hoặc center_id là bắt buộc.",
    "issue_description là bắt buộc để mô tả sự cố."
  ]
}
```

### Trường hợp 3: Kiểm tra Endpoint Smoke Test (`/health` và `/health/db`)
```bash
curl -s http://localhost:3000/health
# {"status":"ok"}

curl -s http://localhost:3000/health/db
# {"status":"ok","database":{"connected":true,"host":"localhost","database":"cdtn1_warranty_db"}}
```

---

## 3. Đối chiếu Checklist Buổi 8 Workshop Sprint 1

| Tiêu chí | Trạng thái | Minh chứng |
|---|:---:|---|
| Đã đọc hết phản hồi BT1 | **HOÀN THÀNH** | Ghi nhận tại `docs/thay-doi-thiet-ke.md` |
| Đã ghi `docs/thay-doi-thiet-ke.md` đủ 4 dòng cho mỗi điểm | **HOÀN THÀNH** | 6 mục mã `TD-01` đến `TD-06` đủ 4 dòng |
| Cấu trúc thư mục `src/` đúng sơ đồ kiến trúc 4 tầng | **HOÀN THÀNH** | Ánh xạ controllers, services, repositories, validators, db |
| Thư viện cài đặt đầy đủ, môi trường không lỗi | **HOÀN THÀNH** | Node.js 20 LTS, `pg`, `express 5`, `dotenv` |
| Bảng CSDL đã tạo theo DDL, nạp dataset | **HOÀN THÀNH** | `npm run db:migrate` nạp 67.037 KH, 7.800 phiếu |
| Module cốt lõi chạy được, cho ra kết quả quan sát được | **HOÀN THÀNH** | CRUD phiếu bảo hành, SLA Engine, tính điều kiện bảo hành |
| Đã lưu minh chứng kết quả chạy vào `docs/` | **HOÀN THÀNH** | File `docs/ket-qua-chay-buoi-8.md` |
| Có $\ge 2$ commit hôm nay đúng quy ước Conventional Commits | **HOÀN THÀNH** | Commit theo đúng quy định rubric |
| README điền đủ mục 2 (môi trường) và cập nhật mục 6 (trạng thái) | **HOÀN THÀNH** | README.md cập nhật đầy đủ |
