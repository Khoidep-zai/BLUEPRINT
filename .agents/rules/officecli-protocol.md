---
trigger: model_decision
description: "Bắt buộc khi tạo, đọc, sửa hoặc kiểm tra tài liệu Office (.docx, .xlsx, .pptx) trong dự án NAB. Quy trình 3 bước OfficeCLI, tra cứu schema, atomic batch và tiêu chuẩn trình bày ngân hàng."
---

# OfficeCLI Protocol (`.docx` · `.xlsx` · `.pptx`)

`officecli.exe` (tại `%LOCALAPPDATA%\OfficeCLI\officecli.exe`) là công cụ **duy nhất được phép** tạo, đọc, sửa và kiểm tra tài liệu Office. Không viết script Python rời rạc.

## 1. Ba bước vàng

| Bước | Việc làm | Lệnh |
| :---: | :--- | :--- |
| 1 | Tra schema + mở resident session | `officecli help <docx\|xlsx\|pptx> <element>` · `officecli open <file>` |
| 2 | Atomic batch edits | `officecli batch <file> --commands '[...]'` |
| 3 | Kiểm chứng thị giác & schema | `officecli validate <file>` · `officecli view <file> text\|html\|image` · `officecli close <file>` |

**Cấm đoán mò tên thuộc tính** — luôn `officecli help` trước.
**Cấm bàn giao** khi chưa chạy `validate` + `view`: phải không có `#REF!`, `#DIV/0!`, tràn chữ, lệch slide.

## 2. Tiêu chuẩn trình bày NAB

**Word (`.docx`)**
- Trang bìa chuẩn NAB + bảng quản lý phiên bản.
- Ma trận truy vết yêu cầu **RTM**: `Business Rule → User Story → API Endpoint → Test Case ID`.

**Excel (`.xlsx`)**
- 3 sheet ngân hàng: `Assumptions` (input — chữ xanh) → `Calculations` (công thức động — chữ đen) → `Summary` (KPI).
- Làm tròn **Banker's Rounding `HALF_EVEN`**; không hard-code số trong sheet Calculations.

**PowerPoint (`.pptx`)**
- Khung 16:9, Minto Pyramid Principle: **Action Title** của mỗi slide là một kết luận nêu rõ số liệu định lượng.
- Zero text overflow.

## 3. Skill chuyên sâu cần nạp kèm

- Base: `officecli` rồi tới `officecli-docx` / `officecli-xlsx` / `officecli-pptx`.
- Scene layer: `officecli-docx` (báo cáo, RTM) · `officecli-xlsx` (tracker) · `officecli-data-dashboard` · `officecli-financial-model` (3-statement, DCF, LBO) · `officecli-pitch-deck` · `officecli-academic-paper` · `officecli-word-form` (form điền được) · `morph-ppt`, `morph-ppt-3d` (chuyển động xuyên slide).
- Tài liệu chỉ-đọc khác: `pdf`, `doc-coauthoring`, `internal-comms`.