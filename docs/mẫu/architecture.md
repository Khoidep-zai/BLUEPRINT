# THIẾT KẾ KIẾN TRÚC HỆ THỐNG
## Luồng L2: Tiếp nhận và phân loại yêu cầu bảo hành
### Hệ thống: Mekong Mobile CRM — Sinh viên: Nguyễn Bá Anh Khôi (MSSV: 2374802010247, Track SE)

---

### 1. Sơ đồ kiến trúc phân lớp và thành phần hệ thống

Hệ thống áp dụng mô hình **Kiến trúc phân lớp 4 tầng chuẩn (4-Tier Layered Architecture)** kết hợp nguyên tắc **phụ thuộc một chiều (Single-Directional Dependency)** nghiêm ngặt: tầng trên gọi tầng dưới, tầng dưới tuyệt đối không bao giờ gọi ngược tầng trên. Mọi chi tiết trao đổi giữa các tầng đều được định chuẩn giao thức rõ ràng.

```text
HỆ THỐNG: Phân hệ tiếp nhận và phân loại bảo hành (Mekong Mobile CRM - Track SE)
+-----------------------------------------------------------------------------------+
| 1. LỚP TRÌNH DIỄN (Presentation Layer - HTML5, Modern CSS, ES6)                   |
| [ Màn hình 1: Danh sách phiếu ]  [ Màn hình 2: Tạo phiếu ]  [ Màn hình 3: Chi tiết ] |
+-----------------------------------------------------------------------------------+
        | v  Giao thức: HTTP / JSON RESTful (Đặc tả tại docs/api-contract.md)
+-----------------------------------------------------------------------------------+
| 2. LỚP ĐIỀU PHỐI (Controller & Middleware Layer - Express.js)                     |
| TicketController · CustomerController · ValidateMiddleware · ErrorHandlerMiddleware|
| - Trách nhiệm: Định tuyến API, kiểm tra rỗng/format đầu vào, chuyển tiếp DTO xuống.|
| - KHÔNG ĐƯỢC: Chứa quy tắc nghiệp vụ, không truy vấn CSDL trực tiếp.              |
+-----------------------------------------------------------------------------------+
        | v  Giao thức: Lời gọi hàm nội bộ (Internal Method Call / DTO)
+-----------------------------------------------------------------------------------+
| 3. LỚP NGHIỆP VỤ CỐT LÕI (Business Service Layer)                                 |
| TicketService (Vòng đời QT-06) · SLACalculator (QT-04) · PhoneHelper (QT-01)      |
| - Trách nhiệm: Quản lý toàn bộ quy tắc nghiệp vụ, tính toán SLA, điều phối Tx.    |
| - KHÔNG ĐƯỢC: Biết công nghệ lưu trữ dữ liệu (SQL, Prisma, hay In-Memory).        |
| >>> TOÀN BỘ quy tắc nghiệp vụ (QT-01 đến QT-06) chỉ nằm tại tầng này <<<          |
+-----------------------------------------------------------------------------------+
        | v  Giao thức: Giao diện Repository trừu tượng (Interface Call)
+-----------------------------------------------------------------------------------+
| 4. LỚP TRUY XUẤT DỮ LIỆU & LƯU TRỮ (Data Access & Persistence Layer)              |
| TicketRepository · CustomerRepository · DeviceRepository · StatusLogRepository    |
| - Trách nhiệm: Thực thi CRUD, che giấu chi tiết SQL, quản lý Database Transaction.|
| PostgreSQL 15 Engine: customer, device, ticket, issue_category, ticket_status_log |
+-----------------------------------------------------------------------------------+
CHÚ THÍCH: [ ] = Màn hình giao diện | v = Hướng phụ thuộc một chiều (trên gọi xuống dưới).
NGOÀI PHẠM VI (Mức WON'T): Phân công KTV (L4), Tồn kho linh kiện (L5), Gửi SMS Brandname (L1), Thu phí sửa chữa.
```

---

### 2. Sự kết hợp ba mẫu kiến trúc và minh chứng cấu trúc thư mục

Hệ thống kết hợp hài hòa **3 mẫu kiến trúc kinh điển** ở quy mô prototype để vừa đảm bảo tính module hóa, vừa dễ dàng kiểm thử tự động theo yêu cầu của học phần:

1. **Mẫu Layered (Phân lớp tổng thể):** Đóng vai trò khung xương định hình 4 mức trừu tượng độc lập (Trình diễn → Điều phối → Nghiệp vụ → Dữ liệu).
2. **Mẫu MVC (Model - View - Controller):** Tổ chức bên trong tầng giao diện và điều phối: `View` (Wireframe UI), `Controller` (Express Router/Controller tiếp nhận request), `Model` (Data Transfer Objects & Entities).
3. **Mẫu Repository (Trừu tượng hóa dữ liệu):** Đặt giữa lớp Nghiệp vụ và CSDL PostgreSQL. Lớp `TicketService` chỉ làm việc với interface `ITicketRepository`, cho phép hoán đổi giữa `PgTicketRepository` (chạy thật) và `MockTicketRepository` (chạy Unit Test nhanh trong bộ nhớ mà không cần kết nối DB thật).

#### Cấu trúc thư mục mã nguồn làm bằng chứng kiến trúc:
```text
cdtn1-NguyenBaAnhKhoi-l2/
├── src/
│   ├── frontend/                       ← MVC: View (Lớp trình diễn)
│   │   ├── index.html                  ← Màn hình 1: Danh sách phiếu
│   │   ├── create-ticket.html          ← Màn hình 2: Tạo phiếu bảo hành
│   │   ├── ticket-detail.html          ← Màn hình 3: Chi tiết & chuyển trạng thái
│   │   ├── css/style.css               ← Dark Mode Modern UI
│   │   └── js/app.js                   ← Tương tác Client-side
│   ├── backend/
│   │   ├── controllers/                ← MVC: Controller & Middleware
│   │   │   ├── TicketController.js
│   │   │   └── CustomerController.js
│   │   ├── services/                   ← LAYERED: Lớp nghiệp vụ cốt lõi
│   │   │   ├── TicketService.js        (Thi hành QT-06 vòng đời)
│   │   │   ├── SLACalculator.js        (Thi hành QT-04 tính hạn)
│   │   │   └── PhoneHelper.js          (Thi hành QT-01 chuẩn hóa SĐT)
│   │   ├── repositories/               ← REPOSITORY: Truy xuất dữ liệu
│   │   │   ├── ITicketRepository.js    (Giao diện trừu tượng)
│   │   │   ├── ticketRepository.js     (Cài đặt in-memory cho prototype)
│   │   │   └── customerRepository.js   (Cài đặt in-memory cho prototype)
│   │   └── db/
│   │       └── schema.sql              ← LAYERED: Lớp lưu trữ (PostgreSQL DDL)
├── tests/
│   ├── smoke.test.js                   ← Health-check endpoints
│   └── ticket.test.js                  ← Integration tests cho toàn bộ nghiệp vụ
└── docs/
    ├── srs.md                          ← Đặc tả yêu cầu phần mềm
    ├── architecture.md                 ← Tài liệu thiết kế kiến trúc (file này)
    ├── api-contract.md                 ← Mô hình dữ liệu ERD & Hợp đồng API
    ├── architecture.drawio             ← Sơ đồ kiến trúc (file gốc draw.io)
    ├── erd.drawio                      ← Sơ đồ ERD (file gốc draw.io)
    ├── usecase.drawio                  ← Sơ đồ Use Case (file gốc draw.io)
    └── wireframes.html                 ← Wireframe 3 màn hình tương tác
```

---

### 3. Lập luận lựa chọn kiến trúc (Architecture Rationale)

Tuân thủ nghiêm ngặt công thức chuẩn:
> *"Vì \<Mã NFR\> yêu cầu \<ngưỡng cụ thể\>, tôi chọn \<quyết định kiến trúc\>, đánh đổi là \<chi phí/nhược điểm\>."*

- **Lập luận 1 — Gắn với Hiệu năng tra cứu (NFR1):**
  Vì **NFR1** yêu cầu thời gian phản hồi của API tra cứu khách hàng và danh sách phiếu phải dưới **500ms** đối với tập dữ liệu thực tế **67.037 bản ghi** (ngưỡng P95), tôi chọn **cơ chế phân trang ở tầng CSDL (OFFSET/LIMIT) kết hợp đánh B-Tree Composite Index trên `(status, due_date)` và B-Tree Index trên `customer(phone)`** thay vì tải toàn bộ dữ liệu rồi lọc ở lớp trình bày.
  *Đánh đổi:* Làm tăng nhẹ dung lượng lưu trữ đĩa và chi phí ghi khi chèn/cập nhật phiếu, nhưng hoàn toàn chấp nhận được vì tần suất đọc (Read) của lễ tân cao gấp 8 lần tần suất ghi (Write).

- **Lập luận 2 — Gắn với Tính sẵn sàng & Khả năng kiểm thử (NFR2):**
  Vì **NFR2** yêu cầu hệ thống đạt tối thiểu **99.9% uptime** và đáp ứng tiêu chí kiểm thử độc lập (Testability với ≥ 3 Unit Test cho Service), tôi chọn **áp dụng mẫu thiết kế Repository Pattern để cô lập hoàn toàn tầng Nghiệp vụ khỏi công nghệ lưu trữ cụ thể**.
  *Đánh đổi:* Phát sinh thêm một lớp giao diện trừu tượng và nhiều tệp mã nguồn hơn ở quy mô prototype, nhưng cho phép chạy bộ kiểm thử Unit Test bằng Repository giả lập trong bộ nhớ mà không phụ thuộc vào hạ tầng mạng hay CSDL thật.

- **Lập luận 3 — Gắn với Toàn vẹn dữ liệu kiểm toán (NFR3):**
  Vì **NFR3** yêu cầu đảm bảo tính toàn vẹn dữ liệu tuyệt đối theo chuẩn ACID với **tỷ lệ mồ côi dữ liệu bằng 0.00%** khi tạo phiếu và cập nhật trạng thái kèm ghi log, tôi chọn **sử dụng Hệ quản trị CSDL quan hệ PostgreSQL kết hợp quản lý Database Transaction tại tầng Service**, bao bọc lệnh `UPDATE ticket` và `INSERT ticket_status_log` trong cùng một khối `BEGIN...COMMIT`.
  *Đánh đổi:* Khó khăn trong việc mở rộng phân tán theo chiều ngang (Horizontal Sharding) so với các CSDL NoSQL phân tán, tuy nhiên luồng L2 có cấu trúc quan hệ chặt chẽ nên CSDL quan hệ là lựa chọn tối ưu nhất.

---

### 4. Đối sánh hai phương án kỹ thuật cho yêu cầu NFR2

**Bối cảnh:** NFR2 đòi hỏi tiếp nhận phiếu bảo hành ≤ 1 giây và duy trì độ ổn định liên tục trong giờ vận hành phục vụ khách hàng.

| Tiêu chí so sánh | Phương án A — Xử lý đồng bộ có Timeout (ĐƯỢC CHỌN) | Phương án B — Xử lý qua Hàng đợi tin nhắn (Message Queue) |
|---|---|---|
| **Cơ chế hoạt động** | `Controller` → `TicketService` → `Postgres Tx` (chờ tuần tự trong 1 transaction duy nhất, gắn timeout 500ms). | `Controller` nhận form → Đẩy job vào RabbitMQ → Trả về mã pending ngay lập tức → Worker nền xử lý lưu DB. |
| **Ưu điểm** | - Đơn giản, tính toàn vẹn ACID tức thời.<br>- Lễ tân nhận ngay mã phiếu chính thức để in biên nhận giao khách (FR9). | - Tuyệt đối không nghẽn cổng tiếp nhận khi có lượng truy cập đột biến.<br>- Đảm bảo NFR2 luôn đạt dưới 100ms ở bước nhận. |
| **Nhược điểm & Đánh đổi** | Nếu CSDL bị khóa dòng tạm thời, request có thể bị chờ tối đa 500ms. | - Thêm cụm máy chủ Queue cần vận hành và giám sát.<br>- Phiếu ở trạng thái "Chờ xử lý" khiến giao diện phải polling liên tục, phức tạp hóa quy trình in biên nhận. |
| **Quyết định cho Prototype** | **Chọn Phương án A:** Vì nghiệp vụ tiếp nhận tại quầy lễ tân đòi hỏi cấp ngay mã phiếu thực tế và in biên nhận vật lý giao khách tại chỗ; đồng thời khối lượng tiếp nhận tại chi nhánh là tuần tự nên phương án A vừa tối ưu chi phí vừa đảm bảo tính toàn vẹn tuyệt đối. | — |
