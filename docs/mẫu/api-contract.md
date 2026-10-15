# MÔ HÌNH DỮ LIỆU & HỢP ĐỒNG API (API CONTRACT)
## Luồng L2: Tiếp nhận và phân loại yêu cầu bảo hành
### Hệ thống: Mekong Mobile CRM — Sinh viên: Nguyễn Bá Anh Khôi (MSSV: 2374802010247, Track SE)

---

### 1. Sơ đồ thực thể quan hệ (ERD — Crow's Foot Notation)

Mô hình dữ liệu luồng L2 được thiết kế chuẩn hóa bậc 3 (3NF) gồm **5 bảng thực thể cốt lõi** và 1 bảng danh mục hỗ trợ, thể hiện đầy đủ khóa chính (PK), khóa ngoại (FK), các ràng buộc toàn vẹn và tỷ số lực lượng theo ký hiệu Crow's Foot (xem chi tiết file `docs/erd.drawio`).

#### Cấu trúc các bảng thực thể cốt lõi:

| Tên bảng | Mô tả thực thể | Khóa chính (PK) | Ràng buộc nghiệp vụ chính |
| :--- | :--- | :--- | :--- |
| `customer` | Khách hàng — lưu hồ sơ định danh | `customer_id BIGSERIAL` | `phone` là UNIQUE (QT-01: Định danh duy nhất) |
| `device` | Thiết bị của khách mang đến bảo hành | `device_id BIGSERIAL` | `serial_no` là UNIQUE; FK `customer_id` |
| `issue_category` | Danh mục nhóm sự cố chuẩn hóa | `category_id SERIAL` | 6 nhóm lỗi; `default_priority` CHECK IN ('CAO','TRUNG_BINH','THAP') |
| `ticket` | Phiếu bảo hành — thực thể trung tâm | `ticket_id BIGSERIAL` | `ticket_code` UNIQUE; FK 4 bảng; CHECK priority, status, issue_desc |
| `ticket_status_log` | Nhật ký chuyển trạng thái kiểm toán | `log_id BIGSERIAL` | FK `ticket_id` ON DELETE CASCADE (QT-06 Audit Trail) |
| `service_center` | Trung tâm tiếp nhận bảo hành chi nhánh | `center_id SERIAL` | `center_code` UNIQUE; FK liên kết với `ticket` |

#### Tỷ số lực lượng giữa các bảng (Crow's Foot Notation):
- `customer` **1 — 0..***: `device` (Một khách hàng sở hữu 0 hoặc nhiều thiết bị trong hệ thống)
- `customer` **1 — 0..***: `ticket` (Một khách hàng có thể có 0 hoặc nhiều phiếu bảo hành)
- `device` **1 — 0..***: `ticket` (Một thiết bị có thể tiếp nhận bảo hành qua nhiều phiếu khác nhau)
- `issue_category` **0..1 — 0..***: `ticket` (`category_id` cho phép NULL đối với các phiếu mới tiếp nhận chưa phân loại)
- `ticket` **1 — 1..***: `ticket_status_log` (Một phiếu bảo hành bắt buộc phải có ít nhất 1 bản ghi nhật ký khởi tạo)
- `service_center` **1 — 0..***: `ticket` (Một trung tâm bảo hành tiếp nhận nhiều phiếu bảo hành)

#### Kiểm tra 5 lỗi ERD phổ biến (theo Tài liệu Buổi 5):

| # | Lỗi thường gặp | Trạng thái ERD này |
|---|---|---|
| 1 | Bảng cô lập (không có quan hệ nào) | ✅ Không có — mọi bảng đều có ít nhất 1 FK liên kết |
| 2 | Thiếu bảng lịch sử (ghi đè trạng thái) | ✅ Có bảng `ticket_status_log` lưu toàn bộ vết thay đổi |
| 3 | Lưu giá trị tính được không có lý do | ✅ Không lưu — `so_ngay_xu_ly` không tồn tại, tính từ `received_at` & `closed_at` khi cần |
| 4 | Thiếu INDEX ở các cột truy vấn nhiều | ✅ Đầy đủ 6 index được giải trình ở mục 2.2 |
| 5 | Dùng khóa nghiệp vụ làm PK | ✅ Dùng `BIGSERIAL` làm PK; `phone`, `serial_no`, `ticket_code` chỉ đặt UNIQUE |

---

### 2. Kịch bản SQL DDL Skeleton (PostgreSQL 15 / 16)

Mã nguồn SQL DDL tạo cấu trúc cơ sở dữ liệu tuân thủ chuẩn 3NF, áp dụng khóa nhân tạo (`BIGSERIAL`) làm khóa chính, khóa tự nhiên đặt `UNIQUE`, tích hợp đầy đủ ràng buộc `CHECK constraint` thi hành trực tiếp quy tắc nghiệp vụ ở tầng lưu trữ:

```sql
-- 1. Bảng Khách hàng (Thực thi quy tắc QT-01 với UNIQUE phone)
CREATE TABLE customer (
    customer_id BIGSERIAL PRIMARY KEY,
    full_name   VARCHAR(120) NOT NULL,
    phone       VARCHAR(20)  NOT NULL UNIQUE,  -- QT-01: Khóa nghiệp vụ duy nhất
    email       VARCHAR(120),
    address     VARCHAR(255),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Bảng Danh mục Nhóm sự cố
CREATE TABLE issue_category (
    category_id      SERIAL PRIMARY KEY,
    category_name    VARCHAR(60) NOT NULL UNIQUE, -- MAN_HINH, PIN, SAC, PHAN_MEM, NUOC_VAO, KHAC
    default_priority VARCHAR(20) NOT NULL CHECK (default_priority IN ('CAO', 'TRUNG_BINH', 'THAP')),
    is_active        BOOLEAN NOT NULL DEFAULT TRUE
);

-- 3. Bảng Thiết bị
CREATE TABLE device (
    device_id       BIGSERIAL PRIMARY KEY,
    customer_id     BIGINT NOT NULL,
    serial_no       VARCHAR(50) NOT NULL UNIQUE,   -- Số Serial / IMEI
    purchase_date   DATE,
    warranty_months SMALLINT NOT NULL DEFAULT 12 CHECK (warranty_months > 0),
    CONSTRAINT fk_device_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE RESTRICT
);

-- 4. Bảng Phiếu bảo hành (Bảng trung tâm)
CREATE TABLE ticket (
    ticket_id   BIGSERIAL PRIMARY KEY,
    ticket_code VARCHAR(30) NOT NULL UNIQUE,   -- Định dạng: BH-xxxxxx/yyyy
    customer_id BIGINT NOT NULL,
    device_id   BIGINT,                        -- NULL khi chưa xác định máy
    center_id   INT NOT NULL,
    category_id INT,                           -- NULL khi phiếu chưa phân loại

    -- QT-03, AC2.2: Mô tả lỗi bắt buộc tối thiểu 10 ký tự
    issue_desc  TEXT NOT NULL CHECK (length(issue_desc) >= 10),

    -- QT-06: Mức ưu tiên chỉ nhận 3 giá trị xác định
    priority    VARCHAR(20) NOT NULL CHECK (priority IN ('CAO', 'TRUNG_BINH', 'THAP')),

    -- QT-06: Vòng đời trạng thái 1 chiều, 6 giá trị hợp lệ
    status      VARCHAR(30) NOT NULL DEFAULT 'MOI'
                CHECK (status IN ('MOI', 'DA_PHAN_CONG', 'DANG_XU_LY', 'CHO_LINH_KIEN', 'HOAN_TAT', 'DA_HUY')),

    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    due_date    TIMESTAMPTZ NOT NULL,          -- QT-04: Tự động tính theo priority
    closed_at   TIMESTAMPTZ,
    is_warranty BOOLEAN NOT NULL DEFAULT TRUE, -- QT-05: Kết quả xác minh bảo hành
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ràng buộc logic giữa 2 cột thời gian
    CONSTRAINT chk_closed_after_received CHECK (closed_at IS NULL OR closed_at >= received_at),

    CONSTRAINT fk_ticket_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE RESTRICT,
    CONSTRAINT fk_ticket_device   FOREIGN KEY (device_id)   REFERENCES device(device_id) ON DELETE SET NULL,
    CONSTRAINT fk_ticket_category FOREIGN KEY (category_id) REFERENCES issue_category(category_id) ON DELETE RESTRICT,
    CONSTRAINT fk_ticket_center   FOREIGN KEY (center_id)   REFERENCES service_center(center_id) ON DELETE RESTRICT
);

-- 5. Bảng Lịch sử chuyển trạng thái (QT-06)
CREATE TABLE ticket_status_log (
    log_id      BIGSERIAL PRIMARY KEY,
    ticket_id   BIGINT NOT NULL,
    from_status VARCHAR(30),                   -- NULL khi tạo lần đầu
    to_status   VARCHAR(30) NOT NULL,
    changed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    changed_by  VARCHAR(100) NOT NULL,         -- Định danh nhân viên (VD: RECEPTIONIST-01)
    note        VARCHAR(255),
    CONSTRAINT fk_log_ticket FOREIGN KEY (ticket_id) REFERENCES ticket(ticket_id) ON DELETE CASCADE
);
```

#### 2.2 Bảng giải trình Index ↔ Yêu cầu phi chức năng (NFR & US):

| Tên Index | Các cột tham gia | Phục vụ yêu cầu | Giải trình kỹ thuật & Đánh đổi |
|---|---|---|---|
| `idx_customer_phone` | `customer(phone)` | **NFR1, US1, QT-01** | Tra cứu hồ sơ khách hàng theo SĐT < 500 ms trên 67.037 bản ghi bằng B-Tree Index O(log N). Đánh đổi: Thêm chi phí ghi khi tạo khách mới, chấp nhận được vì đọc nhiều hơn ghi. |
| `idx_ticket_status_due` | `ticket(status, due_date)` | **NFR1, FR6, FR7, US6, US7** | Composite Index tối ưu hóa truy vấn lọc phiếu theo trạng thái VÀ sắp xếp theo hạn cam kết SLA trong một lần quét duy nhất. Tránh in-memory sort khi bảng phình to. |
| `idx_ticket_code` | `ticket(ticket_code)` | **US2, FR9, NFR1** | Tra cứu chi tiết phiếu bảo hành theo mã biên nhận vật lý O(1) khi khách mang biên nhận đến đối chiếu. |
| `idx_ticket_center` | `ticket(center_id)` | **FR6, US6** | Lọc khối lượng công việc theo chi nhánh cho Quản lý trung tâm mà không quét toàn bộ bảng. |
| `idx_device_serial` | `device(serial_no)` | **FR8, QT-05** | Đối soát thiết bị theo số IMEI/Serial trong bước xác minh điều kiện bảo hành. |
| `idx_status_log_ticket` | `ticket_status_log(ticket_id, changed_at)` | **FR5, US5, NFR3** | Composite Index hiển thị toàn bộ dòng thời gian lịch sử trạng thái theo thứ tự thời gian mà không tốn chi phí quét toàn bộ bảng log. Đánh đổi: Tăng nhẹ chi phí ghi khi chuyển trạng thái. |

---

### 3. Bảng đối chiếu hai chiều: Wireframe ↔ ERD ↔ SRS

Kiểm tra tính nhất quán giữa 3 màn hình giao diện (docs/wireframes.html), mô hình dữ liệu (ERD) và đặc tả yêu cầu (srs.md). Mọi trường trên màn hình phải trỏ về đúng một cột trong CSDL, và mọi cột NOT NULL của `ticket` phải được nhập từ form hoặc do hệ thống tự sinh.

#### Màn hình 1: Danh sách phiếu bảo hành (UC4 — FR6 / FR7 / US6 / US7)

| Phần tử trên Wireframe | Cột trong ERD | Yêu cầu SRS |
|---|---|---|
| Bộ lọc trạng thái (dropdown) | `ticket.status` | FR6, US6 |
| Bộ lọc trung tâm | `ticket.center_id` → `service_center` | FR6, US6 |
| Mã phiếu (ticket code) | `ticket.ticket_code` | FR2, US2 |
| Khách hàng | `customer.full_name` (JOIN) | FR1 |
| Mức ưu tiên (badge màu) | `ticket.priority` | FR2, US2 |
| Trạng thái hiện tại (badge) | `ticket.status` | FR3, US3 |
| Hạn cam kết SLA | `ticket.due_date` | FR4, US4, QT-04 |
| Cảnh báo quá hạn (badge đỏ) | `ticket.due_date` so với `NOW()` | FR7, US7, NFR1 |
| Phân trang (Trang 1/N) | `OFFSET/LIMIT` tại tầng CSDL | NFR1 |

#### Màn hình 2: Tạo phiếu bảo hành mới (UC2 — FR2 / US2)

| Phần tử trên Wireframe | Cột trong ERD | Yêu cầu SRS |
|---|---|---|
| Ô nhập số điện thoại + nút Tra cứu | `customer.phone` (UNIQUE) | FR1, US1, QT-01 |
| Họ tên khách (tự điền) | `customer.full_name` | FR1 |
| Serial / IMEI thiết bị | `device.serial_no` | FR2, FR8, QT-05 |
| Trung tâm tiếp nhận (dropdown) | `ticket.center_id` → `service_center` | FR2 |
| Nhóm sự cố (dropdown 6 nhóm) | `ticket.category_id` → `issue_category` | FR2, US2 |
| Mức ưu tiên (radio) | `ticket.priority` CHECK IN | FR2, US2 |
| Mô tả sự cố (textarea ≥10 ký tự) | `ticket.issue_desc` CHECK length>=10 | FR2, US2, QT-03, AC2.2 |
| Thông báo lỗi (hết bảo hành) | — (logic tại Service, `is_warranty=false`) | FR8, QT-05 |
| *(Hệ thống tự sinh)* Mã phiếu | `ticket.ticket_code` | FR2, US2 |
| *(Hệ thống tự sinh)* Hạn SLA | `ticket.due_date` (QT-04) | FR4, US4 |
| *(Hệ thống tự sinh)* Trạng thái | `ticket.status` DEFAULT 'MOI' | FR2, QT-06 |
| *(Hệ thống tự ghi)* Log khởi tạo | `ticket_status_log` 1 bản ghi | FR5, US5, NFR3 |

#### Màn hình 3: Chi tiết & Xử lý phiếu (UC3 — FR3 / FR5 / US3 / US5)

| Phần tử trên Wireframe | Cột trong ERD | Yêu cầu SRS |
|---|---|---|
| Toàn bộ thông tin phiếu | Bảng `ticket` (tất cả cột) | FR6 |
| Thông tin khách hàng | `customer.full_name`, `customer.phone` | FR1 |
| Thông tin thiết bị | `device.serial_no`, `device.purchase_date` | FR8, QT-05 |
| Tình trạng bảo hành (pill) | `ticket.is_warranty` | FR8, QT-05 |
| Hạn cam kết SLA & bộ đếm giờ | `ticket.due_date` | FR4, FR7, US7 |
| Dropdown chuyển trạng thái | `ticket.status` + vòng đời QT-06 | FR3, US3 |
| Dòng thời gian kiểm toán | `ticket_status_log` (JOIN theo `ticket_id`) | FR5, US5, NFR3 |
| Nút In biên nhận | — (sinh file in từ dữ liệu `ticket`) | FR9, US9 |

---

### 4. Hợp đồng API (API Contract Specification)

Đặc tả kỹ thuật giao tiếp giữa Frontend và Backend, làm căn cứ nghiệm thu và thiết lập bộ kiểm thử tự động.

#### 4.1 Danh mục Endpoint chính của Luồng L2

| Phương thức | Đường dẫn URL Endpoint | Mục đích nghiệp vụ | User Story tương ứng |
| :---: | :--- | :--- | :---: |
| `GET` | `/api/customers?phone={phone}` | Tra cứu hồ sơ khách hàng theo số điện thoại (QT-01) | **US1** (MUST) |
| `POST` | `/api/customers` | Đăng ký mới hồ sơ khách hàng khi chưa tồn tại | **US1, US2** |
| `GET` | `/api/devices/{serial}/warranty` | Đối soát dữ liệu bảo hành thiết bị từ hệ thống ERP (QT-05) | **US8** (COULD) |
| `POST` | `/api/tickets` | Khởi tạo phiếu tiếp nhận bảo hành mới (FR2, QT-04) | **US2, US4** (MUST) |
| `GET` | `/api/tickets?status=&center_id=&page=` | Truy vấn danh sách phiếu (hỗ trợ lọc và phân trang) | **US6** (SHOULD) |
| `GET` | `/api/tickets?overdue=true` | Lấy danh sách phiếu sắp hoặc đã quá hạn SLA | **US7** (COULD) |
| `GET` | `/api/tickets/{id}` | Xem chi tiết phiếu kèm dòng thời gian lịch sử trạng thái | **US5** (SHOULD) |
| `PATCH` | `/api/tickets/{id}/status` | Cập nhật trạng thái phiếu và ghi nhật ký kiểm toán (QT-06) | **US3, US5** (MUST) |
| `GET` | `/api/categories` | Lấy danh mục 6 nhóm lỗi từ issue_category | **US2** (MUST) |
| `GET` | `/api/centers` | Lấy danh mục 6 trung tâm bảo hành từ service_center | **US6** (SHOULD) |

#### 4.2 Đặc tả chi tiết Endpoint: `POST /api/tickets`

**Request Body (JSON):**
```json
{
  "customer_id": 1024,
  "device_id": 3311,
  "center_id": 1,
  "category_id": 2,
  "priority": "CAO",
  "issue_desc": "Máy sập nguồn khi pin còn 20%, cắm sạc thì thân máy nóng rát"
}
```

**Response 201 Created (Khởi tạo thành công kèm SLA tự động theo QT-04):**
```json
{
  "success": true,
  "message": "Tạo phiếu bảo hành thành công",
  "data": {
    "ticket_id": 1001,
    "ticket_code": "BH-000231/2026",
    "status": "MOI",
    "priority": "CAO",
    "received_at": "2026-09-08T14:30:00+07:00",
    "due_date": "2026-09-09T14:30:00+07:00",
    "is_warranty": true
  }
}
```

**Response 400 Bad Request (Dữ liệu không hợp lệ):**
```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Dữ liệu gửi lên không thỏa mãn quy tắc kiểm tra",
    "fields": {
      "issue_desc": "Mô tả sự cố là trường bắt buộc và phải có từ 10 ký tự trở lên"
    }
  }
}
```

#### 4.3 Bảng quy tắc Validation chi tiết

| Tên trường | Bắt buộc | Kiểu dữ liệu / Ràng buộc | Thông báo lỗi khi vi phạm |
| :--- | :---: | :--- | :--- |
| `customer_id` | Có | Số nguyên dương, tồn tại trong bảng `customer` | Không tìm thấy hồ sơ khách hàng |
| `device_id` | Có | Số nguyên dương, phải thuộc quyền sở hữu của khách | Thiết bị không thuộc sở hữu của khách hàng này |
| `center_id` | Có | Số nguyên dương từ 1 đến 6 (thuộc `service_center`) | Mã trung tâm tiếp nhận không hợp lệ |
| `category_id` | Có | Số nguyên từ 1 đến 6 (thuộc `issue_category`) | Nhóm sự cố không tồn tại trong danh mục |
| `priority` | Có | Enum: `CAO`, `TRUNG_BINH`, `THAP` | Mức ưu tiên không hợp lệ (cho phép: CAO, TRUNG_BINH, THAP) |
| `issue_desc` | Có | Kiểu chuỗi, độ dài tối thiểu từ 10 đến 2000 ký tự | Mô tả sự cố là trường bắt buộc và phải có từ 10 ký tự trở lên |
