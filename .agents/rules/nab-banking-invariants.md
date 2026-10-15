---
trigger: glob
description: "Bất biến nghiệp vụ ngân hàng NAB áp dụng khi viết hoặc sửa Java, SQL, DDL, YAML: tiền tệ BigDecimal, sổ cái append-only, idempotency, khóa cạnh tranh, masking PII, tuân thủ APRA/CDR."
globs: "**/*.java, **/*.sql, **/*.ddl, **/*.yaml"
---

# NAB Banking Invariants

Áp dụng cho **mọi** dòng code chạm vào tiền, số dư, hoặc dữ liệu khách hàng. Vi phạm = lỗi nghiêm trọng, không phải cảnh báo style.

## 1. Tiền tệ

- **Chỉ `BigDecimal`** cho số tiền, lãi suất, tỷ giá. Cấm `double`/`float`.
- Làm tròn **`RoundingMode.HALF_EVEN`** (Banker's Rounding); khai báo `scale` tường minh, không dựa vào mặc định.
- Tiền tệ luôn kèm **ISO 4217 currency code**; không cộng trừ hai currency khác nhau.
- So sánh tiền bằng `compareTo`, không dùng `equals`.

## 2. Sổ cái (Ledger)

- **Append-only**: không `UPDATE`/`DELETE` bút toán đã ghi; điều chỉnh bằng bút toán đối ứng.
- Bút toán kép: mọi giao dịch phải cân bằng (`Σ debit = Σ credit`).
- **Bất biến số dư**: `balance = Σ entries` — dùng property-based test để kiểm chứng.

## 3. Giao dịch & cạnh tranh

- Ranh giới transaction bao đúng phạm vi nghiệp vụ; không giữ transaction qua I/O mạng dài.
- Mọi lệnh chi/ghi tiền phải **idempotent**: có `idempotency key` + unique constraint, replay không sinh bút toán thứ hai.
- Cập nhật số dư đồng thời: optimistic lock (`@Version`) hoặc **Redis distributed lock**; không để lost update.
- NPP/ISO 20022: map đúng `pain.001`/`pacs.008`, quản lý state payment rõ ràng, xử lý timeout bằng truy vấn trạng thái chứ không retry mù.

## 4. Dữ liệu & bảo mật

- **Masking PII** trong log, exception message, thông báo lỗi trả về client (số tài khoản, BSB, email, điện thoại, số thẻ).
- Không hard-code secret/token/credential; đọc từ secret manager hoặc biến môi trường.
- SQL tham số hóa; cấm nối chuỗi truy vấn.
- **Audit trail bất biến**: ai làm gì, lúc nào, trên đối tượng nào, giá trị trước/sau — không cho sửa.
- CDR Open Banking: kiểm tra đúng consent scope trước khi trả dữ liệu; thu hồi consent có hiệu lực ngay.

## 5. Hiệu năng

- Tránh N+1 query; kiểm tra index cho mọi truy vấn theo số tài khoản/ngày/tham chiếu.
- Redis chỉ dùng cho cache/lock — mọi thay đổi số dư vẫn phải ghi bền vững xuống Postgres trước khi báo thành công.

## 6. Tuân thủ

- **APRA CPS 234** (an ninh thông tin) và **CPS 230** (khả năng chịu đựng vận hành): thay đổi ảnh hưởng dịch vụ trọng yếu phải có kế hoạch rollback, monitoring và đường báo cáo sự cố.
- Chi tiết nghiệp vụ: nạp skill `.agents\skills\nab-senior-banking-domain\SKILL.md`.