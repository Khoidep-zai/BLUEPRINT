---
trigger: model_decision
description: "Bắt buộc khi đọc hiểu, khám phá, phân tích kiến trúc, sửa đổi mã nguồn hoặc chọn test cần chạy trong dự án NAB. Quy trình CodeGraph-First thay thế grep/find/đọc file lớn, giảm ~90% token tiêu hao."
---

# CodeGraph Protocol — Bộ nhớ kiến trúc dài hạn

`.codegraph/` (12.000+ nodes · 36.000+ edges) là **công cụ bắt buộc hàng đầu** cho mọi hoạt động đọc, khám phá và phân tích mã nguồn. Nó **thay thế hoàn toàn** `grep`, `find`, `view_file` cỡ lớn.

## 1. Pre-flight (một lần mỗi phiên)

| Bước | Lệnh | Xử lý kết quả |
| :--- | :--- | :--- |
| 1. Phát hiện CLI | Windows: `Get-Command codegraph -ErrorAction SilentlyContinue` · Linux/macOS: `which codegraph` | Không có → **DỪNG**, xin phép người dùng trước khi cài |
| 2. Kiểm tra chỉ mục | `codegraph status` | `Not initialized` → hỏi người dùng `codegraph init` tại đây hay `cd` sang thư mục khác |
| 3. Sẵn sàng | `.codegraph/` tồn tại | Bật chế độ CodeGraph-First cho toàn phiên |

**Nếu máy chưa có CodeGraph**, đề xuất cài (nguồn: https://github.com/colbymchenry/codegraph):

1. **Cài CLI** — không bắt buộc Node.js:
   - Windows: `irm https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.ps1 | iex`
   - macOS/Linux: `curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh`
   - Có Node.js: `npm install -g @colbymchenry/codegraph`
2. **Kết nối Agent** — mở terminal mới: `codegraph install` (tự cấu hình MCP cho Antigravity, Claude Code, Cursor, Codex CLI, opencode, Gemini CLI, Kiro, Copilot).
3. **Khởi tạo dự án** — `cd <thư_mục_dự_án>` → `codegraph init`.

## 2. Năm nguyên tắc vàng

| # | Khi nào | Lệnh | Lợi ích |
| :---: | :--- | :--- | :--- |
| 1 | Nhận task mới | `codegraph context "<mô tả task>"` | Trích đúng symbols, relationships, code blocks liên quan nhất |
| 2 | Cần biết về 1 symbol/kiến trúc | `codegraph explore "<symbol \| class \| method \| câu hỏi kiến trúc>"` | Trả mã nguồn gốc + call path 2 chiều (caller/callee) trong **1 lượt gọi** |
| 3 | **Trước khi sửa** bất kỳ method/interface/model | `codegraph impact "<Class.Method>"` | Liệt kê mọi service/controller/repository bị ảnh hưởng → loại bỏ lỗi hồi quy |
| 4 | Sau khi sửa source | `codegraph affected <danh_sách_file_đã_sửa>` | Khoanh vùng test phải chạy lại, không chạy mù toàn bộ suite |
| 5 | Kết thúc thay đổi | `codegraph sync` | Cập nhật đồ thị tri thức cho các phiên sau |

Tương đương qua MCP: `codegraph_explore`, `codegraph_context`, `codegraph_impact`.

## 3. Ranh giới

**Cấm:** `grep -r`, `findstr /s`, đọc trọn file source lớn chỉ để tìm 1 symbol, đọc nhiều file "để chắc chắn".
**Cho phép:** đọc file cấu hình nhỏ, `SKILL.md` đang dùng, artifact đầu ra của chặng trước.
**Bắt buộc:** sau khi tạo/sửa code xong → `codegraph sync` trước khi bàn giao.