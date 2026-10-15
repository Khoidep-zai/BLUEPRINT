# Nhật ký tối ưu — Ba số cho mỗi lần tối ưu

Học phần: Chuyên đề Tốt nghiệp 1 (CDTN1) — Track SE  
Sinh viên: Nguyễn Bá Anh Khôi — MSSV: 2374802010247  

> **Nguyên tắc cốt lõi của học phần:** *"Không tối ưu thứ chưa đo"*. Mỗi lần tối ưu bắt buộc ghi lại đủ ba số liệu: **Thời gian trước · Thời gian sau · Cách thức đo đạc**.

---

## TU-01 · Truy vấn danh sách phiếu bảo hành có bộ lọc (NFR1)

| Hạng mục | Chi tiết |
|---|---|
| **Chỗ bị chậm** | `GET /api/tickets?center_id=1&status=MOI` với 7.800 phiếu bảo hành trong CSDL PostgreSQL. |
| **Cách đo** | Đo qua lệnh curl đo tổng thời gian phản hồi: `curl -s -o /dev/null -w "%{time_total}\n" "http://localhost:3000/api/tickets?center_id=1&status=MOI"`. Chạy 5 lần lấy giá trị trung vị. Đồng thời chạy `EXPLAIN ANALYZE` trong PostgreSQL. |
| **Trước tối ưu** | **1,85 giây**. PostgreSQL thực hiện `Seq Scan on tickets` trên toàn bộ 7.800 dòng và sắp xếp bộ nhớ. Vượt ngưỡng yêu cầu phi chức năng NFR1 (< 1 giây). |
| **Giải pháp áp dụng** | 1. Bổ sung chỉ mục kép: `CREATE INDEX idx_tickets_center_status ON tickets(center_id, status)`.<br>2. Bổ sung chỉ mục tra cứu Serial: `CREATE INDEX idx_tickets_serial ON tickets(serial_imei)`. |
| **Sau tối ưu** | **0,04 giây** (40 ms). `EXPLAIN ANALYZE` chuyển sang `Bitmap Index Scan using idx_tickets_center_status`. Tốc độ tăng hơn **46 lần**. |
| **Giá phải trả** | Tốn thêm khoảng 350 KB dung lượng bộ nhớ cho file index; thao tác INSERT phiếu mới chậm đi vài microsecond (hoàn toàn chấp nhận được). |

---

## TU-02 · Tối ưu thuật toán tính hạn cam kết SLA Engine (QT-04)

| Hạng mục | Chi tiết |
|---|---|
| **Chỗ bị chậm** | Hàm `calculateDueDate` sử dụng vòng lặp `while (remainingHours > 0)` từng giờ để kiểm tra ngày Chủ Nhật khi tính thời hạn 120h (mức THẤP). |
| **Cách đo** | Chạy benchmark 100.000 lượt tính toán qua hàm đo `console.time` / `performance.now()`. |
| **Trước tối ưu** | **128 ms** cho 100.000 phép tính do lặp cộng dồn từng bước 1 giờ và liên tục khởi tạo lại đối tượng `Date`. |
| **Giải pháp áp dụng** | Tính toán số ngày Chủ Nhật xen kẽ theo công thức số học nguyên khối (Block-day Jump), chỉ lặp phần dư số giờ trong ngày cuối cùng. |
| **Sau tối ưu** | **9,4 ms** cho 100.000 phép tính (tăng tốc hơn 13 lần). |
| **Giá phải trả** | Logic code phức tạp hơn đôi chút nhưng đã có bộ unit test `TC-02b` bảo vệ. |

---

## TU-03 · Một lần tối ưu đã HOÀN LẠI (Rollback)

| Hạng mục | Chi tiết |
|---|---|
| **Ý tưởng** | Đặt bộ nhớ đệm (In-memory Cache) cho kết quả `GET /api/customers?phone=...` trong 60 giây. |
| **Cách đo** | Đo thời gian tra cứu khách hàng qua API. |
| **Trước tối ưu** | 2,8 ms (truy vấn trực tiếp qua `customerRepository.findByPhone`). |
| **Sau tối ưu** | 2,1 ms. |
| **Quyết định** | **HOÀN LẠI (ROLLBACK).** Cải thiện 0,7 ms là không đáng kể, trong khi rủi ro rất cao: nếu khách hàng vừa cập nhật thông tin tại quầy hoặc đăng ký mới qua QT-01, nhân viên quầy khác tra cứu sẽ thấy dữ liệu cũ trong 60 giây, gây lỗi nghiệp vụ tiếp nhận. |

> **Bài học kinh nghiệm:** Hoàn lại một giải pháp tối ưu không đem lại hiệu quả thực tế là quyết định kỹ thuật đúng đắn. Tránh làm phức tạp hóa mã nguồn khi chưa cần thiết.
