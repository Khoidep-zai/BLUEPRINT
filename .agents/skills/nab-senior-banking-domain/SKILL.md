---
name: nab-senior-banking-domain
description: Encodes National Australia Bank (NAB) senior-level banking domain rules, Australian regulatory compliance (APRA CPS 234/230, CDR Open Banking, NPP/ISO 20022, AUSTRAC), core banking ledger integrity, and Senior Java financial engineering standards. Use when working as BA, QA, QC, Tester, TechLead, or Java Dev on any NAB banking feature or financial report.
---

# NAB Senior Banking & Financial Engineering Skill

## Overview
Skill này cung cấp bộ quy tắc nghiệp vụ Kinh tế - Ngân hàng cấp độ **Senior** tại **NAB (National Australia Bank)** cùng các tiêu chuẩn kỹ thuật bắt buộc cho đội ngũ **BA, QA, QC, Tester, TechLead và Dev (Java)**. Mọi thiết kế đặc tả, mã nguồn Java, kịch bản kiểm thử và báo cáo Office (`.docx`, `.xlsx`, `.pptx`) trong dự án `C:\O E\NAB` phải tuân thủ nghiêm ngặt các quy định dưới đây.

## When to Use
- Khi **BA** phân tích yêu cầu nghiệp vụ ngân hàng, tính toán hiệu quả kinh tế, viết PRD/User Story.
- Khi **TechLead** thiết kế kiến trúc Microservices, API, Database và hệ thống giám sát tại NAB.
- Khi **Dev (Java)** lập trình logic tính toán tiền tệ, lãi suất, thanh toán, sổ cái (Ledger) và tích hợp API.
- Khi **Tester / QC / QA** viết kịch bản kiểm thử, đối chiếu Spec-to-Code và kiểm toán tuân thủ trước khi Go-Live.

---

## Process & Mandatory Banking Standards

### 1. Tuân thủ Quy định Ngân hàng Liên bang Úc (Australian Regulatory & NAB Compliance)
Mọi tính năng được xây dựng hoặc phân tích tại NAB phải vượt qua 5 chốt chặn pháp lý sau:
1. **APRA CPS 234 (Information Security):**
   - Dữ liệu nhạy cảm của khách hàng (PII, TFN - Tax File Number, số thẻ PAN, thông tin tài khoản) **tuyệt đối không được ghi ra Log (Structured Logs)** dưới dạng rõ (Plaintext). Phải thực hiện Data Masking / Tokenization.
   - Phân tách quyền hạn nghiêm ngặt (Zero Trust, OAuth2 / OIDC / mTLS giữa các Microservices nội bộ).
2. **APRA CPS 230 (Operational Risk Management):**
   - Mọi dịch vụ quan trọng (Critical Operations) phải có cơ chế **Circuit Breaker, Retry with Exponential Backoff + Jitter, Fallback, và Dead-Letter Queue (DLQ)**.
   - Phải định nghĩa rõ $RTO$ (Recovery Time Objective) và $RPO$ (Recovery Point Objective) trong tài liệu ADR của TechLead.
3. **CDR (Consumer Data Right - Open Banking Australia):**
   - Các API chia sẻ dữ liệu ngân hàng phải tuân thủ chuẩn **FAPI (Financial-grade API)**, kiểm tra chặt chẽ **Consent Lifecycle** (Trạng thái đồng thuận của khách hàng: Active, Expired, Revoked) trước mỗi lần trả dữ liệu.
4. **NPP (New Payments Platform) & ISO 20022:**
   - Hệ thống thanh toán thời gian thực (Osko / PayID) phải hỗ trợ định dạng thông điệp **ISO 20022 (`pacs.008`, `pain.001`, `camt.053`)**, đảm bảo SLA phản hồi tính bằng mili-giây và xử lý đầy đủ ký tự mở rộng (Extended Remittance Information).
5. **AUSTRAC (AML/CTF - Phòng chống rửa tiền & Tài trợ khủng bố):**
   - Mọi giao dịch chuyển tiền vượt ngưỡng quy định hoặc có dấu hiệu bất thường phải phát sinh sự kiện bất biến (Immutable Audit Event) đẩy sang hệ thống giám sát AML/Fraud theo thời gian thực.

---

### 2. Bất biến Sổ cái & Toán học Tài chính cho Dev (Java) & Tester
Khi viết code **Java** hoặc thiết kế **Test Case** cho nghiệp vụ ngân hàng:
1. **CẤM TUYỆT ĐỐI kiểu `float` và `double` cho Tiền tệ & Lãi suất:**
   - Mọi giá trị tiền tệ, tỷ giá hối đoái ($FX$), và lãi suất trong Java bắt buộc sử dụng `java.math.BigDecimal` (hoặc thư viện chuẩn `JSR 354 - JavaMoney / Moneta`).
   - Khởi tạo `BigDecimal` từ `String` hoặc `BigDecimal.valueOf(long)`, **cấm** dùng constructor `new BigDecimal(double)`.
2. **Quy tắc Làm tròn và Độ chính xác (Precision & Rounding Mode):**
   - Tính toán trung gian (Intermediate calculations) cho lãi suất/tỷ giá phải giữ tối thiểu $8$ đến $10$ chữ số thập phân (`MathContext.DECIMAL128`).
   - Làm tròn số tiền hiển thị/hạch toán cuối cùng theo quy định sản phẩm của NAB, mặc định sử dụng **Banker's Rounding (`RoundingMode.HALF_EVEN`)** đối với AUD ($2$ chữ số thập phân) và kiểm tra bảng Currency Scale động (ví dụ: JPY/VND có scale $= 0$, KWD có scale $= 3$).
3. **Nguyên tắc Hạch toán Kép & Tính Lũy đẳng (Double-Entry Bookkeeping & Idempotency):**
   - Mọi bút toán thay đổi số dư phải thỏa mãn phương trình bất biến:
     $$\sum \text{Debit} - \sum \text{Credit} = 0$$
   - Không bao giờ thực hiện lệnh `UPDATE account SET balance = ...` đơn lẻ mà không đi kèm bản ghi `ledger_entry` bất biến (Append-only) trong cùng một ACID Database Transaction.
   - Mọi API tạo giao dịch (`POST /payments`, `POST /transfers`) bắt buộc phải nhận và kiểm tra **`Idempotency-Key`** (lưu vết trên Redis + Unique Constraint trong PostgreSQL) để đảm bảo nếu mạng lỗi hoặc client gọi lại nhiều lần thì khách hàng **chỉ bị trừ tiền đúng 1 lần duy nhất**.
4. **Xử lý Thời gian & Múi giờ tại Úc (Timezone & Cut-off Times):**
   - Trong Java, luôn sử dụng `java.time.Instant`, `ZonedDateTime` hoặc `OffsetDateTime` (UTC làm chuẩn lưu trữ), và chuyển đổi sang múi giờ nghiệp vụ của trụ sở NAB (`Australia/Melbourne` - AEST/AEDT, lưu ý Daylight Saving Time) khi tính thời điểm khóa sổ cuối ngày (**EOD Cut-off**) và tính lãi qua đêm (**Accrued Interest** theo quy ước số ngày thực tế $\text{Actual}/365$ của thị trường Úc).

---

### 3. Quy chuẩn Phân tích Kinh tế Ngân hàng cho BA & Báo cáo `OfficeCLI`
Khi **BA** hoặc **TechLead** phân tích đề xuất tính năng hoặc xuất báo cáo Word/Excel/PPT bằng `OfficeCLI`:
1. **Chỉ số Kinh tế Ngân hàng Cốt lõi:**
   - **NIM (Net Interest Margin):** Biên lãi ròng $= \frac{\text{Thu nhập lãi thuần}}{\text{Tổng tài sản sinh lời bình quân}}$.
   - **CIR (Cost-to-Income Ratio):** Tỷ lệ chi phí trên thu nhập — mọi tính năng tự động hóa/AI tại NAB cần chứng minh khả năng giảm $CIR$ hoặc giảm chi phí vận hành trên mỗi giao dịch.
   - **ECL (Expected Credit Loss - IFRS 9 / AASB 9):** Tổn thất tín dụng dự kiến:
     $$ECL = PD \times LGD \times EAD$$
     *(Trong đó: $PD$ là Xác suất vỡ nợ, $LGD$ là Tỷ lệ tổn thất khi vỡ nợ, $EAD$ là Dư nợ tại thời điểm vỡ nợ).*
2. **Tiêu chuẩn Xuất Báo cáo qua `OfficeCLI`:**
   - **File Word (`.docx`):** Có trang bìa chuẩn NAB, bảng Quản lý Phiên bản (Version Control), Ma trận Truy vết Yêu cầu (**RTM - Requirements Traceability Matrix** nối từ Business Rule $\rightarrow$ User Story $\rightarrow$ API Endpoint $\rightarrow$ Test Case ID).
   - **File Excel (`.xlsx`):** Các bảng tính đối soát hoặc mô hình tài chính phải tách biệt rõ Sheet `Assumptions/Inputs` (chữ màu xanh dương), Sheet `Calculations/Model` (chữ màu đen, dùng công thức động thay vì điền số cứng) và Sheet `Executive Summary`.
   - **File PowerPoint (`.pptx`):** Áp dụng nguyên tắc **Pyramid Principle (Minto)**: Mỗi tiêu đề Slide phải là một câu kết luận mang tính hành động (Action Title), theo sau bởi số liệu định lượng và kiến nghị rõ ràng cho Ban Lãnh đạo NAB.

---

## Anti-Rationalization Table (Các lý do ngụy biện bị cấm)

| Ngụy biện của Agent / Dev | Phản biện bắt buộc tại NAB (Rebuttal) |
| :--- | :--- |
| *"Đây chỉ là hàm tính phí đơn giản, dùng `double` cho nhanh."* | Sai số dấu phẩy động IEEE 754 (`0.1 + 0.2 != 0.3`) trong hàng triệu giao dịch tại NAB sẽ gây lệch sổ cái hàng ngàn AUD và vi phạm kiểm toán. Bắt buộc dùng `BigDecimal`. |
| *"API này chỉ gọi nội bộ giữa 2 service nên không cần `Idempotency-Key`."* | Trong môi trường Cloud/Kubernetes, Kafka hoặc HTTP Retry khi mạng chập chờn luôn xảy ra. Thiếu Idempotency sẽ dẫn đến nhân đôi bút toán trừ tiền khách hàng. |
| *"Tôi sẽ viết tài liệu PRD/Test Plan dạng text trên khung chat, không cần chạy `OfficeCLI`."* | Khi người dùng yêu cầu xuất báo cáo Word/Excel/PPT, bắt buộc phải dùng `officecli` kết hợp scene layer tương ứng (`officecli-docx` · `officecli-xlsx` · `officecli-pptx`) để tạo file thực tế và kiểm tra bố cục (`validate`/`view`). |
| *"Tôi sẽ nạp hết tất cả các file `SKILL.md` vào bộ nhớ để biết hết mọi thứ."* | Nạp toàn bộ skill gây lãng phí Token nghiêm trọng và làm loãng sự tập trung của mô hình. Phải tuân thủ bảng định tuyến trong `AGENTS.md`. |

---

## Verification Gate (Cổng Kiểm Chứng Bắt Buộc)
Trước khi tuyên bố hoàn thành bất kỳ nhiệm vụ nào trong dự án NAB, AI Agent phải cung cấp bằng chứng:
- [ ] **Đối với BA:** Mọi User Story đều có Gherkin (`Given/When/Then`) bao phủ cả Happy Path, Negative Path và Edge Cases (làm tròn tiền tệ, giao dịch đồng thời, hết hạn Consent CDR).
- [ ] **Đối với Dev (Java):** Không có `float`/`double` cho tiền tệ; có xử lý `Idempotency-Key`; không lộ PII trong log; toàn bộ Unit Test JUnit 5 chạy Pass.
- [ ] **Đối với Tester / QC:** Đã chạy kiểm chứng Spec-to-Code (`spec-to-code-compliance`) và Property-based test cho bảo toàn số dư.
- [ ] **Đối với Office:** File `.docx`, `.xlsx`, `.pptx` đã được tạo/cập nhật qua `officecli` và vượt qua bước kiểm tra cấu trúc/hiển thị mà không có lỗi định dạng hay lỗi công thức.