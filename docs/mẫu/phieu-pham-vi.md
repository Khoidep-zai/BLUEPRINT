# PHIẾU PHẠM VI BÀI TOÁN CÁ NHÂN

**Họ tên:** Nguyễn Bá Anh Khôi  
**MSSV:** 2374802010247  
**Track:** [X] SE [ ] DA [ ] AI  
**Học phần:** Chuyên đề Tốt nghiệp 1 (CDTN1) · HK1 2026–2027  

---

### 1. LUỒNG NGHIỆP VỤ CHỌN
*(Chọn 1 trong danh mục L1–L10 của case study Mekong Mobile)*  
- **Mã luồng:** L2  
- **Tên luồng:** Tiếp nhận và phân loại yêu cầu bảo hành  

---

### 2. PHẠM VI DIỄN ĐẠT BẰNG MỘT CÂU
*(Ai làm gì, theo trình tự nào, kết thúc ở đâu — theo khuôn ví dụ "VỪA ĐỦ" buổi 1)*  
> **Nhân viên tiếp nhận tạo phiếu bảo hành từ thông tin khách hàng cung cấp, phân loại theo loại sự cố/lỗi, ghi nhận dữ liệu bắt buộc, cập nhật trạng thái ban đầu của phiếu và lưu vào hệ thống để sẵn sàng chuyển sang bước phân công kỹ thuật viên.**

---

### 3. DANH SÁCH SƠ BỘ 5–7 USER STORY DỰ KIẾN
- **US1:** Là nhân viên tiếp nhận, tôi muốn tạo phiếu bảo hành mới để ghi nhận đầy đủ thông tin yêu cầu của khách hàng.
- **US2:** Là nhân viên tiếp nhận, tôi muốn tra cứu thông tin khách hàng và lịch sử mua hàng / bảo hành của sản phẩm (qua SĐT / Serial / IMEI) để kiểm tra điều kiện tiếp nhận.
- **US3:** Là nhân viên tiếp nhận, tôi muốn phân loại phiếu theo loại sự cố (và cập nhật thông tin liên quan) để phiếu được đưa vào đúng luồng xử lý.
- **US4:** Là nhân viên tiếp nhận, tôi muốn cập nhật trạng thái phiếu (ví dụ: Mới → Chờ phân công) và ghi lại lịch sử trạng thái để theo dõi được vòng đời phiếu.
- **US5:** Là nhân viên tiếp nhận, tôi muốn xem danh sách phiếu theo trạng thái / ngày tạo / cửa hàng để quản lý công việc hàng ngày.
- **US6:** Là hệ thống, tôi muốn kiểm tra dữ liệu bắt buộc (NOT NULL / validation) khi tạo hoặc cập nhật phiếu để đảm bảo dữ liệu hợp lệ trước khi lưu.
- **US7 (Tùy chọn):** Là nhân viên tiếp nhận, tôi muốn xem chi tiết một phiếu bảo hành (bao gồm lịch sử trạng thái) để hỗ trợ khách hàng khi cần.

---

### 4. DỮ LIỆU SẼ LÀM VIỆC
- [ ] Sinh mô phỏng  
- [X] Dùng dữ liệu mẫu của case study  
- **Ước lượng số bản ghi cần thiết:** Khoảng 200–500 phiếu bảo hành (cùng dữ liệu khách hàng / sản phẩm / cửa hàng liên quan theo Mục 11 của case study Mekong Mobile).

---

### 5. CÔNG NGHỆ DỰ KIẾN
*(Ngôn ngữ / framework / CSDL hoặc công cụ chính)*  
- **Ngôn ngữ / Runtime:** Node.js 20 LTS
- **Framework API:** Express (hoặc NestJS)
- **Truy cập dữ liệu (ORM):** Prisma (hoặc Sequelize)
- **Cơ sở dữ liệu:** PostgreSQL 16 (có thể dùng SQLite giai đoạn đầu nếu máy yếu)
- **Giao diện:** React (Vite) hoặc Vue (Vite)
- **Kiểm thử:** Jest / Vitest
- **Tài liệu API:** Swagger UI
- **Đóng gói (BT3):** Dockerfile + docker-compose
