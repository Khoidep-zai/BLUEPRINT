# ĐẶC TẢ YÊU CẦU PHẦN MỀM (SRS) RÚT GỌN
## Luồng L2: Tiếp nhận và phân loại yêu cầu bảo hành

- **Học phần:** Chuyên đề Tốt nghiệp 1 (CDTN1)
- **Sinh viên thực hiện:** Nguyễn Bá Anh Khôi
- **MSSV:** 2374802010247
- **Track:** Kỹ thuật phần mềm (Software Engineering - SE)
- **Hệ thống:** Mekong Mobile CRM

---

### 1. Giới thiệu và phạm vi

**1.1 Bối cảnh doanh nghiệp và vấn đề thực tế:**  
Mekong Mobile là chuỗi bán lẻ thiết bị di động và cung cấp dịch vụ kỹ thuật sửa chữa quy mô lớn tại khu vực phía Nam với **24 cửa hàng bán lẻ** và **6 trung tâm tiếp nhận bảo hành (TTBH)**. Hiện tại, toàn bộ quy trình tiếp nhận bảo hành tại các quầy lễ tân đang sử dụng phiếu ghi chép thủ công trên giấy hoặc nhập rời rạc vào các file bảng tính Excel nội bộ.

Thực trạng này gây ra 3 điểm nghẽn nghiệp vụ nghiêm trọng:
- **Thất thoát và sai lệch dữ liệu:** Phiếu giấy dễ thất lạc, khó tra cứu lịch sử mua hàng và lịch sử bảo hành trước đây của thiết bị.
- **Trùng lặp hồ sơ khách hàng:** Dữ liệu khách hàng bị trùng lặp khoảng 20% do nhân viên tại các chi nhánh nhập sai hoặc nhập nhiều lần cùng một số điện thoại.
- **Vi phạm cam kết hạn trả máy (SLA):** Tỷ lệ phiếu bảo hành bị trễ hạn cam kết lên tới ~14.6% do phân loại lỗi cảm tính, không có cơ chế tự động ấn định thời gian hoàn tất theo giờ làm việc thực tế.

Dự án Smart CRM Mekong Mobile được triển khai nhằm số hóa toàn diện quy trình tiếp nhận, lưu trữ tập trung dữ liệu bảo hành và tự động hóa kiểm soát tiến độ xử lý.

**1.2 Luồng nghiệp vụ lựa chọn:**  
Báo cáo này tập trung phân tích và thiết kế chuyên sâu cho **Luồng L2: Tiếp nhận và phân loại yêu cầu bảo hành** (Warranty Reception & Issue Categorization). Luồng nghiệp vụ này đóng vai trò là cửa ngõ đầu vào (Entry-point) của toàn bộ phân hệ sau bán hàng, chịu trách nhiệm nhận diện khách hàng, xác minh thời hạn bảo hành của thiết bị, ghi nhận mô tả sự cố kỹ thuật, tự động tính toán hạn cam kết SLA và khởi tạo phiếu tiếp nhận điện tử thay thế hoàn toàn cho phiếu giấy thủ công.

**1.3 Danh mục các chức năng chủ ý KHÔNG làm (WON'T - MoSCoW):**
- Không làm chức năng tự động phân công kỹ thuật viên (Dispatching) → thuộc Luồng L4.
- Không quản lý tồn kho và xuất nhập linh kiện thay thế → thuộc Luồng L5.
- Không xử lý giao dịch thanh toán chi phí sửa chữa dịch vụ.
- Không gửi tin nhắn SMS Brandname hoặc Email tự động cho khách hàng → thuộc Luồng L1.
- Không quản lý khảo sát và giải quyết khiếu nại khách hàng → thuộc Luồng L8.

**1.4 Bảng thuật ngữ nghiệp vụ chuẩn hóa (Business Glossary):**

| Thuật ngữ | Định nghĩa | Tên kỹ thuật gợi ý |
| :--- | :--- | :--- |
| **Khách hàng** | Cá nhân đã mua ít nhất một sản phẩm hoặc sử dụng dịch vụ của Mekong Mobile. | `customer` |
| **Thiết bị** | Một máy cụ thể mà khách hàng sở hữu, xác định bằng số serial hoặc IMEI. | `device` |
| **Phiếu bảo hành** | Yêu cầu bảo hành được ghi nhận, có mã duy nhất và vòng đời trạng thái. | `ticket` |
| **Trạng thái phiếu** | Vị trí hiện tại: MỚI → ĐÃ PHÂN CÔNG → ĐANG XỬ LÝ → ĐÃ HỦY. | `ticket_status` |
| **Hạn cam kết** | Thời điểm chậm nhất phải hoàn tất phiếu, tính từ lúc tiếp nhận theo mức ưu tiên (SLA). | `due_date` |
| **Nhóm sự cố** | Phân loại nguyên nhân bảo hành: MÀN HÌNH, PIN, SẠC, PHẦN MỀM, NƯỚC VÀO, KHÁC. | `issue_category` |
| **Mức ưu tiên** | Mức khẩn của phiếu: CAO (24h), TRUNG_BÌNH (72h), THẤP (120h). | `priority` |

---

### 2. Các bên liên quan và vai trò (Stakeholders & Actors)

Hệ thống xác định **2 tác nhân người dùng nội bộ** trực tiếp tham gia tương tác và **1 tác nhân hệ thống ngoại vi**:

1. **Nhân viên tiếp nhận (Receptionist — Quầy lễ tân):**
   - *Phạm vi quyền hạn:* Tìm kiếm hồ sơ khách hàng, tạo phiếu bảo hành mới, cập nhật trạng thái phiếu (các bước đầu), phân loại nhóm sự cố.
   - *Trách nhiệm:* Tiếp nhận khách hàng, kiểm tra tính hợp lệ của thiết bị và đảm bảo ghi nhận đúng mô tả lỗi từ khách hàng để tạo phiếu bảo hành.
   - *Use Case liên quan:* UC1, UC2, UC3, UC4.

2. **Quản lý trung tâm (Center Manager):**
   - *Phạm vi quyền hạn:* Xem toàn bộ phiếu bảo hành thuộc trung tâm quản lý, phê duyệt các phiếu chưa xác minh bảo hành, giám sát cảnh báo quá hạn.
   - *Trách nhiệm:* Theo dõi tiến độ các phiếu bảo hành, đảm bảo các phiếu không bị quá hạn cam kết.
   - *Use Case liên quan:* UC4, UC5.

3. **Hệ thống ERP / Kho bán lẻ `<<System>>`:**
   - Hệ thống ngoại vi cung cấp dữ liệu xác minh thông tin IMEI và Hóa đơn mua hàng.
   - *Use Case liên quan:* UC2 (include Xác minh hạn bảo hành thiết bị).

---

### 3. Yêu cầu chức năng (Functional Requirements)

#### 3.1 Bảng danh mục yêu cầu chức năng (FR)

| Mã FR | Tên yêu cầu chức năng | Nội dung chi tiết | Dạng kiểm chứng |
| :--- | :--- | :--- | :--- |
| **FR1** | Tra cứu hồ sơ khách hàng & thiết bị | Cho phép tìm kiếm hồ sơ khách hàng theo SĐT (QT-01) hoặc số IMEI/Serial; tự động tải danh sách thiết bị đã mua. | Nhập SĐT hợp lệ → hiển thị thông tin khách hàng và thiết bị. Nhập SĐT mới → hiển thị nút tạo mới. |
| **FR2** | Khởi tạo phiếu tiếp nhận bảo hành | Ghi nhận hồ sơ thiết bị, nhóm sự cố, mô tả lỗi, mức ưu tiên và lưu trữ vào CSDL với mã phiếu duy nhất dạng `BH-xxxxxx/yyyy`. | Bấm "Lưu phiếu" với dữ liệu hợp lệ → bản ghi `ticket` được tạo, trả về HTTP 201 kèm mã phiếu. |
| **FR3** | Cập nhật trạng thái phiếu tiếp nhận | Chuyển đổi trạng thái phiếu từ MỚI sang ĐÃ PHÂN CÔNG hoặc ĐÃ HỦY theo quy tắc vòng đời một chiều (QT-06). | Thực hiện đổi trạng thái hợp lệ → cập nhật `ticket.status` thành công; thử chuyển ngược chiều → bị chặn. |
| **FR4** | Tự động tính toán hạn cam kết SLA | Tự động ấn định `due_date` dựa trên mức ưu tiên (CAO: 24h, TRUNG_BÌNH: 72h, THẤP: 120h) và loại trừ ngày Chủ Nhật (QT-04). | Tạo phiếu vào Thứ Bảy lúc 10:00 mức CAO → hệ thống gán `due_date` là Thứ Hai lúc 10:00. |
| **FR5** | Ghi nhật ký kiểm toán trạng thái | Tự động ghi lại lịch sử mỗi lần trạng thái phiếu thay đổi trong một Database Transaction toàn vẹn (ACID). | Đổi trạng thái phiếu → bảng `ticket_status_log` tăng 1 bản ghi có đủ `from_status`, `to_status`, `changed_by`. |
| **FR6** | Tra cứu & Lọc danh sách phiếu bảo hành | Cung cấp giao diện lọc phiếu theo trạng thái (MỚI, ĐÃ PHÂN CÔNG...), theo trung tâm tiếp nhận và hỗ trợ phân trang. | Chọn bộ lọc `status = 'MOI'` và `center_id = 1` → danh sách trả về đúng các phiếu thỏa điều kiện. |
| **FR7** | Giám sát và cảnh báo quá hạn SLA | Đánh dấu trực quan các phiếu sắp chạm hạn (còn dưới 4 giờ) hoặc đã quá hạn cam kết để quản lý can thiệp. | Phiếu có `now() > due_date` và chưa hoàn tất → hiển thị badge cảnh báo màu đỏ "QUÁ HẠN". |
| **FR8** | Xác minh điều kiện bảo hành thiết bị | Đối soát số IMEI/Serial với hệ thống ERP/Core để kiểm tra ngày mua và tính toán thời hạn bảo hành còn lại (QT-05). | Nhập IMEI hợp lệ → hiển thị thời hạn bảo hành còn lại; không tìm thấy → đánh dấu "Chưa xác minh". |
| **FR9** | In phiếu biên nhận bảo hành | Xuất định dạng in ấn phiếu tiếp nhận biên nhận bàn giao thiết bị có mã vạch/mã phiếu giao cho khách hàng giữ. | Bấm nút "In biên nhận" → mở hộp thoại in mẫu phiếu khổ A5 chứa đầy đủ thông tin cam kết và điều khoản. |

---

#### 3.2 Danh sách User Story chuẩn INVEST & Tiêu chí chấp nhận MoSCoW

Toàn bộ 9 User Story dưới đây đều tuân thủ chuẩn INVEST (Độc lập, Thương lượng được, Có giá trị, Ước lượng được, Nhỏ gọn, Kiểm thử được), không mắc 4 lỗi thường gặp (không mơ hồ, đo lường được, chỉ chứa 1 mục tiêu/câu, không nêu giải pháp công nghệ).

| Mã | Vai trò | Mục tiêu | Giá trị nghiệp vụ | MoSCoW |
| :---: | :--- | :--- | :--- | :---: |
| **US1** | Là nhân viên tiếp nhận | tôi muốn tra cứu khách hàng bằng số điện thoại | để nhanh chóng tải lại thông tin và lịch sử thiết bị mà không cần nhập thủ công lại từ đầu. | **MUST** |
| **US2** | Là nhân viên tiếp nhận | tôi muốn khởi tạo phiếu tiếp nhận bảo hành điện tử | để số hóa hồ sơ tiếp nhận, ghi nhận chính xác lỗi máy và bàn giao thiết bị vào quy trình sửa chữa. | **MUST** |
| **US3** | Là nhân viên tiếp nhận | tôi muốn cập nhật trạng thái phiếu từ MỚI sang ĐÃ PHÂN CÔNG | để chuyển giao trách nhiệm xử lý sang bộ phận kỹ thuật viên một cách rõ ràng. | **MUST** |
| **US4** | Là hệ thống | tôi muốn tự động tính hạn cam kết hoàn tất (due date) dựa theo mức ưu tiên sự cố và trừ ngày nghỉ Chủ Nhật | để chuẩn hóa cam kết thời gian trả máy cho khách và làm mốc đo lường SLA kỹ thuật. | **SHOULD** |
| **US5** | Là hệ thống | tôi muốn tự động ghi nhận nhật ký kiểm toán mỗi lần phiếu chuyển đổi trạng thái | để đảm bảo tính minh bạch, truy vết được ai đã thay đổi, vào thời điểm nào và lý do gì. | **SHOULD** |
| **US6** | Là quản lý trung tâm | tôi muốn xem danh sách phiếu tiếp nhận có phân trang và bộ lọc theo trạng thái, trung tâm | để bao quát toàn bộ khối lượng công việc hiện có của trung tâm trong ngày. | **SHOULD** |
| **US7** | Là quản lý trung tâm | tôi muốn nhận cảnh báo trực quan về các phiếu bảo hành sắp hoặc đã quá hạn cam kết | để kịp thời điều phối nguồn lực ưu tiên xử lý, giảm thiểu tỷ lệ vi phạm SLA với khách hàng. | **COULD** |
| **US8** | Là nhân viên tiếp nhận | tôi muốn hệ thống tự động đối soát số IMEI với dữ liệu bán lẻ | để xác định chính xác ngày mua và trạng thái còn hay hết hạn bảo hành của thiết bị. | **COULD** |
| **US9** | Là nhân viên tiếp nhận | tôi muốn in phiếu biên nhận bàn giao thiết bị sau khi lưu | để cung cấp chứng từ vật lý có mã số tiếp nhận cho khách hàng giữ đối chiếu khi nhận máy. | **COULD** |

##### Tiêu chí chấp nhận (Given - When - Then) chi tiết cho các User Story MUST:

**1. US1: Tra cứu hồ sơ khách hàng bằng số điện thoại (Mức MUST)**
- **AC1.1 (Luồng chính - Khách hàng đã tồn tại):**  
  *GIVEN* khách hàng đọc số điện thoại hợp lệ `0901234567` đã có trong hệ thống Mekong Mobile,  
  *WHEN* nhân viên tiếp nhận nhập số điện thoại vào ô tra cứu và bấm nút "Tra cứu",  
  *THEN* hệ thống tải và hiển thị chính xác họ tên, địa chỉ liên hệ và danh sách các thiết bị đã từng mua kèm tình trạng bảo hành trong vòng dưới 500ms.
- **AC1.2 (Luồng ngoại lệ - Khách hàng mới chưa có trong hệ thống):**  
  *GIVEN* khách hàng đọc số điện thoại `0988776655` chưa từng lưu trong cơ sở dữ liệu,  
  *WHEN* nhân viên tiếp nhận nhập số điện thoại và bấm nút "Tra cứu",  
  *THEN* hệ thống hiển thị thông báo "Khách hàng mới! Chưa có trong hệ thống" và tự động mở khóa các ô nhập liệu Họ tên, Địa chỉ để nhân viên tạo hồ sơ mới ngay trên màn hình.
- **AC1.3 (Luồng ngoại lệ - Số điện thoại không đúng định dạng):**  
  *GIVEN* nhân viên nhập số điện thoại sai quy cách (chứa chữ cái, ký tự đặc biệt hoặc ít hơn 10 chữ số),  
  *WHEN* nhân viên bấm nút "Tra cứu",  
  *THEN* hệ thống chặn gửi yêu cầu, viền đỏ trường nhập và hiển thị thông báo lỗi "Số điện thoại không hợp lệ, vui lòng nhập đúng 10 chữ số di động".

**2. US2: Khởi tạo phiếu tiếp nhận bảo hành điện tử (Mức MUST)**
- **AC2.1 (Luồng chính - Tạo phiếu thành công):**  
  *GIVEN* nhân viên đã chọn khách hàng hợp lệ, chọn thiết bị thuộc sở hữu khách, chọn nhóm sự cố "PIN", mức ưu tiên "CAO" và nhập mô tả lỗi hợp lệ ("Máy sập nguồn khi pin còn 20%, cắm sạc thì thân máy nóng rát"),  
  *WHEN* nhân viên bấm nút "Lưu & Khởi tạo phiếu tiếp nhận",  
  *THEN* hệ thống lưu bản ghi vào bảng `ticket`, tự động tính `due_date` sau 24h làm việc, sinh mã phiếu dạng `BH-xxxxxx/yyyy`, ghi vết khởi tạo vào `ticket_status_log` và hiển thị thông báo thành công.
- **AC2.2 (Luồng ngoại lệ - Mô tả lỗi quá ngắn hoặc để trống):**  
  *GIVEN* nhân viên tiếp nhận để trống trường mô tả sự cố hoặc nhập dưới 10 ký tự (ví dụ: "hư máy"),  
  *WHEN* nhân viên bấm nút "Lưu & Khởi tạo phiếu tiếp nhận",  
  *THEN* hệ thống từ chối lưu, hiển thị thông báo lỗi xác thực "Mô tả sự cố là trường bắt buộc và phải có từ 10 ký tự trở lên" và giữ nguyên dữ liệu đã nhập trên form.
- **AC2.3 (Luồng ngoại lệ - Thiết bị không thuộc hồ sơ khách hàng đã chọn):**  
  *GIVEN* mã thiết bị truyền lên không trùng khớp với danh sách thiết bị thuộc quyền sở hữu của `customer_id` hiện tại,  
  *WHEN* API khởi tạo phiếu nhận được request,  
  *THEN* hệ thống trả về mã lỗi HTTP 400 Bad Request kèm thông điệp "Thiết bị không thuộc sở hữu của khách hàng này" và hoàn tác toàn bộ giao dịch.

**3. US3: Cập nhật trạng thái phiếu tiếp nhận bảo hành (Mức MUST)**
- **AC3.1 (Luồng chính - Chuyển tiếp trạng thái thành công):**  
  *GIVEN* phiếu bảo hành hiện đang ở trạng thái `MOI`,  
  *WHEN* nhân viên tiếp nhận chọn thao tác cập nhật sang trạng thái `DA_PHAN_CONG` và gửi yêu cầu,  
  *THEN* hệ thống cập nhật trường `status = 'DA_PHAN_CONG'` trong bảng `ticket`, đồng thời tự động chèn một bản ghi mới vào `ticket_status_log` ghi nhận đầy đủ `from_status = 'MOI'`, `to_status = 'DA_PHAN_CONG'`, mã nhân viên và mốc thời gian thực tế.
- **AC3.2 (Luồng ngoại lệ - Chuyển ngược chiều vòng đời trạng thái):**  
  *GIVEN* phiếu bảo hành hiện đang ở trạng thái `DA_PHAN_CONG` hoặc `DANG_XU_LY`,  
  *WHEN* người dùng cố gắng gửi lệnh chuyển trạng thái ngược về `MOI`,  
  *THEN* hệ thống từ chối cập nhật, trả về mã lỗi HTTP 400 và hiển thị thông báo "Quy tắc vòng đời trạng thái là một chiều: không được phép quay ngược lại trạng thái trước".

---

#### 3.3 Đặc tả Use Case chi tiết của ca sử dụng cốt lõi (UC2)

Căn cứ theo sơ đồ Use Case (`docs/usecase.drawio`), **UC2: Khởi tạo phiếu tiếp nhận bảo hành** là ca sử dụng cốt lõi nhất của luồng L2, được đặc tả chi tiết dưới đây:

| Thuộc tính | Nội dung đặc tả chi tiết |
| :--- | :--- |
| **Mã Use Case** | **UC2** |
| **Tên Use Case** | **Khởi tạo phiếu tiếp nhận bảo hành mới** |
| **Tác nhân chính** | Nhân viên tiếp nhận (Receptionist — Quầy lễ tân) |
| **Tác nhân phụ** | Hệ thống Kho bán lẻ / ERP `<<System>>` |
| **Mục tiêu nghiệp vụ** | Ghi nhận đầy đủ thông tin sự cố kỹ thuật, tự động ấn định hạn cam kết SLA và sinh mã phiếu bảo hành điện tử chính thức thay cho phiếu giấy. |
| **Điều kiện tiên quyết (Pre-conditions)** | 1. Nhân viên tiếp nhận đã đăng nhập vào hệ thống với tài khoản hợp lệ.<br>2. Đã hoàn tất bước tra cứu hoặc thêm mới hồ sơ khách hàng (UC1).<br>3. Thiết bị tiếp nhận có số IMEI/Serial xác định. |
| **Điều kiện sau (Post-conditions)** | 1. Bản ghi phiếu bảo hành được tạo mới trong CSDL với trạng thái `MOI`.<br>2. Bản ghi nhật ký khởi tạo được chèn vào bảng `ticket_status_log`.<br>3. Mã phiếu bảo hành duy nhất được cấp phát và hiển thị trên màn hình.<br>4. Kích hoạt tùy chọn in biên nhận giao cho khách hàng. |
| **User Story liên quan** | **US2** (Khởi tạo phiếu - MUST), **US4** (Tính SLA - SHOULD), **US8** (Xác minh ERP - COULD) |
| **Luồng sự kiện chính (Happy Path)** | 1. Nhân viên chọn thiết bị từ danh sách máy của khách hàng (hoặc nhập số Serial/IMEI mới).<br>2. Hệ thống gọi dịch vụ đối soát ERP để xác minh ngày mua và kiểm tra điều kiện bảo hành (QT-05).<br>3. Nhân viên lắng nghe khách hàng mô tả sự cố, sau đó chọn một Nhóm sự cố từ danh mục (MÀN HÌNH, PIN, SẠC, PHẦN MỀM, NƯỚC VÀO, KHÁC).<br>4. Hệ thống gợi ý Mức ưu tiên tương ứng và gọi thuật toán SLA Engine tự động tính toán Hạn cam kết hoàn thành (`due_date`) theo quy tắc ngày làm việc QT-04.<br>5. Nhân viên nhập mô tả chi tiết biểu hiện lỗi thực tế (tối thiểu 10 ký tự).<br>6. Nhân viên kiểm tra lại toàn bộ thông tin trên màn hình tóm tắt và nhấn nút "Lưu & Khởi tạo phiếu tiếp nhận".<br>7. Hệ thống mở một Database Transaction, lưu bản ghi vào bảng `ticket`, chèn lịch sử vào `ticket_status_log`, gán mã phiếu dạng `BH-xxxxxx/yyyy` và hiển thị thông báo thành công kèm giao diện xem chi tiết phiếu. |
| **Luồng ngoại lệ (Exceptions)** | **2a. Thiết bị đã hết hạn bảo hành hoặc không tra cứu được dữ liệu mua hàng:**<br>&nbsp;&nbsp;&nbsp;&nbsp;2a.1. Hệ thống hiển thị cảnh báo: *"Thiết bị chưa xác minh được hạn bảo hành gốc"*; cờ `is_warranty` được gán giá trị `false`.<br>&nbsp;&nbsp;&nbsp;&nbsp;2a.2. Hệ thống hiển thị tùy chọn tiếp nhận diện sửa chữa dịch vụ tính phí hoặc chuyển Quản lý trung tâm phê duyệt ngoại lệ (QT-05). Quy trình tiếp tục tại bước 3.<br><br>**5a. Mô tả sự cố bị để trống hoặc nhập dưới 10 ký tự:**<br>&nbsp;&nbsp;&nbsp;&nbsp;5a.1. Hệ thống chặn thao tác gửi dữ liệu, viền đỏ ô nhập mô tả sự cố.<br>&nbsp;&nbsp;&nbsp;&nbsp;5a.2. Hiển thị thông báo lỗi: *"Mô tả sự cố là trường bắt buộc và phải có từ 10 ký tự trở lên"*. Form giữ nguyên trạng thái để nhân viên bổ sung.<br><br>**7a. Lỗi kết nối CSDL hoặc lỗi hệ thống trong quá trình lưu:**<br>&nbsp;&nbsp;&nbsp;&nbsp;7a.1. Database Transaction tự động Rollback hoàn toàn, không tạo dữ liệu rác hay bản ghi mồ côi (NFR3).<br>&nbsp;&nbsp;&nbsp;&nbsp;7a.2. Hệ thống hiển thị thông báo: *"Không thể lưu phiếu bảo hành do sự cố mạng, vui lòng thử lại sau giây lát"*. Nhân viên không bị mất dữ liệu đã nhập trên giao diện. |

---

### 4. Yêu cầu phi chức năng (Non-Functional Requirements)

| Mã NFR | Nhóm yêu cầu | Phát biểu yêu cầu có ngưỡng định lượng cụ thể | Phương pháp kiểm chứng |
| :--- | :--- | :--- | :--- |
| **NFR1** | Hiệu năng (Performance) | Thời gian phản hồi của API tra cứu khách hàng theo SĐT (`GET /api/customers?phone=...`) phải đạt **dưới 500ms** đối với tập dữ liệu thực tế gồm **67.037 bản ghi** (đo lường ở ngưỡng phân vị P95). | Sử dụng kịch bản kiểm thử tải bằng k6 / Apache JMeter với 50 người dùng đồng thời (concurrent users) thực hiện tra cứu liên tục trong 5 phút. |
| **NFR2** | Tính khả dụng (Availability) | Phân hệ tiếp nhận bảo hành phải duy trì độ sẵn sàng tối thiểu **99.9% uptime** trong khung giờ vận hành phục vụ khách hàng (tổng thời gian gián đoạn không vượt quá 43.8 phút/tháng). | Giám sát trạng thái thông qua endpoint `GET /health` định kỳ 60 giây một lần bởi hệ thống uptime monitoring bên ngoài. |
| **NFR3** | Toàn vẹn dữ liệu (Data Integrity) | Mọi thao tác tạo phiếu hoặc đổi trạng thái phải được bao bọc trong một **Database Transaction duy nhất** tuân thủ chuẩn ACID; tỷ lệ phát sinh bản ghi mồ côi (orphan records) là **tuyệt đối 0.00%**. | Kiểm thử tích hợp tự động (Integration Test) mô phỏng ngắt kết nối giữa bước ghi bảng `ticket` và bảng `ticket_status_log` để kiểm tra rollback. |
| **NFR4** | Bảo mật & Phân quyền (Security) | Hệ thống bắt buộc phân quyền truy cập theo vai trò (Role-Based Access Control - RBAC). Chỉ nhân viên có quyền `RECEPTIONIST` mới được tạo phiếu; chỉ `CENTER_MANAGER` mới có quyền phê duyệt ngoại lệ bảo hành. | Kiểm thử bảo mật API bằng cách gửi request không kèm token hoặc giả mạo role để xác thực phản hồi mã HTTP 401 Unauthorized / HTTP 403 Forbidden. |

---

### 5. Ràng buộc và quy tắc nghiệp vụ cốt lõi (Business Rules)

- **QT-01 (Định danh khách hàng duy nhất):**  
  Số điện thoại khách hàng là khóa nghiệp vụ duy nhất trong hệ thống (`UNIQUE phone`). Khi nhân viên nhập một số điện thoại đã tồn tại, hệ thống bắt buộc phải tải hồ sơ khách hàng sẵn có thay vì tạo bản ghi mới để triệt tiêu tình trạng trùng lặp hồ sơ khách hàng giữa các chi nhánh.

- **QT-04 (Quy tắc tính toán hạn cam kết SLA):**  
  Hạn hoàn tất (`due_date`) được tính toán tự động từ thời điểm tiếp nhận (`received_at`) căn cứ theo mức ưu tiên:
  - **Mức CAO:** Hoàn thành trong **24 giờ làm việc**.
  - **Mức TRUNG_BÌNH:** Hoàn thành trong **72 giờ làm việc**.
  - **Mức THẤP:** Hoàn thành trong **120 giờ làm việc**.
  
  *Quy tắc ngày làm việc:* Trung tâm bảo hành hoạt động từ Thứ Hai đến Thứ Bảy (Chủ Nhật nghỉ làm việc). Nếu khoảng thời gian SLA cắt ngang qua ngày Chủ Nhật, hệ thống tự động cộng dồn thêm 24 giờ của ngày Chủ Nhật vào thời điểm cam kết.

- **QT-05 (Xác minh điều kiện bảo hành thiết bị):**  
  Thiết bị được công nhận là **Còn bảo hành chính hãng** khi thỏa mãn:  
  $$(Ngày\_tiếp\_nhận - Ngày\_mua) \le warranty\_months$$  
  Trường hợp thiết bị không đối soát được ngày mua trên hệ thống bán lẻ Mekong Core hoặc khách làm mất chứng từ mua hàng, phiếu bảo hành bắt buộc phải được đánh dấu trạng thái cờ `is_warranty = false` ("Chưa xác minh bảo hành") và phải được Quản lý trung tâm phê duyệt ngoại lệ trước khi bàn giao kỹ thuật viên xử lý.

- **QT-06 (Vòng đời trạng thái phiếu một chiều):**  
  Vòng đời trạng thái của phiếu bảo hành tuân thủ quy tắc chuyển đổi một chiều nghiêm ngặt:
  ```
  MỚI (MOI) → ĐÃ PHÂN CÔNG (DA_PHAN_CONG) → ĐANG XỬ LÝ (DANG_XU_LY) → HOÀN TẤT (HOAN_TAT)
                                         ↘ ĐÃ HỦY (DA_HUY)
  ```
  Tuyệt đối không cho phép quay ngược trạng thái trước đó. Mỗi lần chuyển trạng thái hợp lệ bắt buộc phải ghi nhận đồng thời 1 bản ghi vào bảng `ticket_status_log` trong cùng một giao dịch.

---

### 6. Bảng truy vết yêu cầu (Traceability Matrix)

Bảng truy vết đảm bảo 100% tính thông suốt từ Yêu cầu chức năng (FR) $\leftrightarrow$ User Story (US) $\leftrightarrow$ Ca sử dụng (Use Case) $\leftrightarrow$ Mức ưu tiên MoSCoW $\leftrightarrow$ Thành phần kiến trúc thực thi. Tuyệt đối không có ô trống.

| Yêu cầu chức năng (FR) | User Story tương ứng | Use Case tương ứng (Draw.io) | Mức ưu tiên (MoSCoW) | Thành phần kiến trúc / Module phụ trách |
| :--- | :---: | :--- | :---: | :--- |
| **FR1:** Tra cứu hồ sơ khách hàng & thiết bị | **US1** | UC1: Tra cứu hồ sơ Khách hàng & Thiết bị | **MUST** | `CustomerController`, `CustomerService`, `customer` table |
| **FR2:** Khởi tạo phiếu tiếp nhận bảo hành | **US2** | UC2: Khởi tạo phiếu tiếp nhận bảo hành | **MUST** | `TicketController`, `TicketService`, `ticket` table |
| **FR3:** Cập nhật trạng thái phiếu tiếp nhận | **US3** | UC3: Cập nhật trạng thái phiếu bảo hành | **MUST** | `TicketController`, `TicketService`, `ticket_status_log` |
| **FR4:** Tự động tính toán hạn cam kết SLA | **US4** | UC2: Khởi tạo phiếu tiếp nhận (include) | **SHOULD** | SLA Engine Module (`slaCalculator.js`), `QT-04` |
| **FR5:** Ghi nhật ký kiểm toán trạng thái | **US5** | UC3: Cập nhật trạng thái phiếu (include) | **SHOULD** | Transaction Manager, `ticket_status_log` table |
| **FR6:** Tra cứu & Lọc danh sách phiếu bảo hành | **US6** | UC4: Tra cứu & Lọc danh sách phiếu bảo hành | **SHOULD** | `TicketController.listTickets`, Database Query Filter |
| **FR7:** Giám sát và cảnh báo quá hạn SLA | **US7** | UC5: Giám sát tiến độ & Cảnh báo hạn cam kết | **COULD** | SLA Monitor Service, UI Alert Badge Component |
| **FR8:** Xác minh điều kiện bảo hành thiết bị | **US8** | UC2: Khởi tạo phiếu tiếp nhận (include) | **COULD** | ERP Integration Adapter, Device Service (`QT-05`) |
| **FR9:** In phiếu biên nhận bảo hành cho khách | **US9** | UC2: Khởi tạo phiếu tiếp nhận (extend) | **COULD** | Receipt Generator Service, Print Template Component |
