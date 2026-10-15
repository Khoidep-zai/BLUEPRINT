---
trigger: model_decision
description: "Chạy một tính năng hoặc Change Request xuyên suốt vòng đời SDLC của dự án NAB: BA, TechLead, Dev_Java, Tester, QC, QA. Mô tả chuỗi skill, ràng buộc và artifact bàn giao của từng giai đoạn."
---

# Luồng SDLC 6 giai đoạn (NAB End-to-End)

Mọi tính năng hoặc Change Request đi theo chuỗi khép kín dưới đây. Mỗi giai đoạn **chỉ nạp skill của chính nó**, đầu ra là artifact bàn giao cho giai đoạn sau.

```text
BA  →  TechLead  →  Dev_Java  →  Tester  →  QC  →  QA
PRD    ADR+Tasks    Code+UT      TestSuite  QC Report  Go-Live
```

| # | Giai đoạn | Tra cứu CodeGraph | Skill nạp | Ràng buộc chính | Artifact bàn giao |
| :---: | :--- | :--- | :--- | :--- | :--- |
| 1 | **BA & kinh tế ngân hàng** | — | `interview-me` → `spec-driven-development` → `user-story` | APRA CPS 234/230 · CDR Open Banking · NPP/ISO 20022 | PRD/BRD + Gherkin Acceptance Criteria (`.docx`) |
| 2 | **TechLead & kiến trúc** | `codegraph explore "<kiến trúc hiện tại>"` | `planning-and-task-breakdown` + `documentation-and-adrs` | BIAN Service Domain · Idempotency · Audit trail · Observability | ADR + danh sách atomic tasks (`.pptx`/`.xlsx`) |
| 3 | **Dev (Java) & TDD** | `codegraph context "<task>"` + `codegraph impact "<symbol>"` | `api-and-interface-design` → `incremental-implementation` | Java 17/21 · BigDecimal HALF_EVEN · Postgres ACID · Redis lock · masking PII | Source code + unit test xanh + commit nguyên tử + `codegraph sync` |
| 4 | **Tester (automation & BDD)** | `codegraph affected <files>` | `junit-5-skill` + `cucumber-skill` + `property-based-testing` | Test Pyramid 80/15/5 · bất biến số dư sổ cái · API security CDR | Test suite pass 100% + Test Execution Matrix (`.xlsx`) |
| 5 | **QC (chất lượng & bảo mật)** | — | `spec-to-code-compliance` + `code-review-and-quality` + `security-and-hardening` | Đối chiếu từng dòng code với spec BA · Insecure defaults · OWASP Top 10 · CVE | Biên bản QC & Security Audit (`.docx`/`.xlsx`) |
| 6 | **QA (cổng chất lượng & Go-Live)** | — | `constraint-driven-development` + `doubt-driven-development` + `shipping-and-launch` | Đối chiếu `references\definition-of-done.md` · kế hoạch rollback & monitoring | Chứng nhận Go-Live Readiness + slide SteerCo (`.pptx`) |

## Quy tắc vận hành chuỗi

1. **Không nhảy cóc** — Dev không bắt đầu khi chưa có ADR; QC không ký khi chưa có test suite xanh.
2. **Bàn giao = artifact**, không bàn giao ngữ cảnh: chặng sau chỉ đọc file đầu ra, không đọc lại skill của chặng trước.
3. **Rẽ nhánh:** nếu đầu ra cuối là tài liệu → chặng cuối đổi thành `Office` (nạp `officecli` + skill scene layer tương ứng).
4. **Vòng lặp lỗi:** QC phát hiện lệch spec → trả về chặng 3 kèm mã lỗi cụ thể, không làm lại từ chặng 1.
5. **Truy vết:** mỗi artifact phải giữ được chuỗi `Business Rule → User Story → API Endpoint → Test Case ID`.
